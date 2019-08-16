# Sequence Diagram Generator

Parse a network capture file (_e.g._ captures with tshark or Wireshark or something) and generate a timing diagram from that data.

## Commands

Contains three commands:
- `queryCaptureLogs`: Queries specific `events` out of a capture file.  If given the `-o` flag, will generate a SVG file of these events. (This is the one-command-for-everything command)
- `generateSequenceDiag`: If provided with a CSV of events (built manually or with `queryCaptureLogs`), generates an SVG file
- `generateWireSharkDisplayFilters`: Generates a string of display filters.  These are what are used to filter the capture log

## Misc.

Note that the SVG events currently have a `onclick` action that calls a function to provide the user with additional information on the event, such as the packet ID and the ACK package ID.  This implementation is not yet, but it exists to be improved upon in the near future.

## Limitations

- Written quickly and for a purpose, so some aspects (like having a template) do not generalise well
- Written for my current company, so we search for company specific `events` in the packages, so not generalisable
- Is not based on any SVG library or anything, it pretty much just uses string manipulation to build an SVG file (the code doesn't know any SVG semantics, so it wouldn't be easy to change any of the shapes or make very different diagrams.)

## Setup

Two files are required, a `config` file and a `data` file.  See the samples for example.

The values in the `settings` block are defined as:

- `hostSpacing`: Spacing (in display units) between the start of every host timeline
- `timeMarginLeft`: Left marking spacing (in display units)
- `timeSpacing`: Multiplier (in display units) for vertical spacing of a time unit.  _e.g._ event B happens `x` seconds from the start, so place it at `x * timeSpacing` units down the page
- `maxTimeGap`: The maximum allowable space (in seconds) between two events.  Subsequent events with a larger spacing than this will have their spacing collapsed to this value.  The goal of this is to have high resolution time lines without gigantic empty vertical gaps.
- `minLabelTimeGap`: The minimum amount of time between two events for a time label to appear.  The goal of this is to remove overlapping time lables.  _e.g._ If events `A` and `B` occur within 0.005 s, do not show a time label for event `B`
- `timeUnit`: Display style of the time label, only supported value currently is `secondsSinceStart`

## Run

To generate a SVG in one command, run

```sh
queryCaptureLogs                                        \
   --config samples/sample1/config.json                 \
   --capture-file data/LoggingService_processing.pcapng \
   --hosts App2A Admin2A MIS2A                          \
   --template template.svg                              \
   --write-events /tmp/events.csv                       \
   --output-svg   diag.svg
```

Or, you can seperate this into two commands,
```sh
# Fetch the event data from the capture log
queryCaptureLogs                                        \
   --config samples/sample1/config.json                 \
   --capture-file data/LoggingService_processing.pcapng \
   --hosts App2A Admin2A MIS2A                          \
   --write-events /tmp/events.csv

# Generate the SVG
generateSequenceDiag                    \
   --config samples/sample1/config.json \
   --input /tmp/events.csv              \
   --template template.svg              \
   --output   diag.svg
```

# Notes

This repo includes some setup config files, data, and README files for particular cases.  These were included as an example of steps taken to diagnose issues (that and I'm not sure where else to save them. :) )
