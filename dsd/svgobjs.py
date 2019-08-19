#!/usr/bin/env python3

from __future__ import print_function

import argparse
import sys
import os
import re
import random
import datetime
from aenum import Enum

class JsonSerializatble(object):
    @staticmethod
    def json2py_name(name):
        """ Converts camel case JSON attribute names to python snake case names """
        return re.sub(r'([A-Z])', r'_\1', name).lower()

    def __getattr__(self, attr):
        if attr.startswith('_'):
            return super(JsonSerializatble, self).__getattribute__(attr) # pylint: disable-no-member
        elif attr in self._data:
            return self._data[attr]
        else:
            return None

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            super(JsonSerializatble, self).__setattr__(attr, value)
        else:
            self._data[self.json2py_name(attr)] = value

    @classmethod
    def from_json(cls, data):
        return cls(data)

    def update(self, obj):
        if type(obj) is dict:
            for k,v in obj.items():
                self._data[self.json2py_name(k)] = v
        else:
            super(DisplayOptions, self).__setattr__('_data', dict(self._data, **obj._data))

class DisplayOptions(JsonSerializatble):
    def __init__(self, data: dict = {}):
        super(DisplayOptions, self).__setattr__('_data', {})
        super(DisplayOptions, self).__setattr__('_defaults', {})

        self._defaults = {
            'x': 0,
            'y': 0,
            'width': 1,
            'height': 1,
            'color': '#000000', # deprecated
            'font_size': 10,
            'font_color': '#000000',
        }

        self.update(data)

    def __getattr__(self, attr):
        if super(DisplayOptions, self).__getattr__(attr) is None and attr in super(DisplayOptions, self).__getattr__('_defaults'):
            return super(DisplayOptions, self).__getattr__('_defaults')[attr]
        else:
            return super(DisplayOptions, self).__getattr__(attr)

    def __str__(self):
        return str(self._data)

    def text_style(self):
        """ Return the content for a <text> style attribute """
        parts = []
        parts.append(['font-style',       'normal'])
        parts.append(['font-weight',      'normal'])
        parts.append(['font-size',        '%fpx'%self.font_size])
        parts.append(['line-height',      '125%'])
        parts.append(['font-family',      'Sans'])
        parts.append(['text-align',       'center'])
        parts.append(['letter-spacing',   '0px'])
        parts.append(['word-spacing',     '0px'])
        parts.append(['text-anchor',      'middle'])
        parts.append(['fill',             self.font_color])
        parts.append(['fill-opacity',     '1'])
        parts.append(['stroke',           'none'])
        parts.append(['stroke-width',     '0.25px'])
        parts.append(['stroke-linecap',   'butt'])
        parts.append(['stroke-linejoin',  'miter'])
        parts.append(['stroke-opacity',   '1'])

        parts2=[]
        for p in parts:
            parts2.append(':'.join(p))

        return ';'.join(parts2)

    def tspan_style(self):
        """ Return the content for a <text> style attribute """
        parts = []
        parts.append(['font-style',    'normal'])
        parts.append(['text-align',    'center'])
        parts.append(['text-anchor',   'middle'])
        parts.append(['fill',          self.font_color])
        parts.append(['font-family',   'Sans'])
        parts.append(['stroke-width',  '0.26px'])

        parts2=[]
        for p in parts:
            parts2.append(':'.join(p))

        return ';'.join(parts2)

class SvgObject(object):
    """ Container for display objects like position, etc """

    def __init__(self):
        self.display_options = DisplayOptions()

    def compile(self):
        """ Method to process some values after getting inputs but before exporting SVG """
        pass

class HostType(Enum):
    """ ENUM to distinguish host type """

    APP   = 1
    GA    = 2
    MIS   = 3
    ADMIN = 4
    ELM   = 5
    REC   = 6

    @staticmethod
    def name_to_enum(name):
        if 'APP' == name:
            return HostType.APP
        elif 'MIS' == name:
            return HostType.GA
        elif 'GA' == name:
            return HostType.GA
        elif 'REC' == name:
            return HostType.REC
        elif 'ADMIN' == name:
            return HostType.ADMIN
        elif 'ELM' == name:
            return HostType.ELM
        else:
            raise ValueError('Cannot interpret host type %s'%name)

