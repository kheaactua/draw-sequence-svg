#!/usr/bin/env python3

from __future__ import print_function

import argparse
import sys

import dsd.solaobjs as so
import dsd.loaddata as ld

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = ld.get_arg_parse(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('-i', '--input',      dest='data',       action='store', required=ld.argparse_file_exists, type=str, help='CSV file listing the events')
    parser.add_argument('-o', '--output',     dest='output',     action='store', required=True, type=str, help='Output SVG name')
    parser.add_argument('-f', '--from-frame', dest='from_frame', action='store', default=None,  type=int, help='Start frame')
    parser.add_argument('-t', '--to-frame',   dest='to_frame',   action='store', default=None,  type=int, help='To frame')

    args = parser.parse_args()

    # /Load CLI parameters

    hosts, event_types, settings = ld.read_config(args.config)
    event_data = ld.read_events(
        args.data,
        hosts=hosts,
        event_types=event_types,
        from_frame=args.from_frame,
        to_frame=args.to_frame,
        settings=settings,
        verbose=args.verbose
    )
    ld.filter_hosts(hosts=hosts, events=event_data)

    if not hosts:
        print('No hosts were involved in any of the events.  Aborting', file=sys.stderr)
        sys.exit(1)

    if not event_data:
        print('No events were provided.  Aborting', file=sys.stderr)
        sys.exit(1)

    diag = so.Diagram(hosts=hosts, events=event_data, settings=settings, inkscape=args.inkscape)
    contents = diag.generate()

    with open(args.output, 'w') as f: f.write(contents)

if __name__ == "__main__":
    main()
