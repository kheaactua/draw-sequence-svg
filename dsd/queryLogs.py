#!/usr/bin/env python3

from __future__ import print_function

import pyshark
from enum import Enum

from svgobjs import *
from generateWireSharkDisplayFilters import generateDisplayFilter


def queryLogs(hosts, events, verbose=False):
    # print(hosts)
    # print(events)

    msgs_df = generateDisplayFilter(hosts=hosts, events=events, line_breaks=verbose)
    # Gotta add ACKs to this filter, I think the sequence number or something has the time
    if verbose:
        print('Display Filter:\n%s'%msgs_df)

    # log_filename = 'data/Test1-No_visible_delays.pcap'
    log_filename = 'data/LoggingService_processing.pcapng'

    if verbose:
        print('Reading', log_filename)
    cap = pyshark.FileCapture(
        log_filename,
        display_filter=msgs_df,
    )

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


        if 'xml' in p:
            # Look for event type

            # Default time label is dt
            dt = (p.sniff_time - sniff_start_time)
            events.append(Event(
                time=p.sniff_time,
                time_label='%3.2f'%(dt.microseconds/1000),
                src=p['ip'].src,
                dst=p['ip'].dst,
                event_type=find_event_type(p['xml']),
                packet_id=int(p.number),
            ))

        elif p['tcp'].ack and 'http' in p and p['http'].response_code:
            # Looking for an ACK
            request_frame = p['http'].request_in
            e = next((e for e in events if e.packet_id == int(request_frame)), None)
            if e:
                e.ack_time = p['tcp'].time_relative
            else:
                print("Could not find event for %s"%str(request_frame), file=sys.stderr)

    return events

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = GetArgParse()
    parser.add_argument(
        '--hosts',
        action='store',
        metavar='HOSTS',
        nargs='+',
        help='List of hosts to include'
    )
    parser.add_argument(
        '-e', '--events',
        metavar='EVENTS',
        dest='events',
        nargs='+',
        default=['StartCall', 'EndCall', 'endMedia', 'CDRType1'],
        help='List of events to query'
    )

    args = parser.parse_args()

    all_hosts, *ed = read_config(args.config)

    hosts=[]
    for hname in args.hosts:
        h = Host.match(hosts=all_hosts, name_or_ip=hname)
        if h is not None:
            hosts.append(h)

    if args.verbose:
        print('Examining events %s between %s'%(', '.join(args.events), ', '.join([str(x) for x in hosts])))
    queryLogs(hosts=hosts, events=args.events, verbose=args.verbose)


if __name__ == "__main__":
    main()

# vim: sw=4 ts=4 sts=4 expandtab ft=python ffs=unix :
