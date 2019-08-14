#!/usr/bin/env python3

from __future__ import print_function

import os
import re
import csv
import json
import argparse
import datetime
import pyshark

from svgobjs import *

def read_config(filename):
    with open(filename) as json_file:
        data = json.load(json_file)

    # Maybe write something later dst automatically load host objects.  See https://github.com/kheaactua/vim-managecolor/blob/master/lib/cmds.py the CSData.dict_to_obj and stuff
    hosts = []
    for s in data['hosts']:
        hosts.append(Host(
            id=s['id'],
            name=s['name'],
            ip=s['ip'],
            host_type=s['host_type'],
            sort_nudge=s['sort_nudge']
        ))

    # Sort the list
    hosts.sort(key=lambda x: x.sort_nudge)

    event_style = {}
    for e in data['eventTypes']:
        event_style[e['eventType']] = EventStyle(event_type=e['eventType'], color=e['color'])

    return hosts, event_style, data["settings"]

def read_events(filename, hosts, event_styles, settings, verbose=False):
    csv.register_dialect('eventStyle', delimiter = ',', skipinitialspace=True)

    if verbose:
        print('Reading event data from %s'%filename)

    data = []
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, dialect='eventStyle')
        for i, row in enumerate(reader):
            if i<1:
                continue
            if len(row) < 4:
                continue
            if re.match('^\s*#', row[0]):
                continue

            src = next(s for s in hosts if s.id == row[1])
            dst = next(s for s in hosts if s.id == row[2])

            sty = event_styles[row[3]] if row[3] in event_styles else None

            ack_time = None
            if len(row) > 3:
                ack_time = row[4]

            packet_id = None
            if len(row) > 4:
                packet_id = row[5]

            data.append(Event(
                time=datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f'),
                src=src,
                dst=dst,
                event_type=row[3],
                ack_time=ack_time,
                packet_id=packet_id,
                event_style=sty
            ))

    Event.sort_and_process(events=data, settings=settings)

    return data

def write_events(filename, events):
    """ Write the events to a CSV file """
    # print("writing events: ", events)
    with open(filename, 'w') as f:
        colHeadings = ['time', 'src', 'dst', 'eventType', 'ackTime', 'packetId']
        writer = csv.DictWriter(f, delimiter=',', fieldnames=colHeadings)

        writer.writeheader()
        for e in events:
            writer.writerow({
                'time':       e.time,
                'src':        e.src.id,
                'dst':        e.dst.id,
                'eventType':  e.event_type,
                'ackTime':    e.ack_time,
                'packetId':   e.packet_id,
            })

def read_template(filename):
    """ Import our template, and read some properties from it """
    with open(filename, 'r') as f: contents=f.read()

    # Determine some properties, get the svg tag
    tag = re.search('<svg.*?>', contents, re.MULTILINE|re.S);
    props = re.findall(r'\b(?P<attr>\w+)=\"(?P<val>.*?)\"', tag.group(0), re.MULTILINE)
    info = {}
    for m in props:
        if 'width' == m[0]:
            units=re.match(r'(?P<val>\d+.?\d+)(?P<unit>\w+)', m[1])
            info['width'] = float(units.group('val'))
            info['unit']  = units.group('unit')
        elif 'height' == m[0]:
            units=re.match(r'(?P<val>\d+.?\d+)(?P<unit>\w+)', m[1])
            info['height'] = float(units.group('val'))

    return contents, info

def filter_hosts(hosts, event_data):
    """ Remove hosts that aren't involved in any events """
    host_copy = hosts.copy()
    for s in host_copy:
        found = False
        for e in event_data:
            if s == e.src or s == e.dst:
                found = True
                break
        if not found:
            hosts.remove(s)

def match_hosts(all_hosts, user_hosts):
    """ Given a list of hosts from a command line, match to Host objects in user_hosts """
    hosts=[]
    for hname in user_hosts:
        h = Host.match(hosts=all_hosts, name_or_ip=hname)
        if h is not None:
            hosts.append(h)
    return hosts

def argparse_file_exists(f):
    """ Used by argparse to see whether the filename exists, if so return the filename, otherwise raise an exception """
    if not os.path.exists(f):
        raise argparse.ArgumentTypeError('Cannot read %s'%f)
    else:
        return f

