#!/usr/bin/env python3

from __future__ import print_function

import argparse
import sys

from svgobjs import *
from loaddata import *

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = get_arg_parse(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('-i', '--input',    dest='data',     action='store', required=argparse_file_exists, type=str, help='CSV file listing the events')
    parser.add_argument('-o', '--output',   dest='output',   action='store', required=True, type=str, help='Output SVG name')
    parser.add_argument('-t', '--template', dest='template', action='store', default='data/template.svg', type=argparse_file_exists, help='Template SVG file')

    args = parser.parse_args()

    # /Load CLI parameters

    hosts, event_styles, settings = read_config(args.config)
    event_data = read_events(args.data, hosts=hosts, event_styles=event_styles, settings=settings, verbose=args.verbose)
    filter_hosts(hosts=hosts, event_data=event_data)
    template, info = read_template(args.template)

    if not hosts:
        print('No hosts were involved in any of the events.  Aborting', file=sys.stderr)
        sys.exit(1)

    if not event_data:
        print('No events were provided.  Aborting', file=sys.stderr)
        sys.exit(1)

    diag = Diagram(template=template, hosts=hosts, events=event_data, event_styles=event_styles, doc_info=info, settings=settings)
    contents = diag.generate()

    with open(args.output, 'w') as f: f.write(contents)


if __name__ == "__main__":
    main()
