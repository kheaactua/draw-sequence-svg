#!/usr/bin/env python3

from __future__ import print_function

import pyshark
from enum import Enum

from svgobjs import *

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

<<<<<<< HEAD
    if args.verbose:
        print('Examining events %s between %s'%(', '.join(args.events), ', '.join([str(x) for x in hosts])))
    queryLogs(hosts=hosts, events=args.events, verbose=args.verbose)
=======
    queryLogs(hosts=hosts, events=args.events)
>>>>>>> 7db1cdb... Provided the display query to queryLogs


if __name__ == "__main__":
    main()

# vim: sw=4 ts=4 sts=4 expandtab ft=python ffs=unix :
