#!/usr/bin/env python3

from __future__ import print_function

import argparse
from svgobjs import *

def main():
    """ Provided with system names, produce wireshark display filters """

    # Load CLI arguments
    parser = argparse.ArgumentParser(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('-c', '--config', dest='config', metavar='FILE', required=True, action='store', type=str, help='JSON Config file')
    parser.add_argument('systems', metavar='SYSTEM', nargs='+', help='List of systems to include')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print('Cannot find config file %s'%args.config, file=sys.stderr)

    # /Load CLI arguments

    all_systems, ed = read_config(args.config)

    systems=[]
    for s in all_systems:
        if s.name in args.systems:
            systems.append(s)

    is_first = True
    outp = '(\n'
    outp = outp + '   (\n'
    for s1 in systems:
        for s2 in systems:
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


    print(outp)
    print("\n")

    outp_nw = re.sub('\n', '', outp)
    outp_nw = re.sub('\s+', ' ', outp)
    print(outp_nw)


if __name__ == "__main__":
    main()