class Host(SvgObject):
    """ Host (App, Admin, etc) system """

    def __init__(self, id: str, name: str, ip: str, host_type: HostType, sort_nudge: int=100, display_options: DisplayOptions=None, description: str=None):
        super(Host, self).__init__()
        self.id          = id
        self.name        = name
        self.ip          = ip
        self.sort_nudge  = sort_nudge
        self.host_type   = host_type
        self.description = description

        self.display_options.width  = 40
        self.display_options.height = 15
        self.display_options.background_color = '#c47e6c'
        self.display_options.font_size = 4.2
        self.display_options.lifeline_length = 0

        if not display_options is None:
            self.display_options.update(display_options)

        # Position that events can use to hook on to
        self.display_options.abs_center = 0

    @classmethod
    def from_json(cls, data):
        display_options = None
        if 'displayOptions' in data:
            display_options = DisplayOptions.from_json(data['displayOptions'])
            del data['displayOptions']

        # Adjust the HostType
        data['host_type'] = HostType.name_to_enum(data['hostType'])
        del data['hostType']

        data['sort_nudge'] = data['sortNudge']
        del data['sortNudge']

        host = cls(**data, display_options=display_options)
        return host

    @staticmethod
    def match(hosts, name_or_ip):
        """ Provided with a list of systems form a config file, match a specific system by its IP or its name """

        for h in hosts:
            if h.id.lower() == name_or_ip.lower():
                return h
            elif h.name.lower() == name_or_ip.lower():
                return h
            elif h.ip.lower() == name_or_ip.lower():
                return h

        return None

    def __str__(self):
        return '%s [%s]'%(self.name, self.ip)

    def __repr__(self):
        return '%s'%self.id

    def compile(self, settings):
        super().compile()

        self.display_options.abs_center = self.display_options.x + (self.display_options.width/2.0)
        if self.last_event:
            self.display_options.lifeline_length = int(self.last_event.dt.total_seconds() * settings.time_spacing)  + self.display_options.height

    def to_svg(self):
        """ Serialize to an XML block """

        # Name
        y_t=self.display_options.height * (3/7)
        # IP
        y_t2=self.display_options.height * (6/7)

        stroke_width = 0.1
        if self.host_type is HostType.APP:
            stroke_width = 0.6

        rect_style = "fill:{background_color};stroke-width:{stroke_width}px;stroke-miterlimit:4;stroke-dasharray:none;stroke:{stroke_color};stroke-opacity:1".format(
            background_color=self.display_options.background_color,
            stroke_width=stroke_width,
            stroke_color='#000000',
        )

        def escape(s):
            s = s.replace("'", r"\\'")
            return s

        description_action = ''
        if type(self.description) is str and len(self.description):
            description_action=' onclick="show_host_info(\'{description}\')"'.format(description=escape(self.description))


        svg = '''<g
       transform="translate({x_g},{y_g})"
       id="host-{host}">
      <rect
         id="host-{host}-titlebox"
         width="{width}"
         height="{height}"
         x="{x_r}"
         y="{y_r}"
         style="{rect_style}"
         {description_action} />
      <path
         style="fill:none;stroke:#000000;stroke-width:0.20;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;stroke-miterlimit:4;stroke-dasharray:0.60,0.20;stroke-dashoffset:0"
         d="m {x_l},{y_l} v {lifeline_length}"
         id="host-{host}-lifeline"
         inkscape:connector-curvature="0"
         sodipodi:nodetypes="cc" />
      <text
         xml:space="preserve"
         style="{text_style}"
         x="{x_t}"
         y="{y_t}"
         id="host-{host}-label"><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t}"
           style="{tspan_style}"
           id="host-{host}-label-name">{host_name}</tspan><tspan
           sodipodi:role="line"
           x="{x_t}"
           y="{y_t2}"
           style="text-align:center;text-anchor:middle;stroke-width:0.26px"
           id="host-{host}-label-ip">{ip}</tspan></text>
    </g>'''.format(
            host=self.id.lower(),
            host_name=self.name,
            ip=self.ip,
            width=self.display_options.width,
            rect_style=rect_style,
            description_action=description_action,
            height=self.display_options.height,
            text_style=self.display_options.text_style(),
            tspan_style=self.display_options.tspan_style(),
            fontSize=self.display_options.fontSize,
            fontColor=self.display_options.fontColor,
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_r=0, y_r=0,
            x_t=self.display_options.width/2, y_t=y_t, y_t2=y_t2,
            x_l=self.display_options.width/2, y_l=self.display_options.height,
            lifeline_length=self.display_options.lifeline_length
        )

        return svg

class EventType(object):
    """ Hold information about an event """

    def __init__(self, event_type: str, display_options: DisplayOptions=None):
        self.name = event_type

        # Defaults
        self.display_options = DisplayOptions({
            'color': '#000000',
            'font_size': 3.0,
        })
        if not display_options is None:
            self.display_options.update(display_options)

    @classmethod
    def from_json(cls, data):
        display_options = None
        if 'displayOptions' in data:
            display_options = DisplayOptions.from_json(data['displayOptions'])
        name = data['eventType']

        es = cls(event_type=name, display_options=display_options)
        return es

    def __repr__(self):
        return '%s(%s)'%(self.name, self.display_options.color)

