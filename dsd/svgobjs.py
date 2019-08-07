#!/usr/bin/env python3

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

    def compile(self):
        """ Method to process some values after getting inputs but before exporting SVG """
        pass

class System(SvgObject):
    def __init__(self, id, name, ip):
        super().__init__()
        self.id   = id
        self.name = name
        self.ip   = ip

        self.display_options.width  = 40
        self.display_options.height = 15
        self.display_options.bgcolor = '#000000'
        self.display_options.fontsize = 4.2
        self.display_options.fontcolor = '#ff0000'
        self.display_options.lifeline_length = 0

        # Position that events can use to hook on to
        self.display_options.abs_center = 0

    def __str__(self):
        return '%s [%s]'%(self.name, self.ip)

    def __repr__(self):
        return '%s'%self.id

    def compile(self):
        super().compile()

        self.display_options.abs_center = self.display_options.x + (self.display_options.width/2.0)
        self.display_options.lifeline_length = self.display_options.page_height - self.display_options.height

    def to_svg(self):
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
         style="fill:{bgcolor};stroke-width:0.26px" />
      <path
         style="fill:none;stroke:#000000;stroke-width:0.20;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;stroke-miterlimit:4;stroke-dasharray:0.60,0.20;stroke-dashoffset:0"
         d="m {x_l},{y_l} v {lifeline_length}"
         id="system-{system}-lifeline"
         inkscape:connector-curvature="0"
         sodipodi:nodetypes="cc" />
      <text
         xml:space="preserve"
         style="font-style:normal;font-weight:normal;font-size:{fontsize}px;line-height:125%;font-family:Sans;text-align:center;letter-spacing:0px;word-spacing:0px;text-anchor:middle;fill:{fontcolor};fill-opacity:1;stroke:none;stroke-width:0.25px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
         x="{x_t}"
         y="{y_t}"
         id="system-{system}-label"><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="font-size:{fontsize}px;text-align:center;text-anchor:middle;fill:{fontcolor};stroke-width:0.2px"
           style="text-align:center;text-anchor:middle;stroke-width:0.26px"
           id="system-{system}-label-name">{system_name}</tspan><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="text-align:center;text-anchor:middle;stroke-width:0.26px"
           id="system-{system}-label-ip">{ip}</tspan></text>
    </g>'''.format(
            system=self.id.lower(),
            system_name=self.name,
            ip=self.ip,
            width=self.display_options.width,
            height=self.display_options.height,
            bgcolor=self.display_options.bgcolor,
            fontsize=self.display_options.fontsize,
            fontcolor=self.display_options.fontcolor,
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_r=0, y_r=0,
            x_t=self.display_options.width/2, y_t=self.display_options.height/2,
            x_l=self.display_options.width/2, y_l=self.display_options.height,
            # x_l=self.display_options.width/2, y_l=0,
            lifeline_length=self.display_options.lifeline_length
        )

        return svg

class Event(SvgObject):
    def __init__(self, time, src, dst, event_type, event_style):
        super().__init__()
        self.time      = float(time)
        self.src       = src
        self.dst       = dst
        self.event_type = event_type
        self.event_style = event_style

        self.display_options.fontsize = 3.6

    def __str__(self):
        return '%2.2f: %s->%s %s'%(self.time, self.src, self.dst, self.event_type)

    def __repr__(self):
        return '%2.3f: %s->%s %s'%(self.time, self.src, self.dst, self.event_type)

    def to_svg(self):
        """ Serialize to an XML block """

        a_len = self.dst.display_options.abs_center - self.src.display_options.abs_center
        if self.dst.display_options.abs_center < self.src.display_options.abs_center:
            a_len = -1 * a_len

        # Abs
        # a_start = self.src.display_options.abs_center - self.display_options.x
        a_start = self.src.display_options.abs_center

        # Relative
        a_center = (a_len/2.0) + a_start

        svg = '''<g
     id="{id}-event-group"
     transform="translate({x_g},{y_g})">
    <g
       id="{id}-event"
       transform="translate({x_e},{y_e})">
      <path
         inkscape:connector-curvature="0"
         id="{id}-arrow"
         d="m {x_a},{y_a} h {a_len}"
         style="fill:none;stroke:{eventcolor};stroke-width:0.40;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;marker-end:url(#Arrow2Lend)" />
      <text
         id="{id}-label"
         x="{x_l}"
         y="{y_l}"
         style="font-style:normal;font-weight:normal;font-size:{fontsize}px;line-height:1.25;font-family:sans-serif;letter-spacing:0px;word-spacing:0px;fill:{color};fill-opacity:1;stroke:none;stroke-width:0.25"
         xml:space="preserve"><tspan
           style="font-size:{fontsize}px;stroke-width:0.25"
           x="{x_l}"
           y="{y_l}"
           id="{id}-label-tspan">{name}</tspan></text>
    </g>
    <text
       id="{id}-time-label-text"
       x="{x_t}"
       y="{y_t}"
       style="font-style:normal;font-weight:normal;font-size:{fontsize}px;line-height:1.25;font-family:sans-serif;letter-spacing:0px;word-spacing:0px;fill:{color};fill-opacity:1;stroke:none;stroke-width:0.25"
       xml:space="preserve"><tspan
         style="font-size:{fontsize}px;stroke-width:0.25"
         x="{x_t}"
         y="{y_t}"
         id="{id}-time-label-tspan"
         sodipodi:role="line">{t}</tspan></text>
  </g>'''.format(
            t=self.time,
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_e=self.src.display_options.x - self.display_options.x + (self.src.display_options.width/2.0), y_e=0,
            x_a=0, y_a=0, a_len=a_len,
            x_l=a_len/2.0, y_l=0,
            x_t=0, y_t=0,
            id='time-%s'%re.sub('\W', '', str(self.time)),
            fontsize=self.display_options.fontsize,
            color=self.display_options.color,
            eventcolor=self.event_style.color,
            name=self.event_type,
        )

        return svg

class EventStyle(object):
    def __init__(self, event_type, color):
        self.event_type = event_type
        self.color      = color

    def __repr__(self):
        return '%s(%s)'%(self.event_type, self.color)

class Diagram(object):
    """ Class to build our diagram.  Collects all the data, and then generates an SVG file from a template  """

    def __init__(self, template, systems, events, event_styles, doc_info):
        self.template    = template
        self.systems     = systems
        self.events      = events
        self.doc_info    = doc_info

    def generate(self):
        """ Generate the SVG """

        # First we have to position everything
        svg_systems = ''
        for i, s in enumerate(self.systems):
            s.display_options.x = 60*i + 20 # magic variable
            s.display_options.y = 0
            s.display_options.page_height = self.doc_info['height']
            s.compile()
            svg_systems = svg_systems + s.to_svg()

        events_svg = ''
        for i, e in enumerate(self.events):
            e.display_options.x = 5
            e.display_options.y = int(float(e.time - self.events[0].time) * 5) # magic values
            e.compile()
            events_svg = events_svg + e.to_svg()

        outp = re.sub('{{systems}}',      svg_systems, self.template)
        outp = re.sub('{{time-left}}',    str(0), outp)
        outp = re.sub('{{time-top}}',     str(self.systems[0].display_options.height + 10), outp)
        outp = re.sub('{{events}}',  events_svg, outp)

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
        event_style[e['eventType']] = EventStyle(event_type=e['eventType'], color=e['color'])

    return systems, event_style

def read_data(filename, systems, event_styles):
    csv.register_dialect('eventStyle', delimiter = '\t', skipinitialspace=True)

    data = []
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, dialect='eventStyle')
        for row in reader:
            if len(row) < 4:
                continue
            if re.match('^\s*#', row[0]):
                continue
            src = next(s for s in systems if s.id == row[1])
            dst = next(s for s in systems if s.id == row[2])
            sty = event_styles[row[3]] if row[3] in event_styles else None
            data.append(Event(time=row[0], src=src, dst=dst, event_type=row[3], event_style=sty))

    return data

def read_template(filename):
    """ Import our template, and read some properties from it """
    with open(filename, 'r') as f: contents=f.read()

    # Determine some properties, get the svg tag
    tag = re.search('<svg.*?>', contents, re.MULTILINE|re.S);
    props = re.findall(r'\b(?P<attr>\w+)=\"(?P<val>.*?)\"', tag.group(0), re.MULTILINE)
    info = {}
    for m in props:
        if 'width' == m[0]:
            units=re.match(r'(?P<val>\d+.?\d+)(?P<unit>\w+)', m[1])
            info['width'] = float(units.group('val'))
            info['unit']  = units.group('unit')
        elif 'height' == m[0]:
            units=re.match(r'(?P<val>\d+.?\d+)(?P<unit>\w+)', m[1])
            info['height'] = float(units.group('val'))

    return contents, info

def filter_systems(systems, event_data):
    """ Remove systems that aren't involved in any events """
    for s in systems:
        found = False
        for e in event_data:
            if s == e.src or s == e.dst:
                found = True
                break
        if not found:
            systems.remove(s)

