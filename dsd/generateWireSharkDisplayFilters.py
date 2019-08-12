#!/usr/bin/env python3

from __future__ import print_function

import argparse
import dsd.loaddata as ld
from svgobjs import *

def generateDisplayFilter(hosts, line_breaks=True):
    is_first = True
    outp = '(\n'
    outp = outp + '   (\n'
    for s1 in hosts:
        for s2 in hosts:
            if s1 == s2:
                continue

            outp = outp + '      '
            if is_first:
                outp = outp + '   '
                is_first = False
            else:
                outp = outp + 'or '
            outp = outp + '(ip.src=={s1} and ip.dst=={s2})\n'.format(s1=s1.ip, s2=s2.ip)

    outp = outp + '   )\n'
    outp = outp + '    and (http contains "StartCall" or http ~ "<eventType>.*endMedia.*</eventType>" or http ~ "<eventType>.*CDRType1.*</eventType>" or http ~ "<eventType>.*EndCall.*</eventType>")\n'
    outp = outp + ')'

    if not line_breaks:
        outp_nw = re.sub('\n', '', outp)
        outp_nw = re.sub('\s+', ' ', outp)

    return outp

def main():
    """ Provided with host names, produce wireshark display filters """

    # Load CLI arguments
    parser = ld.GetArgParse(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('hosts', metavar='HOSTS', nargs='+', help='List of hosts to include')
    parser.add_argument('--nice', action='store_true', dest='nice', help='Format nicely')

    args = parser.parse_args()

    # /Load CLI arguments

    all_hosts, *ed = ld.read_config(args.config)

    hosts=[]
    for hname in args.hosts:
        h = Host.match(hosts=all_hosts, name_or_ip=hname)
        if h is not None:
            hosts.append(h)

    outp = ld.generateDisplayFilter(hosts, args.nice)
    print(outp)

if __name__ == "__main__":
    main()