class EventAckSpeed(Enum):
    """ ENUM for how we consider how fast an Event is """

    NORMAL    = 1
    SLOW      = 2
    VERY_SLOW = 3

class Event(SvgObject):
    """ Object representing an event (StartCall, EndCall, etc.) with enough
    data to include in a timing diagram """

    def __init__(
        self,
        time: datetime.datetime,
        src: Host,
        dst: Host,
        event_type: EventType,
        settings: None,
        time_label=None,
        frame_id: int=None,
        ack_time: int=None,
        ack_frame_id: int=None
    ):
        super().__init__()

        """ Settings object """
        self.settings = settings

        """ Time of the event """
        self.time         = time

        """ Time since first event """
        self.dt           = datetime.timedelta(seconds = 0)

        """ Time label the user will see """
        self.time_label   = str(time)

        """ Source/dest hosts """
        self.src          = src
        self.dst          = dst

        """ EventType """
        self.event_type   = event_type

        """ Frame ID in the capture logs """
        self.frame_id     = int(frame_id)

        """ Frame ID of the ACK message """
        self.ack_frame_id = int(ack_frame_id) if ack_frame_id is not None else None

        """ The "speed type" we consider the event to have had, set when ack_time is set """
        self.event_ack_speed = EventAckSpeed.NORMAL

        """ Time it took to receive the ACK """
        self.ack_time     = float(ack_time) if ack_time is not None else None

        """ Pointer to previous event (set in sort_and_process) """
        self.prev = None

        """ Pointer to next previous event (set in sort_and_process) """
        self.next = None

    def __str__(self):
        return '%s: %s->%s %s'%(self.time_label, self.src, self.dst, self.event_type)

    def __repr__(self):
        return '%s: %s->%s %s'%(self.time, self.src, self.dst, self.event_type)

    @property
    def ack_time(self):
        return self._ack_time

    @ack_time.setter
    def ack_time(self, value):
        self._ack_time = float(value)
        if self.settings:
            if self.ack_time > self.settings.ack_threshold_very_slow:
                self.event_ack_speed = EventAckSpeed.VERY_SLOW
            elif self.ack_time > self.settings.ack_threshold_slow:
                self.event_ack_speed = EventAckSpeed.SLOW
            else:
                self.event_ack_speed = EventAckSpeed.NORMAL

    @staticmethod
    def sort_and_process(events, settings):
        """ Sort the events by time, and ensure every event has a dt from the first entry """
        events.sort(key=lambda x: x.time)

        for i,e in enumerate(events):
            e.settings = settings
            if i != 0:
                e.prev = events[i-1]
            if i != (len(events)-1):
                e.next = events[i+1]

            e.dt = e.time - events[0].time

            if settings.time_unit == 'secondsSinceStart':
                e.time_label = '%4.3f'%e.dt.total_seconds()

        if len(events) < 2:
            return

        # Make sure there are no huge gaps in the times.  If there are, reduce them
        if float(settings.max_time_gap) > 0:
            mdt = datetime.timedelta(seconds=settings.max_time_gap)
            for i,e in enumerate(events):
                if i==0: continue
                dt = events[i].time - events[i-1].time
                if dt > mdt:

                    for en in events[i:]:
                        en.dt = en.dt - (dt-mdt)

    def to_svg(self):
        """ Serialize to an XML block """

        a_len = self.dst.display_options.abs_center - self.src.display_options.abs_center
        if self.dst.display_options.abs_center < self.src.display_options.abs_center:
            a_len = -1 * a_len

        # Abs
        a_start = self.src.display_options.abs_center

        # Position the label randomely a little
        label_pos = a_len/2.0 + random.randint(int(-1*a_len/4), int(a_len/4))

        event_label = self.event_type.name
        if type(self.ack_time) is float:
            event_label += ' ('
            if self.event_ack_speed == EventAckSpeed.VERY_SLOW:
                event_label += '<tspan style="fill:{color};">{ack_time:0.0f}</span>'.format(color='#ff0000', ack_time=self.ack_time)
            elif self.event_ack_speed == EventAckSpeed.SLOW:
                event_label += '<tspan style="fill:{color};">{ack_time:0.0f}</span>'.format(color='#ff00ff', ack_time=self.ack_time)
            else:
                event_label += '%0.0f'%self.ack_time
            event_label += ' ms)'

        x_t = 0
        time_text_obj = '''<text
       id="{id}-time-label-text"
       x="{x_t}"
       y="{y_t}"
       style="{text_style}"
       xml:space="preserve"><tspan
         style="{tspan_style}"
         x="0"
         y="0"
         id="{id}-time-label-tspan"
         sodipodi:role="line">{t}</tspan></text>'''.format(
            id='time-%s'%re.sub('\W', '', str(self.time)),
            x_t=x_t, y_t=0,
            text_style=self.event_type.display_options.text_style(),
            tspan_style=self.event_type.display_options.text_style(),
            t=self.time_label,
        )

        if self.prev:
            dt = self.time - self.prev.time
            if dt < datetime.timedelta(seconds=self.settings.min_label_time_gap):
                time_text_obj=''

        def inject_capture_info(e):
            """ Tiny lambda to include some additional info about the event in
            the SVG.  This is done this way because I am still unsure of a good
            way to do this, so a lambda gives me flexibility. """

            return '''onclick="show_capture_info({{'time': new Date('{time}'), 'eventType': '{event_type}', 'frameId': {frame_id}, 'ackFrameId': {ack_frame_id}, 'ackTime': {ack_time}}})"'''.format(
                    time=e.time,
                    event_type=e.event_type.name,
                    ack_time=e.ack_time,
                    frame_id=e.frame_id,
                    ack_frame_id=e.ack_frame_id,
                )

        def arrow_id(e):
            """ Select the proper arrow ID, these are defined in the template """
            if e.event_ack_speed == EventAckSpeed.VERY_SLOW:
                return 'Arrow2Mend'
            elif e.event_ack_speed == EventAckSpeed.SLOW:
                return 'Arrow2MendX'
            else:
                return 'Arrow2MendR'


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
         style="fill:none;stroke:{event_color};stroke-width:0.40;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;marker-end:url(#{arrow_id})" />
      <text
         id="{id}-label"
         x="{x_l}"
         y="{y_l}"
         style="{text_style}"
         xml:space="preserve"><tspan
           style="{tspan_style}"
           x="{x_l}"
           y="{y_l}"
           id="{id}-label-tspan" {show_capture_info}>{event_label}</tspan></text>
    </g>'''.format(
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_e=self.src.display_options.x - self.display_options.x + (self.src.display_options.width/2.0), y_e=0,
            x_a=0, y_a=0, a_len=a_len,
            x_l=label_pos, y_l=0,
            time=self.time, show_capture_info=inject_capture_info(self),
            id='time-%s'%re.sub('\W', '', str(self.time)),
            arrow_id=arrow_id(self),
            text_style=self.event_type.display_options.text_style(),
            tspan_style=self.event_type.display_options.text_style(),
            event_color=self.event_type.display_options.color,
            event_label=event_label,
            time_text_obj=time_text_obj
        )
        if time_text_obj:
            svg += '\n    ' + time_text_obj + '\n'
        svg += '  </g>'

        return svg

class Diagram(object):
    """ Class to build our diagram.  Collects all the data, and then generates an SVG file from a template  """

    def __init__(self, template, hosts, events, doc_info, settings, inkscape=False):
        self.template    = template
        self.hosts       = hosts
        self.events      = events
        self.doc_info    = doc_info
        self.settings    = settings
        self.inkscape    = inkscape

    def generate(self):
        """ Generate the SVG """

        # First we have to position everything
        svg_hosts = ''
        for i, h in enumerate(self.hosts):
            h.display_options.x = self.settings.host_spacing*i + self.settings.time_margin_left
            h.display_options.y = 0
            h.last_event = next((e for e in reversed(self.events) if e.src==h or e.dst==h), None)
            h.compile(settings=self.settings)
            svg_hosts = svg_hosts + h.to_svg()

        events_svg = ''
        for i, e in enumerate(self.events):
            e.display_options.x = self.settings.time_margin_left
            e.display_options.y = int(e.dt.total_seconds() * self.settings.time_spacing)
            e.compile()
            events_svg = events_svg + e.to_svg()

        page_height = int(self.events[len(self.events)-1].dt.total_seconds() * self.settings.time_spacing) + 20
        page_width = len(self.hosts)*self.settings.host_spacing + self.settings.time_margin_left + self.hosts[len(self.hosts)-1].display_options.width

        outp = re.sub('{{hosts}}',       svg_hosts, self.template)
        outp = re.sub('{{time-left}}',   str(0), outp)
        outp = re.sub('{{time-top}}',    str(self.hosts[0].display_options.height + 10), outp)
        outp = re.sub('{{events}}',      events_svg, outp)
        outp = re.sub('{{page_width}}',  str(page_width), outp)
        outp = re.sub('{{page_height}}', str(page_height), outp)

        if not self.inkscape:
            outp = re.sub('inkscape:[a-z-]+=".*?"\s*', '', outp)
            outp = re.sub('sodipodi:[a-z-]+=".*?"\s*', '', outp)

        return outp

# vim: sw=4 ts=4 sts=0 expandtab ft=python ffs=unix :