def get_arg_parse(*args, **kwargs):
    """ Factory for argparse library with some of the common elements used by every script already loaded """

    parser = argparse.ArgumentParser(*args, *kwargs)
    parser.add_argument(
        '-c', '--config',
        dest='config',
        metavar='FILE',
        action='store',
        help='JSON Config file',
        type=argparse_file_exists,
        default='/tmp/config.json'
    )


    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        help='Increase verbosity',
    )

    return parser

def generate_display_filter(hosts, events, line_breaks=True):
    """ Generate a display filter intended to search for Solacom events in a
    capture file between specified hosts """

    is_first = True

    outp = ''
    if len(hosts):
        outp += '(\n'

        if len(hosts) > 1:
            outp += '   (\n'
            for s1 in hosts:
                for s2 in hosts:
                    if s1 == s2:
                        continue

                    outp += '      '
                    if is_first:
                        outp += '   '
                        is_first = False
                    else:
                        outp += 'or '
                    outp += '(ip.src=={s1} and ip.dst=={s2})\n'.format(s1=s1.ip, s2=s2.ip)
            outp += '   )\n'
        else:
            outp += '    ip.src={s}\n'.format(s=hosts[0].ip)

        outp += '   and '

    ack_filter = '(http.response.code==200 and tcp.ack)'
    et_filter = 'http ~ "<eventType>{event}</eventType>'
    if type(events) == list:
        if  len(events) > 1:
            outp += '(\n'
            for i,e in enumerate(events):
                outp += '      '
                if i>0:
                    outp += 'or '
                else:
                    outp += '   '
                outp += ('%s"\n'%et_filter).format(event=e)
            outp += '      or %s\n'%ack_filter
            outp += '   )\n'

        elif len(events) == 1:
            outp += ('   %s"\n'%et_filter).format(event=e)
            outp += 'or %s\n'%ack_filter

    outp += ')'

    if not line_breaks:
        outp = re.sub('\n', '', outp)
        outp = re.sub('\s+', ' ', outp)

    return outp


def query_logs(capture_filename, hosts, events, verbose=False):
    """ Query a capture file for events """

    msgs_df = generate_display_filter(hosts=hosts, events=events, line_breaks=verbose)
    if verbose:
        print('Display Filter:\n%s'%msgs_df)

    if verbose:
        print('Reading', capture_filename)
    cap = pyshark.FileCapture(
        capture_filename,
        display_filter=msgs_df,
    )
    if verbose:
        cap.set_debug()

    def find_event_type(layer_xml):
        tag = layer_xml.get_field('tag')

        t_idx = None
        for i,t in enumerate(tag.fields):
            if t.showname == '<eventType>':
                t_idx = i
                break

        # The -1 is because of the nest level I think?
        return layer_xml.get_field('cdata').fields[t_idx-1].binary_value.decode('ascii')


    events = []
    is_first=True
    sniff_start_time = 0
    for p in cap:
        if is_first:
            sniff_start_time = p.sniff_time
            is_first=False

        if 'xml' in p and p['http'].request_method=='POST':
            # Look for event type

            # Default time label is dt
            dt = (p.sniff_time - sniff_start_time)

            src = next(s for s in hosts if s.ip == str(p['ip'].src))
            dst = next(s for s in hosts if s.ip == str(p['ip'].dst))

            events.append(Event(
                time=p.sniff_time,
                time_label='%3.2f'%(dt.microseconds/1000),
                src=src,
                dst=dst,
                event_type=find_event_type(p['xml']),
                packet_id=int(p.number),
            ))
            if verbose:
                print('pid=%d event=%s\n'%(int(p.number), events[len(events)-1]))

        elif p['tcp'].ack and 'http' in p and int(p['http'].response_code)==200:
            request_frame = p['http'].request_in
            e = next((e for e in events if e.packet_id == int(request_frame)), None)
            if e:
                e.ack_time = p['tcp'].time_relative
            else:
                print("Could not find event for request_frame=%d"%int(request_frame), file=sys.stderr)
        else:
            pass
            # print('Skipping %d'%int(p.number), p['tcp'].ack, p['http'].responce_code)

    Event.sort_and_process(events=data, settings=settings)

    return events

# vim: sw=4 ts=4 sts=0 expandtab ft=python ffs=unix :
