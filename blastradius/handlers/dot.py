# standard libraries
import json
import itertools
import re
import subprocess

# 3rd party libraries 
import jinja2

# 1st party libraries
from blastradius.graph import Graph, Node, Edge

class DotGraph(Graph):

    def __init__(self, filename, file_contents=None):
        self.filename = filename
        self.nodes    = []
        self.edges    = []
        
        if file_contents:
            self.contents = file_contents
        else:
            with open(filename, 'r') as f:
                self.contents = f.read()

        # pretty naive way to put a parser together, considering graphviz/dot have a
        # bnf grammar. but gets the job done, for now.
        edge_fmt_re = re.compile(r'\s+\"(?P<src>.*)\"\s+\-\>(?P<dst>.*)\s+\[(?P<fmt>.*)\]')
        edge_re = re.compile(r'\s+\"(?P<src>.*)\"\s+\-\>\s+\"(?P<dst>.*)\"')
        decl_re = re.compile(r'\s+\"(?P<node>.*)\"\s+\[(?P<fmt>.*)\]')

        # read node and edge declarations from an existing graphviz/dot file.
        for l in self.contents.splitlines():
            for pat in [edge_fmt_re, edge_re, decl_re]:
                m = pat.match(l)
                if m:
                    d = m.groupdict()
                    fmt = Format(d['fmt']) if 'fmt' in d else Format('')
                    if 'src' in m.groupdict():
                        e = DotEdge(d['src'], d['dst'], fmt=fmt)
                        e.fmt.add(id=e.svg_id)
                        self.edges.append(e)
                    elif 'node' in m.groupdict():
                        self.nodes.append(DotNode(d['node'], fmt=fmt))
                    break
        
        # terraform graph output doesn't always make implicit node declarations;
        # sometimes they're a side-effect of edge definitions. Capture them.
        for e in self.edges:
            if e.source not in [ n.label for n in self.nodes ]:
                self.nodes.append(DotNode(e.source))
            if e.target not in [ n.label for n in self.nodes ]:
                self.nodes.append(DotNode(e.target))

    def json(self):
        edges = [ dict(e) for e in self.edges ]
        nodes = [ dict(n) for n in self.nodes ]
        #nodes = [ { **dict(n), 'def' : terraform.definition(n.label, terraform)} for n in self.nodes ]
        return json.dumps({ 'nodes' : nodes, 'edges' : edges }, indent=4)
    
    dot_template_str = """
digraph {
    compound = "true"
    newrank = "true"
    graph [fontname = "courier new",fontsize=8];
    node [fontname = "courier new",fontsize=8];
    edge [fontname = "courier new",fontsize=8];
    subgraph "root" {
        {% for node in nodes %}
        {% if node.type %}
           "{{node.label}}" [ shape=none, margin=0, id={{node.svg_id}} label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
                <TR><TD>{{node.type}}</TD></TR>
                <TR><TD>{{node.resource_name}}</TD></TR>
            </TABLE>>];
        {% else %}
            "{{node.label}}" [{{node.fmt}}]
        {% endif %}
        {% endfor %}
        {% for edge in edges %}
            "{{edge.source}}" -> "{{edge.target}}" {% if edge.fmt %} [{{edge.fmt}}] {% endif %}
        {% endfor %}
    }
}
"""
    dot_template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(dot_template_str)
        

class Format:
    """
    Naive parser for graphviz/dot formatting options. 
    TBD: method to add/replace format options, rather than exposing self.fmt
    """

    def __init__(self, s):
        self.fmt = {}
        
        if len(s) > 0:

            # doesn't handle '=' or ','  within keys/values, and includes quotation
            # marks, rather than stripping them... but sufficient for a subset of dotfiles
            # produced by terraform, hopefully.
            param_re = re.compile(r'\s*(?P<key>.*)\s*\=(?P<val>.*)')
            params = s.split(',')
            for p in params:
                m = param_re.match(p)
                if m:
                    self.fmt[m.groupdict()['key']] = m.groupdict()['val']
                else:
                    print('Error processing format param: ' + 'p', file=sys.stderr)

    def add(self, **kwargs):
        self.fmt = {**self.fmt, **kwargs}
    
    def remove(self, key):
        if key in self.fmt:
            del self.fmt[key]

    def __str__(self):
        return ','.join([ key + '=' + val for key, val in self.fmt.items() ])

class DotNode(Node):

    def __init__(self, label, fmt=None):
        self.label          = label
        self.fmt            = fmt if fmt else Format('')
        self.simple_name    = re.sub(r'\[root\]\s+', '', label)
        self.type           = DotNode._resource_type(label)
        self.resource_name  = DotNode._resource_name(label)
        self.group          = 20000 # placeholder.
        self.svg_id         = 'node_' + str(Node.svg_id_counter())
        self.definition     = {}

    def __iter__(self):
        for key in {'label', 'simple_name', 'type', 'resource_name', 'group', 'svg_id', 'definition'}:
           yield (key, getattr(self, key))

    @staticmethod
    def _resource_type(name):
        # strip [root] if this is a top-level thing.
        full_name = re.sub(r'\[root\]\s+', '', name)
        m = re.match(r'(?P<type>\S+)\.\S+', full_name)
        if m:
            return m.groupdict()['type']
        else:
            return ''

    @staticmethod
    def _resource_name(name):
        # strip [root] if this is a top-level thing.
        full_name = re.sub(r'\[root\]\s+', '', name)
        m = re.match(r'(?P<type>\S+)\.(?P<name>\S+)', full_name)
        if m:
            return m.groupdict()['name']
        else:
            return ''


class DotEdge(Edge):

    def __init__(self, source, target, fmt=None):
        self.source = source
        self.target = target
        self.svg_id = 'edge_' + str(self.svg_id_counter())
        self.fmt    = fmt

    def __iter__(self):
        for key in {'source', 'target', 'svg_id'}: 
            yield (key, getattr(self, key))