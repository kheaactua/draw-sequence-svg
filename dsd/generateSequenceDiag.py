#!/usr/bin/env python3

from __future__ import print_function

import argparse
import sys
import os
import csv
import json
import re

from svgobjs import *

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = argparse.ArgumentParser(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('-c', '--config',   dest='config',   metavar='FILE', required=True, action='store', type=str, help='JSON Config file')
    parser.add_argument('-i', '--input',    dest='data',     action='store', required=True, type=str, help='CSV file listing the events')
    parser.add_argument('-o', '--output',   dest='output',   action='store', required=True, type=str, help='Output SVG name')
    parser.add_argument('-t', '--template', dest='template', action='store', default='data/template.svg', type=str, help='Template SVG file')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print('Cannot find config file %s'%args.config, file=sys.stderr)

    if not os.path.exists(args.data):
        print('Cannot find data file %s'%args.data, file=sys.stderr)

    if not os.path.exists(args.template):
        print('Cannot find template file %s'%args.data, file=sys.stderr)

    # /Load CLI parameters

    systems, event_styles, settings = read_config(args.config)
    event_data = read_data(args.data, systems=systems, event_styles=event_styles, settings=settings)
    filter_systems(systems=systems, event_data=event_data)
    template, info = read_template(args.template)

    if not systems:
        print('No systems were involved in any of the events.  Aborting', file=sys.stderr)
        sys.exit(1)

    if not event_data:
        print('No events were provided.  Aborting', file=sys.stderr)
        sys.exit(1)

    diag = Diagram(template=template, systems=systems, events=event_data, event_styles=event_styles, doc_info=info, settings=settings)
    contents = diag.generate()

    with open(args.output, 'w') as f: f.write(contents)


if __name__ == "__main__":
    main()
