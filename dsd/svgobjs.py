#!/usr/bin/env python3

from __future__ import print_function

import argparse
import sys
import os
import re
import random
import datetime
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
    """ Object representing an event (StartCall, EndCall, etc.) with enough
    data to include in a timing diagram """

    def __init__(self, time, src, dst, event_type, time_label=None, event_style=None, packet_id=None, ack_time=None):
        super().__init__()
        self.time        = time
        self.dt          = datetime.timedelta(seconds=0)
        self.time_label  = str(time)
        self.src         = src
        self.dst         = dst
        self.event_type  = event_type
        self.event_style = event_style
        self.packet_id   = packet_id
        self.ack_time    = ack_time

        # TODO this can be a default, but it should also be configurable
        self.display_options.fontsize = 3.3

    def __str__(self):
        return '%s: %s->%s %s'%(self.time_label, self.src, self.dst, self.event_type)

    def __repr__(self):
        return '%s: %s->%s %s'%(self.time, self.src, self.dst, self.event_type)

    @staticmethod
    def sort_and_process(events, settings):
        """ Sort the events by time, and ensure every event has a dt from the first entry """
        events.sort(key=lambda x: x.time)

        if len(events) < 2:
            return

        first_event = events[0]
        for e in events:
            e.dt = e.time - first_event.time

        # Make sure there are no huge gaps in the times.  If there are, reduce them
        if 'maxTimeGap' in settings and int(settings['maxTimeGap']) > 0:
            mdt = datetime.timedelta(seconds=settings['maxTimeGap'])
            for i,e in enumerate(events):
                if i==0: continue
                dt = e.time - events[i-1].time
                if dt > mdt:
                    for en in events[i:]:
                        en.time = en.time-(dt-mdt)

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
            e.display_options.y = int(e.dt.seconds * self.settings['timeSpacing'])
            e.compile()
            events_svg = events_svg + e.to_svg()

        outp = re.sub('{{hosts}}',      svg_hosts, self.template)
        outp = re.sub('{{time-left}}',    str(0), outp)
        outp = re.sub('{{time-top}}',     str(self.hosts[0].display_options.height + 10), outp)
        outp = re.sub('{{events}}',  events_svg, outp)

        return outp

# vim: sw=4 ts=4 sts=0 expandtab ft=python ffs=unix :
