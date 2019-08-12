#!/usr/bin/env python3

from __future__ import print_function

import argparse
import sys
import os
import csv
import json
import re
import random
import argparse
from aenum import Enum

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

class HostType(Enum):
    APP   = 1
    GA    = 2
    MIS   = 3
    ADMIN = 4
    ELM   = 5
    REC   = 6

    @staticmethod
    def nameToEnum(name):
        if 'APP' == name:
            return self.APP
        elif 'MIS' == name:
            return self.GA
        elif 'GA' == name:
            return self.GA
        elif 'REC' == name:
            return self.REC
        elif 'ADMIN' == name:
            return self.ADMIN
        elif 'ELM' == name:
            return self.ELM
        else:
            raise ValueError('Cannot interpret host type %s'%name)

class Host(SvgObject):
    def __init__(self, id, name, ip, sort_nudge=100, host_type=HostType.APP):
        super().__init__()
        self.id   = id
        self.name = name
        self.ip   = ip
        self.sort_nudge = sort_nudge
        self.host_type=host_type

        self.display_options.width  = 40
        self.display_options.height = 15
        self.display_options.bgcolor = '#c47e6c'
        self.display_options.fontsize = 4.2
        self.display_options.fontcolor = '#000000'
        self.display_options.lifeline_length = 0

        # Position that events can use to hook on to
        self.display_options.abs_center = 0

    @staticmethod
    def match(hosts, name_or_ip):
        """ Provided with a list of systems form a config file, match a specific system by its IP or its name """

        for h in hosts:
            if h.id.lower() == name_or_ip.lower():
                return h
            elif h.name.lower() == name_or_ip.lower():
                return h
            elif h.name.lower() == name_or_ip.lower():
                return h

        return None

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
       id="host-{host}">
      <rect
         id="host-{host}-titlebox"
         width="{width}"
         height="{height}"
         x="{x_r}"
         y="{y_r}"
         style="fill:{bgcolor};stroke-width:0.26px" />
      <path
         style="fill:none;stroke:#000000;stroke-width:0.20;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;stroke-miterlimit:4;stroke-dasharray:0.60,0.20;stroke-dashoffset:0"
         d="m {x_l},{y_l} v {lifeline_length}"
         id="host-{host}-lifeline"
         inkscape:connector-curvature="0"
         sodipodi:nodetypes="cc" />
      <text
         xml:space="preserve"
         style="font-style:normal;font-weight:normal;font-size:{fontsize}px;line-height:125%;font-family:Sans;text-align:center;letter-spacing:0px;word-spacing:0px;text-anchor:middle;fill:{fontcolor};fill-opacity:1;stroke:none;stroke-width:0.25px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
         x="{x_t}"
         y="{y_t}"
         id="host-{host}-label"><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="font-size:{fontsize}px;text-align:center;text-anchor:middle;fill:{fontcolor};stroke-width:0.2px"
           style="text-align:center;text-anchor:middle;stroke-width:0.26px"
           id="host-{host}-label-name">{host_name}</tspan><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="text-align:center;text-anchor:middle;stroke-width:0.26px"
           id="host-{host}-label-ip">{ip}</tspan></text>
    </g>'''.format(
            host=self.id.lower(),
            host_name=self.name,
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
            lifeline_length=self.display_options.lifeline_length
        )

        return svg

class Event(SvgObject):
    def __init__(self, time, src, dst, event_type, event_style):
        super().__init__()
        self.time        = float(time)
        self.time_label  = float(time)
        self.src         = src
        self.dst         = dst
        self.event_type  = event_type
        self.event_style = event_style

        self.display_options.fontsize = 3.3

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
        a_start = self.src.display_options.abs_center

        # Position the label randomely a little
        label_pos = a_len/2.0 + random.randint(int(-1*a_len/4), int(a_len/4))

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
            t=self.time_label,
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_e=self.src.display_options.x - self.display_options.x + (self.src.display_options.width/2.0), y_e=0,
            x_a=0, y_a=0, a_len=a_len,
            x_l=label_pos, y_l=0,
            x_t=0, y_t=0,
            id='time-%s'%re.sub('\W', '', str(self.time)),
            fontsize=self.display_options.fontsize,
            color=self.event_style.color,
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

    def __init__(self, template, hosts, events, event_styles, doc_info, settings):
        self.template    = template
        self.hosts     = hosts
        self.events      = events
        self.doc_info    = doc_info
        self.settings    = settings

    def generate(self):
        """ Generate the SVG """

        # First we have to position everything
        svg_hosts = ''
        for i, s in enumerate(self.hosts):
            s.display_options.x = self.settings['hostSpacing']*i + self.settings['timeMarginLeft']
            s.display_options.y = 0
            s.display_options.page_height = self.doc_info['height']
            s.compile()
            svg_hosts = svg_hosts + s.to_svg()

        events_svg = ''
        for i, e in enumerate(self.events):
            e.display_options.x = self.settings['timeMarginLeft']
            e.display_options.y = int(float(e.time - self.events[0].time) * self.settings['timeSpacing'])
            e.compile()
            events_svg = events_svg + e.to_svg()

        outp = re.sub('{{hosts}}',      svg_hosts, self.template)
        outp = re.sub('{{time-left}}',    str(0), outp)
        outp = re.sub('{{time-top}}',     str(self.hosts[0].display_options.height + 10), outp)
        outp = re.sub('{{events}}',  events_svg, outp)

        return outp

def read_config(filename):
    with open(filename) as json_file:
        data = json.load(json_file)

    # Maybe write something later dst automatically load host objects.  See https://github.com/kheaactua/vim-managecolor/blob/master/lib/cmds.py the CSData.dict_to_obj and stuff
    hosts = []
    for s in data['hosts']:
        hosts.append(Host(
            id=s['id'],
            name=s['name'],
            ip=s['ip'],
            host_type=s['host_type'],
            sort_nudge=s['sort_nudge']
        ))

    # Sort the list
    hosts.sort(key=lambda x: x.sort_nudge)

    event_style = {}
    for e in data['eventTypes']:
        event_style[e['eventType']] = EventStyle(event_type=e['eventType'], color=e['color'])

    return hosts, event_style, data["settings"]

def read_data(filename, hosts, event_styles, settings):
    csv.register_dialect('eventStyle', delimiter = '\t', skipinitialspace=True)

    data = []
    with open(filename, 'r') as csv_file:
        reader = csv.reader(csv_file, dialect='eventStyle')
        for row in reader:
            if len(row) < 4:
                continue
            if re.match('^\s*#', row[0]):
                continue
            src = next(s for s in hosts if s.id == row[1])
            dst = next(s for s in hosts if s.id == row[2])
            sty = event_styles[row[3]] if row[3] in event_styles else None
            data.append(Event(time=row[0], src=src, dst=dst, event_type=row[3], event_style=sty))

    # Make sure there are no huge gaps in the times.  If there are, reduce them
    for i,e in enumerate(data):
        if i==0: continue
        dt = e.time - data[i-1].time
        if dt > settings['maxTimeGap']:
            for en in data[i:]:
                en.time = en.time-(dt-settings['maxTimeGap'])

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

def filter_hosts(hosts, event_data):
    """ Remove hosts that aren't involved in any events """
    host_copy = hosts.copy()
    for s in host_copy:
        found = False
        for e in event_data:
            if s == e.src or s == e.dst:
                found = True
                break
        if not found:
            hosts.remove(s)

def argparse_file_exists(f):
    """ Used by argparse to see whether the filename exists, if so return the filename, otherwise raise an exception """
    if not os.path.exists(f):
        raise argparse.ArgumentTypeError('Cannot read %s'%f)
    else:
        return f

def GetArgParse(*args, **kwargs):
    """ Factory for argparse library with some of the common elements used by every script already loaded """

    parser = argparse.ArgumentParser(*args, *kwargs)
    parser.add_argument(
        '-c', '--config',
        dest='config',
        metavar='FILE',
        action='store',
        help='JSON Config file',
        type=argparse_file_exists,
        default='/tmp/config.json'
    )

    return parser
