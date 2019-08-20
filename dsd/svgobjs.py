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

class SvgType(Enum):
    """ ENUM output type (plain SVG or inkscape) """

    PLAIN     = 1
    INKSCAPE  = 2

class Tspan(SvgObject):
    """ A class that actually maps to a SVG tag - likely should have done this a while ago.  This object builds a <tspan> tag.

    This class might be temporary though, if I can make use of it, I can probably upgrade to an actual SVG library. (just right now all the code is too far away from that.)
    """

    def __init__(self, value: str='', settings=None):
        self.id = None
        self._position = None
        self._sodipodi = {}
        self._inkscape = {}
        self._style = {}
        self.value = value
        self.on_click = None

        self.settings = settings
        if settings:
            self.type = settings.svg_type
        else:
            self.type = SvgType.PLAIN

    @property
    def x(self):
        if self._position is not None:
            return self._position['x']
        return None
    @x.setter
    def x(self, val):
        if self._position is None:
            self._position={'x': val, 'y': 0}
        else:
            self._position['x'] = val
    @property
    def y(self):
        if self._position is not None:
            return self._position['y']
        return None
    @x.setter
    def y(self, val):
        if self._position is None:
            self._position={'x': 0, 'y': val}
        else:
            self._position['y'] = val
    @property
    def position(self):
        if self._position is not None:
            return self._position
        return None
    @position.setter
    def position(self, val):
        self._position={'x': val[0], 'y': val[1]}

    @property
    def role(self):
        if 'role' in self._sodipodi:
            return self._sodipodi['role']
        else:
            return None
    @role.setter
    def role(self, val):
        self._sodipodi['role'] = val

    @property
    def font_color(self):
        if 'fill' in self._style:
            return self._style['fill']
        else:
            return None
    @font_color.setter
    def font_color(self, val):
        self._style['fill'] = val

    @property
    def font_size(self):
        if 'font-size' in self._style:
            return self._style['font-size']
        else:
            return None
    @font_size.setter
    def font_size(self, val):
        self._style['font-size'] = val

    @property
    def text_align(self):
        if 'text-align' in self._style:
            return self._style['text-align']
        else:
            return None
    @text_align.setter
    def text_align(self, val):
        self._style['text-align'] = val

    @property
    def text_anchor(self):
        if 'text-anchor' in self._style:
            return self._style['text-anchor']
        else:
            return None
    @text_anchor.setter
    def text_anchor(self, val):
        self._style['text-anchor'] = val

    def to_svg(self):
        attrs={}
        if self._position:
            attrs['x'] = self._position['x']
            attrs['y'] = self._position['y']

        if SvgType.INKSCAPE == self.type:
            for k,v in self._sodipodi.items():
                attrs['sodipodi:%s'%k] = v
            for k,v in self._inkscape.items():
                attrs['inkscape:%s'%k] = v

        if len(self._style):
            parts=[]
            for k,v in self._style.items():
                parts.append('%s:%s'%(k,v))
            attrs['style'] = ';'.join(parts)

        if self.on_click: attrs['onclick'] = str(self.on_click)
        if self.id:       attrs['id']      = str(self.id)

        s = '<tspan'
        if len(attrs):
            s += ' %s'%' '.join(['%s="%s"'%(k,v) for k,v in attrs.items()])
        s += '>%s</tspan>'%self.value

        return s

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

    def __init__(self, id: str, name: str, ip: str, host_type: HostType, sort_nudge: int=100, display_options: DisplayOptions=None, description: str=None, settings=None):
        super(Host, self).__init__()
        self.id          = id
        self.name        = name
        self.ip          = ip
        self.sort_nudge  = sort_nudge
        self.host_type   = host_type
        self.description = description
        self.settings    = settings

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

        self.settings=settings
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


        host_name = Tspan(self.name, settings=self.settings)
        host_name.position = (self.display_options.width/2, y_t)
        host_name.id = 'host-{host}-label-name'.format(host=self.id.lower())
        host_name.font_size = '4.3px'
        host_name.font_color = self.display_options.font_color
        host_name.text_anchor = 'middle'
        host_name.role = 'line'

        host_ip = Tspan(self.ip, settings=self.settings)
        host_ip.position = (host_name.x, y_t2)
        host_ip.id = 'host-{host}-label-ip'.format(host=self.id.lower())
        host_ip.font_size = '4.2px'
        host_ip.font_color = self.display_options.font_color
        host_ip.text_anchor = 'middle'
        host_ip.role = 'line'

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
         id="host-{host}-label">{host_name}{ip}</text>
    </g>'''.format(
            host=self.id.lower(),
            host_name=host_name.to_svg(),
            ip=host_ip.to_svg(),
            width=self.display_options.width,
            rect_style=rect_style,
            description_action=description_action,
            height=self.display_options.height,
            text_style=self.display_options.text_style(),
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_r=0, y_r=0,
            x_t=self.display_options.width/2, y_t=y_t,
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

    FAST      = 1
    NORMAL    = 2
    SLOW      = 3
    VERY_SLOW = 4

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

        """ Time it took to receive the ACK (s) """
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
            elif self.ack_time < self.settings.ack_threshold_fast:
                self.event_ack_speed = EventAckSpeed.FAST
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

        id_prefix = 'time-%s'%re.sub('\W', '', str(self.time))

        a_len = self.dst.display_options.abs_center - self.src.display_options.abs_center
        if self.dst.display_options.abs_center < self.src.display_options.abs_center:
            a_len = -1 * a_len

        # Abs
        a_start = self.src.display_options.abs_center

        # Position the label randomely a little
        label_pos = a_len/2.0 + random.randint(int(-1*a_len/4), int(a_len/4))

        time_label_tspan = Tspan(self.time_label)
        time_label_tspan.position = (0,0)
        time_label_tspan.id = '{id}-time-label-tspan'.format(id=id_prefix)

        x_t = 0
        time_text_obj = '''<text
       id="{id}-time-label-text"
       x="{x_t}"
       y="{y_t}"
       style="{text_style}"
       xml:space="preserve">{t}</text>'''.format(
            id='%s-text'%id_prefix,
            x_t=x_t, y_t=0,
            text_style=self.event_type.display_options.text_style(),
            t=time_label_tspan.to_svg(),
        )

        if self.prev:
            dt = self.time - self.prev.time
            if dt < datetime.timedelta(seconds=self.settings.min_label_time_gap):
                time_text_obj=''


        def arrow_id(e):
            """ Select the proper arrow ID, these are defined in the template """
            if e.event_ack_speed == EventAckSpeed.VERY_SLOW:
                return 'ArrowRightVerySlow'
            elif e.event_ack_speed == EventAckSpeed.SLOW:
                return 'ArrowRightSlow'
            else:
                return 'ArrowRightNormal'


        event_label = self.event_type.name
        if type(self.ack_time) is float and EventAckSpeed.FAST != self.event_ack_speed:
            event_label += ' ('

            if self.ack_time > 1:
                unit = 's'
                val = '%0.1f %s'%(self.ack_time, unit)
            else:
                unit = 'ms'
                val = '%0.0f %s'%(self.ack_time*1e3, unit)

            if self.event_ack_speed != EventAckSpeed.NORMAL:
                event_label_ack_tspan = Tspan(val)
                event_label_ack_tspan.id = '%s-label-tspan-ack_time'%id_prefix
                if EventAckSpeed.VERY_SLOW == self.event_ack_speed:
                    event_label_ack_tspan.font_color = self.settings.ack_threshold_very_slow_color
                else:
                    event_label_ack_tspan.font_color = self.settings.ack_threshold_slow_color
                event_label += event_label_ack_tspan.to_svg()
            else:
                event_label += '%s'%(val)
            event_label += ')'


        def inject_capture_info(e):
            """ Tiny lambda to include some additional info about the event in
            the SVG.  This is done this way because I am still unsure of a good
            way to do this, so a lambda gives me flexibility. """

            return '''show_capture_info({{'time': new Date('{time}'), 'eventType': '{event_type}', 'frameId': {frame_id}, 'ackFrameId': {ack_frame_id}, 'ackTime': {ack_time}}})'''.format(
                    time=e.time,
                    event_type=e.event_type.name,
                    ack_time=e.ack_time,
                    frame_id=e.frame_id,
                    ack_frame_id=e.ack_frame_id,
                )

        event_label_tspan = Tspan('%s'%event_label)
        event_label_tspan.id = '{id}-label-tspan'.format(id=id_prefix)
        event_label_tspan.font_size = '2.5px'
        event_label_tspan.font_color = self.event_type.display_options.color
        event_label_tspan.on_click = inject_capture_info(self)

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
         xml:space="preserve">{event_label}</text>
    </g>'''.format(
            x_g=self.display_options.x, y_g=self.display_options.y,
            x_e=self.src.display_options.x - self.display_options.x + (self.src.display_options.width/2.0), y_e=0,
            x_a=0, y_a=0, a_len=a_len,
            x_l=label_pos, y_l=0,
            id=id_prefix,
            arrow_id=arrow_id(self),
            text_style=self.event_type.display_options.text_style(),
            event_color=self.event_type.display_options.color,
            event_label=event_label_tspan.to_svg(),
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

        page_height = int(self.events[len(self.events)-1].dt.total_seconds() * self.settings.time_spacing) + 40
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
