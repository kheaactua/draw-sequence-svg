#!/usr/bin/env python3

from __future__ import print_function

from loaddata import generate_display_filter, query_logs, get_arg_parse, read_config, match_hosts, write_events

def main():
    """ Loads all the data and prepares the SVG """

    # Load CLI parameters
    parser = get_arg_parse()
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
    parser.add_argument(
        '-w', '--write-events',
        metavar='OUTFILE',
        dest='events_outfile',
        help='If provided, write the discovered events to a CSV file'
    )

    args = parser.parse_args()

    all_hosts, *ed = read_config(args.config)

    # Match the user entered hosts to the configured hosts
    hosts=match_hosts(all_hosts, args.hosts)

    if args.verbose:
        print('Examining events %s between %s'%(', '.join(args.events), ', '.join([str(x) for x in hosts])))
    events = query_logs(
        capture_filename='data/LoggingService_processing.pcapng',
        hosts=hosts,
        events=args.events,
        verbose=args.verbose
    )

    if args.events_outfile:
        write_events(filename=args.events_outfile, events=events)

if __name__ == "__main__":
    main()

# vim: sw=4 ts=4 sts=4 expandtab ft=python ffs=unix :
