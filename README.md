# Sequence Diagram Generator

Very rudimentary project to convert well structured data into a sequence diagram.  This is messy, still has some magic numbers in it, and was built for a single purpose.  It does not rely on any SVG libs, but instead more-or-less just uses string manipulation.

# Setup

Two files are required, a `config` file and a `data` file.  See the samples for example.

# Run

`generateSequenceDiag.py -c samples/sample1/config.json -i samples/sample1/events.csv -o diag.svg`
