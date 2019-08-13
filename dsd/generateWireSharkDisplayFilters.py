#!/usr/bin/env python3

from __future__ import print_function

import argparse
import dsd.loaddata as ld
from svgobjs import *

def generateDisplayFilter(hosts, events, line_breaks=True):
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

    if type(events) == list:
        if  len(events) > 1:
            outp += '(\n'
            for i,e in enumerate(events):
                outp += '      '
                if i>0:
                    outp += 'or '
                else:
                    outp += '   '
                outp += 'http.response.code ~ "<eventType>.*{event}.*</eventType>"\n'.format(event=e)
            outp += '      or (http and tcp.ack)\n'
            outp += '   )\n'

        elif len(events) == 1:
            outp += '   http.response.code ~ "<eventType>.*{event}.*</eventType>\n'.format(event=e)
            outp += 'or (http and tcp.ack)\n'

    outp += ')'

    if not line_breaks:
        outp = re.sub('\n', '', outp)
        outp = re.sub('\s+', ' ', outp)

    return outp

def main():
    """ Provided with host names, produce wireshark display filters """

    # Load CLI arguments
    parser = ld.GetArgParse(description='Generate an SVG of a sequence diagram based on input data')
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

    outp = ld.generateDisplayFilter(hosts=hosts, events=args.events, line_breaks=args.nice)
    print(outp)

if __name__ == "__main__":
    main()
