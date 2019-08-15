# Sequence Diagram Generator

Parse a network capture file (_e.g._ captures with tshark or Wireshark or something) and generate a timing diagram from that data.

## Commands

Contains three commands:
- `queryCaptureLogs`: Queries specific `events` out of a capture file.  If given the `-o` flag, will generate a SVG file of these events. (This is the one-command-for-everything command)
- `generateSequenceDiag`: If provided with a CSV of events (built manually or with `queryCaptureLogs`), generates an SVG file
- `generateWireSharkDisplayFilters`: Generates a string of display filters.  These are what are used to filter the capture log

## Misc.

Note that the SVG events will contain a `<info>` tag that contains additional
information, such as the packet ID and the ACK package ID.  This is not
standard, but is a helpful way (for now) of adding additional information into
the diagrams.

## Limitations

- Written quickly and for a purpose, so some aspects (like having a template) do not generalise well
- Written for my current company, so we search for company specific `events` in the packages, so not generalisable
- Is not based on any SVG library or anything, it pretty much just uses string manipulation to build an SVG file (the code doesn't know any SVG semantics, so it wouldn't be easy to change any of the shapes or make very different diagrams.)

## Setup

Two files are required, a `config` file and a `data` file.  See the samples for example.

## Run

```sh
queryCaptureLogs                                        \
   --config samples/cample1/config.json                 \
   --capture-file data/LoggingService_processing.pcapng \
   --hosts App2A Admin2A MIS2A                          \
   --template template.svg                              \
   --write-events /tmp/events.csv                       \
   --output-svg   diag.svg
```

# Notes

This repo includes some setup config files, data, and README files for particular cases.  These were included as an example of steps taken to diagnose issues (that and I'm not sure where else to save them. :) )
