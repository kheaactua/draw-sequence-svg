#!/usr/bin/env python3

from __future__ import print_function

import sys
import os
import re
import csv
import json
import argparse
import datetime
import pyshark

import dsd.solaobjs as so
import dsd.svgobjs as svg

class Settings(object):
    """ Config object to hold various settings """

    def __init__(self, data):
        for k,v in data.items():
            setattr(self, so.JsonSerializatble.json2py_name(k), v)

    @classmethod
    def from_json(cls, data):
        # Defaults on Settings (until it's its own object)
        defaults = {
            'hostSpacing':      60,   # mm
            'timeMarginLeft':   20,   # mm
            'timeSpacing':      25,   # s
            'minLabelTimeGap':  0.01, # s
            'maxTimeGap':       2,    # s
            'timeUnit':         'secondsSinceStart',

            # Ack time thresholds
            'ackThresholdFast':     0.001, # s
            'ackThresholdSlow':     0.001, # s
            'ackThresholdVerySlow': 0.010, # s

            # SVG output type
            'svg_type':         svg.SvgType.PLAIN
        }

        for k,v in defaults.items():
            if k not in data:
                data[k] = v

        return cls(data=data)

class ConfigFile(object):
    """ Object representing the config file """

    @classmethod
    def from_json(cls, data):
        settings    = Settings.from_json(data['settings'])
        hosts       = list(map(so.Host.from_json,       data['hosts']))
        event_types = list(map(so.EventType.from_json,  data['eventTypes']))

        return hosts, event_types, settings

def read_config(filename):
    with open(filename) as json_file:
        hosts, event_types, settings = ConfigFile.from_json(json.load(json_file))

    # Sort the list
    hosts.sort(key=lambda x: x.sort_nudge)

    return hosts, event_types, settings

def read_events(filename, hosts, event_types, settings, from_frame=None, to_frame=None, verbose=False):
    csv.register_dialect('EventType', delimiter = ',', skipinitialspace=True)

    if verbose:
        print('Reading event data from %s'%filename)

    data = []
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, dialect='EventType')
        for i, row in enumerate(reader):
            if i<1:
                continue
            if len(row) < 4:
                continue
            if re.match('^\s*#', row[0]):
                continue

            src = next(s for s in hosts if s.id == row[1])
            dst = next(s for s in hosts if s.id == row[2])

            try:
                et = next(e for e in event_types if e.name == row[3])
            except (StopIteration):
                print('Cannot match event "%s", skipping event'%row[3], file=sys.stderr)
                continue

            ack_time = None
            if len(row) > 3:
                ack_time = row[4]
                if not len(ack_time):
                    ack_time = None

            frame_id = None
            if len(row) > 4:
                frame_id = int(row[5])

            ack_frame_id = None
            if len(row) > 5:
                ack_frame_id = row[6]
                if len(ack_frame_id):
                    ack_frame_id = int(ack_frame_id)
                else:
                    ack_frame_id = None

            if from_frame and frame_id < from_frame:
                continue

            if to_frame and ack_frame_id > to_frame:
                break

            e = so.Event(
                settings     = settings,
                time         = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f'),
                src          = src,
                dst          = dst,
                event_type   = et,
                ack_time     = ack_time,
                frame_id     = frame_id,
                ack_frame_id = ack_frame_id,
            )
            data.append(e)

    so.Event.sort_and_process(events=data, settings=settings)

    return data

def write_events(filename, events):
    """ Write the events to a CSV file """
    with open(filename, 'w') as f:
        colHeadings = ['time', 'src', 'dst', 'eventType', 'ackTime', 'frameId', 'ackFrameId']
        writer = csv.DictWriter(f, delimiter=',', fieldnames=colHeadings)

        writer.writeheader()
        for e in events:
            writer.writerow({
                'time':       e.time,
                'src':        e.src.id,
                'dst':        e.dst.id,
                'eventType':  e.event_type.name,
                'ackTime':    e.ack_time,
                'frameId':    e.frame_id,
                'ackFrameId': e.ack_frame_id,
            })

