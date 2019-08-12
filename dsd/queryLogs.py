#!/usr/bin/env python3

from __future__ import print_function

import pyshark
from enum import Enum

from svgobjs import *


def queryLogs():
    pass

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = GetArgParse()
    parser.add_argument('hosts', action='store', metavar='HOSTS', nargs='+', help='List of hosts to include')
    parser.add_argument('-e', '--events', metavar='EVENTS', dest='events', required=True, help='List of events to query')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print('Cannot find config file %s'%args.config, file=sys.stderr)

    all_hosts, *ed = read_config(args.config)

    hosts=[]
    for hname in args.hosts:
        h = Host.match(hosts=all_hosts, name_or_ip=hname)
        if h is not None:
            hosts.append(h)


if __name__ == "__main__":
    main()
