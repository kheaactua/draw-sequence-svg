#!/usr/bin/env python

from __future__ import print_function

import argparse
import sys
import os
import csv
import json
import re

class DisplayOptions(object):
    def __init__(self, x,y):
        self.x = x
        self.y = y
        self.color = '#000000'
        self.fontsize = 10

class SvgObject(object):
    """ Container for display objects like position, etc """

    def __init__(self):
        self.display_options = DisplayOptions(0,0)

class System(SvgObject):
    def __init__(self, id, name, ip):
        super().__init__()
        self.id   = id
        self.name = name
        self.ip   = ip

        self.display_options.width  = 50
        self.display_options.height = 20
        self.display_options.bgcolor = '#FF0000'
        self.display_options.fontsize = 12
        self.display_options.fontcolor = '#FF0000'

    def __str__(self):
        return '%s [%s]'%(self.name, self.ip)

    def __repr__(self):
        return '%s'%self.id

    def to_svg(self, top):
        """ Serialize to an XML block """

        svg = '''<g
       transform="translate({x_g},{y_g})"
       id="system-{system}">
      <rect
         id="system-{system}-titlebox"
         width="{width}"
         height="{height}"
         x="{x_r}"
         y="{y_r}"
         style="fill:#{bgcolor};stroke-width:0.26458332" />
      <path
         style="fill:none;stroke:#000000;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
         d="M {x_l},{y_l} V 186.63095"
         id="System-{system}-Lifeline"
         inkscape:connector-curvature="0"
         sodipodi:nodetypes="cc" />
      <text
         xml:space="preserve"
         style="font-style:normal;font-weight:normal;font-size:{fontsize}pt;line-height:125%;font-family:Sans;text-align:center;letter-spacing:0px;word-spacing:0px;text-anchor:middle;fill:{fontcolor};fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
         x="{x_t}"
         y="{y_t}"
         id="system-{system}-label"><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="text-align:center;text-anchor:middle;stroke-width:0.26458332px"
           id="system-{system}-label-name">{system}</tspan><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="text-align:center;text-anchor:middle;stroke-width:0.26458332px"
           id="system-{system}-label-ip">{ip}</tspan></text>
    </g>'''.format(
            system=self.id,
            ip=self.ip,
            width=self.display_options.width,
            height=self.display_options.height,
            bgcolor=self.display_options.bgcolor,
            fontsize=self.display_options.fontsize,
            fontcolor=self.display_options.fontcolor,
            x_g=14, y_g=0,
            x_r=30, y_r=10,
            x_l=33, y_l=50,
            x_t=33, y_t=50,
        )

        return svg

class Event(SvgObject):
    def __init__(self, time, src, dst, eventType):
        super().__init__()
        self.time      = float(time)
        self.src       = src
        self.dst       = dst
        self.eventType = eventType

        self.display_options.fontsize = 3.6

    def __str__(self):
        return '%2.2f: %s->%s %s'%(self.time, self.src, self.dst, self.eventType)

    def __repr__(self):
        return '%2.3f: %s->%s %s'%(self.time, self.src, self.dst, self.eventType)

    def to_svg(self):
        """ Serialize to an XML block """

        svg = '''<text
       xml:space="preserve"
       style="font-style:normal;font-weight:normal;font-size:{fontsize}px;line-height:1.25;font-family:sans-serif;letter-spacing:0px;word-spacing:0px;fill:{color};fill-opacity:1;stroke:none;stroke-width:0.26458332"
       x="{x}"
       y="{y}"
       id="timepoint-1"><tspan
         sodipodi:role="line"
         id="{id}"
         x="{x}"
         y="{y}"
         style="stroke-width:0.26458332;font-size:{fontsize}px">{t}</tspan></text>'''.format(
            t=self.time,
            x=self.display_options.x, y=self.display_options.y,
            id='time-label-%s'%re.sub('\W', '', str(self.time)),
            fontsize=self.display_options.fontsize,
            color=self.display_options.color
        )

        return svg

class EventStyle(object):
    def __init__(self, eventType, color):
        self.eventType = eventType
        self.color     = color

class Diagram(object):
    """ Class to build our diagram.  Collects all the data, and then generates an SVG file from a template  """

    def __init__(self, template, systems, events, event_style, doc_info):
        self.template    = template
        self.systems     = systems
        self.events      = events
        self.event_style = event_style
        self.doc_info    = doc_info

    def generate(self):
        """ Generate the SVG """

        # First we have to position everything
        svg_systems = ''
        for i, s in enumerate(self.systems):
            s.display_options.x = 200*i # magic variable
            s.display_options.y = 0
            svg_systems = svg_systems + s.to_svg(top=self.doc_info['height'])

        time_labels = ''
        for i, e in enumerate(self.events):
            e.display_options.x = 0
            e.display_options.y = 20 * i # magic variable
            time_labels = time_labels + e.to_svg()

        outp = re.sub('{{systems}}',     svg_systems, self.template)
        outp = re.sub('{{time-labels}}', time_labels, outp)

        return outp

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
    """ Import our template, and read some properties from it """
    with open(filename, 'r') as f: contents=f.read()

    # # Determine some properties
    # props = re.findall(r'inkscape:(?P<param>[\w-]+)=\"(?P<value>.*?)\"', contents, re.MULTILINE)
    # info = {}
    # for m in props:
    #     info[m[0]] = m[1]

    # Determine some properties, get the svg tag
    tag = re.search('<svg.*?>', contents, re.MULTILINE|re.S);
    props = re.findall(r'\b(?P<attr>\w+)=\"(?P<val>.*?)\"', tag.group(0), re.MULTILINE)
    info = {}
    for m in props:
        if 'width' == m[0]:
            units=re.match(r'(?P<val>\d+.?\d+)(?P<unit>\w+)', m[1])
            info['width'] = units.group('val')
            info['unit']  = units.group('unit')
        elif 'height' == m[0]:
            units=re.match(r'(?P<val>\d+.?\d+)(?P<unit>\w+)', m[1])
            info['height'] = units.group('val')

    return contents, info

def main(config_filename, data_filename, output_filename):
    """ Loads all the data and prepares the SVG """

    systems, event_style = read_config(config_filename)
    event_data = read_data(data_filename, systems)
    template, info = read_template('template.svg')

    diag = Diagram(template=template, systems=systems, events=event_data, event_style=event_style, doc_info=info)
    contents = diag.generate()

    with open(output_filename, 'w') as f: f.write(contents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate an SVG of a sequence diagram based on input data')
    parser.add_argument('-c', '--config', dest='config', metavar='FILE', required=True, action='store', type=str, help='JSON Config file')
    parser.add_argument('-i', '--input', dest='data', action='store', required=True, type=str, help='CSV file listing the events')
    parser.add_argument('-o', '--output', dest='output', action='store', required=True, type=str, help='Output SVG name')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print('Cannot find config file %s'%args.config, file=sys.stderr)

    if not os.path.exists(args.data):
        print('Cannot find data file %s'%args.data, file=sys.stderr)

    main(config_filename=args.config, data_filename=args.data, output_filename=args.output)
