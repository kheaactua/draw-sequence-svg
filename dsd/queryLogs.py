#!/usr/bin/env python3

from __future__ import print_function

import dsd.loaddata as ld
from dsd.svgobjs import Diagram

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = ld.get_arg_parse()
    parser.add_argument(
        '--hosts',
        action='store',
        metavar='HOSTS',
        nargs='+',
        help='List of hosts to include'
    )
    parser.add_argument(
        '-i', '--capture-file',
        metavar='EVENTS',
        dest='capture_filename',
        action='store',
        required=True,
        help='List of events to query'
    )
    parser.add_argument(
        '-e', '--events',
        metavar='EVENTS',
        dest='events',
        nargs='+',
        default=['StartCall', 'EndCall', 'endMedia', 'CDRType1'],
        help='List of events to query'
    )
    parser.add_argument(
        '-w', '--write-events',
        metavar='EVENTS_OUTFILE',
        dest='events_outfile',
        help='If provided, write the discovered events to a CSV file'
    )
    parser.add_argument(
        '-o', '--output-svg',
        metavar='SVG_OUTFILE',
        dest='svg_outfile',
        help='If provided, generate an SVG with the discovered data'
    )
    parser.add_argument(
        '-t', '--template',
        metavar='TEMPLATE_FILE',
        dest='template',
        action='store',
        required=False,
        type=ld.argparse_file_exists,
        help='Template SVG file, required if generating an SVG'
    )

    args = parser.parse_args()

    all_hosts, event_types, settings = ld.read_config(args.config)

    # Match the user entered hosts to the configured hosts
    hosts=ld.match_hosts(all_hosts, args.hosts)

    if not len(hosts):
        print('No matched hosts')
        return
    else:
        if args.verbose:
            print('Examining events between %s'%(' '.join([str(x) for x in hosts])))

    events = ld.query_logs(
        capture_filename=args.capture_filename,
        hosts=hosts,
        event_type_names=args.events,
        event_types=event_types,
        settings=settings,
        verbose=args.verbose
    )

    # Filter out hosts not used in any events
    ld.filter_hosts(hosts=hosts, events=events)

    if not len(events):
        print('No events were found for the selected hosts: %s'%(', '.join(hosts) if len(hosts) else '[no matched hosts]'))
        return
    else:
        if args.verbose:
            print('Examining %d events between hosts %s'%(len(events), ' '.join([str(x) for x in hosts])))

    if args.events_outfile:
        ld.write_events(filename=args.events_outfile, events=events)

    if args.svg_outfile:
        template, info = ld.read_template(args.template)
        diag = Diagram(template=template, hosts=hosts, events=events, doc_info=info, settings=settings)
        contents = diag.generate()

        with open(args.svg_outfile, 'w') as f: f.write(contents)

if __name__ == "__main__":
    main()

# vim: sw=4 ts=4 sts=4 expandtab ft=python ffs=unix :
