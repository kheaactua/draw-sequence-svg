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
- Contains Solacom specific 'objects', searches for I3 events, _etc_. - not generalisable
- Is not based on any SVG library or anything, it pretty much just uses string manipulation to build an SVG file (the code doesn't know any SVG semantics, so it wouldn't be easy to change any of the shapes or make very different diagrams.  There has been a little work to change this though)

## Setup

Two files are required, a `config` file and a `data` file.  See the samples for example.

The values in the `settings` block are defined as:

- `hostSpacing`: Spacing (in display units) between the start of every host timeline
- `timeMarginLeft`: Left marking spacing (in display units)
- `timeSpacing`: Multiplier (in display units) for vertical spacing of a time unit.  _e.g._ event B happens `x` seconds from the start, so place it at `x * timeSpacing` units down the page
- `maxTimeGap`: The maximum allowable space (in seconds) between two events.  Subsequent events with a larger spacing than this will have their spacing collapsed to this value.  The goal of this is to have high resolution time lines without gigantic empty vertical gaps.
- `minLabelTimeGap`: The minimum amount of time between two events for a time label to appear.  The goal of this is to remove overlapping time lables.  _e.g._ If events `A` and `B` occur within 0.005 s, do not show a time label for event `B`
- `timeUnit`: Display style of the time label, only supported value currently is `secondsSinceStart`

### Install

All installations are encouraged to be done in a Python3 virtual enviroment.

#### Install for source

Clone the repo, and in the base directory:
```sh
python setup.py install
````

## Run

To generate a SVG in one command, run

```sh
queryCaptureLogs                                        \
   --config samples/sample1/config.json                 \
   --capture-file data/LoggingService_processing.pcapng \
   --hosts App2A Admin2A MIS2A                          \
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
   --output   diag.svg
```

# Notes

This repo includes some setup config files, data, and README files for particular cases.  These were included as an example of steps taken to diagnose issues (that and I'm not sure where else to save them. :) )

# Developer Notes

- `tspan` objects have been converted into a class as a first step towards converting most/all of the tags into objects.  Once this transformation is complete, the code might be clean enough to leverage a proper SVG package.
- The SvgObject hierarchy needs to be refactored a little now that a `tspan` class exists.  Types such as Events, Hosts, _etc_ should be in their own library, separate from classes such as `tspan`.
