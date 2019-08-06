#!/usr/bin/env python

from __future__ import print_function

import argparse, sys, os, csv, json, re

class System:
    def __init__(self, id, name, ip):
        self.id   = id
        self.name = name
        self.ip   = ip

    def __str__(self):
        return '%s [%s]'%(self.name, self.ip)

    def __repr__(self):
        return '%s'%self.id

    def toSvg(self, x,y):
        svg = '''<g
       transform="translate({x_g},{y_g})"
       id="System-{system}">
      <rect
         id="System-{system}-Titlebox"
         width="50"
         height="20"
         x="{x_t}"
         y="{x_t}"
         style="fill:#808080;stroke-width:0.26458332" />
      <path
         style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
         d="M {x_l},{y_l} V 186.63095"
         id="System-{system}-Lifeline"
         inkscape:connector-curvature="0"
         sodipodi:nodetypes="cc" />
    </g>'''.format(
            system=self.id,
            x_g=14, y_g=0,
            x_t=30, y_t=10,
            x_l=33, y_l=50,
        )

        return svg


class Event:
    def __init__(self, time, src, dst, eventType):
        self.time      = float(time)
        self.src       = src
        self.dst       = dst
        self.eventType = eventType

    def __str__(self):
        return '%2.2f: %s->%s %s'%(self.time, self.src, self.dst, self.eventType)

    def __repr__(self):
        return '%2.3f: %s->%s %s'%(self.time, self.src, self.dst, self.eventType)

class EventStyle:
    def __init__(self, eventType, color):
        self.eventType = eventType
        self.color     = color

class Diagram:
    def __init__(self, template, systems, events, event_style):
        self.template   = template
        self.systems    = systems
        self.events     = events
        self.event_style = event_style

    def generate(self):
        svg_systems = ''
        for i,s in enumerate(self.systems):
            svg_systems = svg_systems + s.toSvg(200*i, 0)

        outp = re.sub('{{systems}}', svg_systems, self.template)

        print(outp)


def read_config(filename):
    with open(filename) as json_file:
        data = json.load(json_file)

    # Maybe write something later dst automatically load system objects.  See https://github.com/kheaactua/vim-managecolor/blob/master/lib/cmds.py the CSData.dict_to_obj and stuff
    systems = []
    for s in data['systems']:
        systems.append(System(s['id'], s['name'], s['ip']))

    event_style = {}
    for e in data['eventTypes']:
        event_style[e['name']] = EventStyle(e['name'], e['color'])

    return systems, event_style

def read_data(filename, systems):
    csv.register_dialect('eventStyle', delimiter = '\t', skipinitialspace=True)

    data = []
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, dialect='eventStyle')
        for row in reader:
            # print(row)
            src = next(s for s in systems if s.id == row[1])
            dst = next(s for s in systems if s.id == row[2])
            data.append(Event(time=row[0], src=src, dst=dst, eventType=row[3]))

    return data

def read_template(filename):
    with open(filename, 'r') as f: contents=f.read()
    return contents

def main(config_filename, data_filename):

    systems, event_style = read_config(config_filename)
    event_data = read_data(data_filename, systems)
    template   = read_template('template.svg')

    diag = Diagram(template=template, systems=systems, events=event_data, event_style=event_style)
    diag.generate()

    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('-c', '--config', dest='config', metavar='FILE', required=True, action='store', type=str, help='JSON Config file')
    parser.add_argument('-i', '--input', dest='data', action='store', required=True, type=str, help='CSV file listing the events')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print('Cannot find config file %s'%args.config, file=sys.stderr)

    if not os.path.exists(args.data):
        print('Cannot find data file %s'%args.data, file=sys.stderr)

    main(config_filename=args.config, data_filename=args.data)
