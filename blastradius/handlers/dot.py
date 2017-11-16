# standard libraries
import json
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
        self.clusters = ('root',)
        
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
                        self.edges.append(e)
                    elif 'node' in m.groupdict():
                        self.nodes.append(DotNode(d['node'], fmt=fmt))
                    break
        
        # terraform graph output doesn't always make explicit node declarations;
        # sometimes they're a side-effect of edge definitions. Capture them.
        for e in self.edges:
            if e.source not in [ n.label for n in self.nodes ]:
                self.nodes.append(DotNode(e.source))
            if e.target not in [ n.label for n in self.nodes ]:
                self.nodes.append(DotNode(e.target))

        self.stack('var')
        self.stack('output')

        for n in self.nodes:
            n.fmt.add(id=n.svg_id, shape='box')

        for e in self.edges:
            e.fmt.add(id=e.svg_id)

        # leftover nodes belong to the root subgraph.
        for n in self.nodes:
            n.cluster = 'root' if not n.cluster else n.cluster

    def stack(self, node_type, threshold=2):
        '''if a group of nodes of type 'type' number as many as 'threshold', 
        and share the same (single) parent and (single) child, then
        hide their dependencies, and create a chain of pseudo-dependencies 
        so that they stack one above the next in the final diagram.'''
        for n in self.nodes:
            if n.type != node_type:
                continue

            parents  = [ e for e in self.edges if e.target == n.label ]
            children = [ e for e in self.edges if e.source == n.label ]

            if len(children) > 1 or len(parents) != 1:
                continue

            # setup the cluster.
            target = children[0].target if len(children) > 0 else ''
            n.cluster = 'cluster' + parents[0].source + '_' + node_type + '_' + target
            self.clusters = self.clusters + (n.cluster,)

        for cluster in [ cluster for cluster in self.clusters if re.match('.*_' +  node_type + '_.*', cluster) ]:
            nodes     = [ n for n in self.nodes if n.cluster == cluster ]
            prev      = None
            last_edge = None

            if len(nodes) == 1:
                continue

            for n in nodes:

                # 1st iteration.
                if not prev: 
                    for e in self.edges:
                        if e.source == n.label:
                            e.edge_type = EdgeType.HIDDEN

                # subsequent iterations.
                else:
                    last_edge = None
                    for e in self.edges:
                        if e.target == n.label:
                            e.edge_type = EdgeType.HIDDEN
                        if e.source == n.label:
                            e.edge_type = EdgeType.HIDDEN
                            last_edge = e
                    self.edges.append(DotEdge(prev.label, n.label, fmt=Format('style=dashed,arrowhead=none'), edge_type=EdgeType.LAYOUT_SHOWN))
                    #print('\tsource: ' + prev.label)
                    #print('\ttarget: ' + n.label)
                    #print('\tsvg_id: ' + self.edges[-1].svg_id)
                    #print('')
                    #print('') 
                # each iteration.
                prev = n
            
            if last_edge:
                last_edge.edge_type = EdgeType.NORMAL

    def dot(self):
        'returns a dot/graphviz representation of the graph (a string)'
        return self.dot_template.render({ 'nodes': self.nodes, 'edges': self.edges, 'clusters' : self.clusters, 'EdgeType' : EdgeType })

    def json(self):
        edges = [ dict(e) for e in self.edges ]
        nodes = [ dict(n) for n in self.nodes ]
        return json.dumps({ 'nodes' : nodes, 'edges' : edges }, indent=4, sort_keys=True)
    
    dot_template_str = """
digraph {
    compound = "true"

    graph [fontname = "courier new",fontsize=8];
    node [fontname = "courier new",fontsize=8];
    edge [fontname = "courier new",fontsize=8];
    {% for cluster in clusters %}
        subgraph "{{cluster}}" {
            style=invis;
            {% for node in nodes %}
                {% if node.cluster == cluster %}
                    {% if node.type %}
                    "{{node.label}}" [ shape=none, margin=0, id={{node.svg_id}} label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
                            <TR><TD>{{node.type}}</TD></TR>
                            <TR><TD>{{node.resource_name}}</TD></TR>
                        </TABLE>>];
                    {% else %}
                        "{{node.label}}" [{{node.fmt}}]
                    {% endif %}
                {% endif %}
            {% endfor %}
        }
    {% endfor %}
        {% for edge in edges %}
            {% if edge.edge_type == EdgeType.NORMAL %}"{{edge.source}}" -> "{{edge.target}}" {% if edge.fmt %} [{{edge.fmt}}] {% endif %}{% endif %}
            {% if edge.edge_type == EdgeType.LAYOUT_SHOWN %}"{{edge.source}}" -> "{{edge.target}}" {% if edge.fmt %} [{{edge.fmt}}] {% endif %}{% endif %}
            {% if edge.edge_type == EdgeType.LAYOUT_HIDDEN %}"{{edge.source}}" -> "{{edge.target}}" [style="invis"]{% endif %}
        {% endfor %}
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
        self.cluster        = None # for graphviz groupings.

    def __iter__(self):
        for key in {'label', 'simple_name', 'type', 'resource_name', 'group', 'svg_id', 'definition', 'cluster'}:
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

class EdgeType:
    '''Sometimes we want to hide edges, and sometimes we want to add edges in order
    to influence layout. '''
    NORMAL        = 1 # what we talk about when we're talking about edges.
    HIDDEN        = 2 # these are normal edges, but aren't drawn.
    LAYOUT_SHOWN  = 3 # these edges are drawn, but aren't "real" edges
    LAYOUT_HIDDEN = 4 # these edges are not drawn, aren't "real" edges, but inform layout.

    def __init__(self):
        pass


class DotEdge(Edge):

    def __init__(self, source, target, fmt=None, edge_type=EdgeType.NORMAL):
        self.source = source
        self.target = target
        self.svg_id = 'edge_' + str(Edge.svg_id_counter())
        self.fmt    = fmt
        self.edge_type = edge_type

    def __iter__(self):
        for key in {'source', 'target', 'svg_id', 'edge_type'}: 
            yield (key, getattr(self, key))