def filter_hosts(hosts, events):
    """ Remove hosts that aren't involved in any events """
    host_copy = hosts.copy()
    for s in host_copy:
        found = False
        for e in events:
            if s == e.src or s == e.dst:
                found = True
                break
        if not found:
            hosts.remove(s)

def match_hosts(all_hosts, user_hosts):
    """ Given a list of hosts from a command line, match to Host objects in user_hosts """
    hosts=[]
    for hname in user_hosts:
        h = so.Host.match(hosts=all_hosts, name_or_ip=hname)
        if h is not None:
            hosts.append(h)

    # Ensure the list is still sorted
    hosts.sort(key=lambda x: x.sort_nudge)

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

    parser.add_argument(
        '--inkscape',
        dest='inkscape',
        action='store_true',
        help='Do not filter out inkscape tags/attributes (helpful for debugging in Inkscape, but renders the SVG non-standard)',
    )

    return parser

def generate_display_filter(hosts, event_type_names, line_breaks=True):
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
    if type(event_type_names) == list:
        if  len(event_type_names) > 1:
            outp += '(\n'
            for i,e in enumerate(event_type_names):
                outp += '      '
                if i>0:
                    outp += 'or '
                else:
                    outp += '   '
                outp += ('%s"\n'%et_filter).format(event=e)
            outp += '      or %s\n'%ack_filter
            outp += '   )\n'

        elif len(event_type_names) == 1:
            outp += ('   %s"\n'%et_filter).format(event=e)
            outp += 'or %s\n'%ack_filter

    outp += ')'

    if not line_breaks:
        outp = re.sub('\n', '', outp)
        outp = re.sub('\s+', ' ', outp)

    return outp

def query_logs(capture_filename, hosts, event_type_names, event_types, from_frame: int=None, to_frame: int=None, settings: Settings=None, verbose=False):
    """ Query a capture file for events """

    msgs_df = generate_display_filter(
        hosts=hosts,
        event_type_names=event_type_names,
        line_breaks=False
    )

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

        if from_frame and int(p.number) < from_frame:
            continue

        if to_frame and int(p.number) > to_frame + 20:
            # 20 is an arbitrary number provided to allow time to find the ACK message
            break

        if 'xml' in p and p['http'].request_method=='POST':
            # Look for event type

            # Default time label is dt
            dt = (p.sniff_time - sniff_start_time)

            src = next(s for s in hosts if s.ip == str(p['ip'].src))
            dst = next(s for s in hosts if s.ip == str(p['ip'].dst))

            et = next(e for e in event_types if e.name == find_event_type(p['xml']))

            events.append(so.Event(
                time=p.sniff_time,
                time_label='%3.2f'%(dt.microseconds/1000),
                settings=settings,
                src=src,
                dst=dst,
                event_type=et,
                frame_id=int(p.number),
            ))
            if verbose:
                print('pid=%d event=%s\n'%(int(p.number), events[len(events)-1]))

        elif p['tcp'].ack and 'http' in p and hasattr(p['http'], 'response_code') and int(p['http'].response_code)==200 and hasattr(p['http'], 'request_in'):
            request_frame = int(p['http'].request_in)
            e = next((e for e in events if e.frame_id == request_frame), None)
            if e:
                e.ack_time = float(p['http'].time)
                e.ack_frame_id = int(p.number)

                if to_frame and e.ack_frame_id > to_frame:
                    break

            else:
                if verbose:
                    print("Could not find event for request_frame=%d"%request_frame, file=sys.stderr)
        else:
            pass
            # print('Skipping %d'%int(p.number), p['tcp'].ack, p['http'].responce_code)


    so.Event.sort_and_process(events=events, settings=settings)

    return events

# vim: sw=4 ts=4 sts=0 expandtab ft=python ffs=unix :
