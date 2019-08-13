#!/usr/bin/env python3

from __future__ import print_function

import argparse
import dsd.loaddata as ld


def main():
    """ Provided with host names, produce wireshark display filters """

    # Load CLI arguments
    parser = ld.get_arg_parse(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('--hosts', metavar='HOSTS', dest='hosts', nargs='+', help='List of hosts to include', default=[])
    parser.add_argument('--nice', action='store_true', dest='nice', help='Format nicely')
    parser.add_argument('-e', '--events', metavar='EVENTS', dest='events', help='List of events to query', default=['StartCall', 'EndCall', 'endMedia', 'CDRType1'])

    args = parser.parse_args()

    # /Load CLI arguments

    all_hosts, *ed = ld.read_config(args.config)

    hosts=[]
    for hname in args.hosts:
        h = Host.match(hosts=all_hosts, name_or_ip=hname)
        if h is not None:
            hosts.append(h)

    outp = ld.generate_display_filter(hosts=hosts, events=args.events, line_breaks=args.nice)
    print(outp)

if __name__ == "__main__":
    main()
