#!/usr/bin/env python3

from __future__ import print_function

from aenum import Enum


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

def get_template():
    """ Version 0 of this module held the template in a data file, but this
    required an additional command line argument on each invokation.  The
    version 1 goal is to have the SVG almost entirely generated without the
    need for a template like this.  For now however, the template is returned
    by this function """

    return '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   id="svg8"
   version="1.1"
   viewBox="0 0 {{page_width}} {{page_height}}"
   width="{{page_width}}mm"
   height="{{page_height}}mm">
  <script type="text/javascript">
// <![CDATA[
    function show_capture_info(e)
    {
        window.alert(JSON.stringify(e));
    }

    function show_host_info(desc)
    {
        window.alert(desc);
    }
// ]]>
  </script>
  <defs
     id="defs2">
    <marker
       inkscape:isstock="true"
       style="overflow:visible;"
       id="ArrowRightNormal"
       refX="0.0"
       refY="0.0"
       orient="auto"
       inkscape:stockid="Arrow2MendR">
      <path
         transform="scale(0.6) rotate(180) translate(0,0)"
         d="M 8.7185878,4.0337352 L -2.2072895,0.016013256 L 8.7185884,-4.0017078 C 6.9730900,-1.6296469 6.9831476,1.6157441 8.7185878,4.0337352 z "
         style="stroke-linejoin:round;stroke-opacity:1;fill-rule:evenodd;fill-opacity:1;stroke:#506b83;stroke-width:0.625;fill:#506b83"
         id="path6573" />
    </marker>
    <marker
       inkscape:isstock="true"
       style="overflow:visible;"
       id="ArrowRightSlow"
       refX="0.0"
       refY="0.0"
       orient="auto"
       inkscape:stockid="Arrow2MendX">
      <path
         transform="scale(0.6) rotate(180) translate(0,0)"
         d="M 8.7185878,4.0337352 L -2.2072895,0.016013256 L 8.7185884,-4.0017078 C 6.9730900,-1.6296469 6.9831476,1.6157441 8.7185878,4.0337352 z "
         style="stroke-linejoin:round;stroke-opacity:1;fill-rule:evenodd;fill-opacity:1;stroke:#c87137;stroke-width:0.625;fill:#c87137"
         id="path8002" />
    </marker>
    <marker
       inkscape:stockid="Arrow2Mend"
       orient="auto"
       refY="0.0"
       refX="0.0"
       id="ArrowRightVerySlow"
       style="overflow:visible;"
       inkscape:isstock="true">
      <path
         id="path6326"
         style="fill-rule:evenodd;stroke-width:0.625;stroke-linejoin:round;stroke:#ff0000;stroke-opacity:1;fill:#ff0000;fill-opacity:1"
         d="M 8.7185878,4.0337352 L -2.2072895,0.016013256 L 8.7185884,-4.0017078 C 6.9730900,-1.6296469 6.9831476,1.6157441 8.7185878,4.0337352 z "
         transform="scale(0.6) rotate(180) translate(0,0)" />
    </marker>
  </defs>
  <metadata
     id="metadata5">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g inkscape:label="Hosts" inkscape:groupmode="layer" id="layer-hosts">
     {{hosts}}
  </g>
  <g inkscape:label="Events" inkscape:groupmode="layer" id="layer-timeline" transform="translate({{time-left}},{{time-top}})">
    {{events}}
  </g>
</svg>'''

# vim: sw=4 ts=4 sts=0 expandtab ft=python ffs=unix :
