#Allow print function to work in Python 2
from __future__ import print_function

# standard libraries
import json
import re
import subprocess
from collections import OrderedDict
from collections import deque

# 3rd party libraries 
import jinja2

# 1st party libraries
from blastradius.graph import Graph, Node, Edge
from blastradius.util import OrderedSet

class DotGraph(Graph):

    def __init__(self, filename, file_contents=None):
        self.filename = filename
        self.nodes    = []
        self.edges    = []
        self.clusters = OrderedDict()
        self.clusters['root'] = True # Used like an ordered Set.
        
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

        # leftover nodes belong to the root subgraph.
        for n in self.nodes:
            n.cluster = 'root' if not n.cluster else n.cluster

    def get_node_by_name(self, label):
        '''return node by label (if exists) otherwise simple_name'''
        for n in self.nodes:
            if n.label == label:
                return n

        for n in self.nodes:
            if n.simple_name == label:
                return n
        
        return None

    #
    # Output functions (return strings).
    #

    def dot(self):
        'returns a dot/graphviz representation of the graph (a string)'
        return self.dot_template.render({ 'nodes': self.nodes, 'edges': self.edges, 'clusters' : self.clusters, 'EdgeType' : EdgeType })

    def json(self):
        edges = [ dict(e) for e in self.edges ]
        nodes = [ dict(n) for n in self.nodes ]
        return json.dumps({ 'nodes' : nodes, 'edges' : edges }, indent=4, sort_keys=True)

    #
    # A handful of graph manipulations. These are hampered by the decision 
    # to not de-serialize the graphs (leaving them as lists of nodes and
    # edges). This code is garbage, but it mostly works.
    #

    def stack(self, node_type, threshold=2):
        '''if a group of nodes of type 'type' number as many as 'threshold', 
        and share the same (single) parent and (single) child, then
        hide their dependencies, and create a chain of pseudo-dependencies 
        so that they stack one above the next in the final diagram.'''
        new_edges = []

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
            self.clusters[n.cluster] = True # <-- OrderedDict, used for its ordering. Pretend its a Set

        for cluster in [ cluster for cluster in self.clusters.keys() if re.match('.*_' +  node_type + '_.*', cluster) ]:
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
                    new_edges.append(DotEdge(prev.label, n.label, fmt=Format('style=dashed,arrowhead=none'), edge_type=EdgeType.LAYOUT_SHOWN))

                # each iteration.
                prev = n
            
            if last_edge:
                last_edge.edge_type = EdgeType.NORMAL

        self.edges = self.edges + new_edges

    def set_module_depth(self, depth):
        """
        Group resources below the requested module depth into stand-in nodes.
        """

        depth += 1 # account for [root] module

        def is_too_deep(modules):
            return len(modules) >= depth and modules[0] != 'root'

        def find_edge(edges, e):
            for edge in edges:
                if e.source == edge.source and e.target == edge.target and e.edge_type == edge.edge_type:
                    return True
            return False

        def find_placeholder(modules):
            for placeholder in placeholders:
                if placeholder.is_standin(modules):
                    return placeholder
            return None
        
        # find DotNodes at too great a depth.
        too_deep     = [ n for n in self.nodes if is_too_deep(n.modules) ]

        # generate ModuleNodes to stand-in for DotNodes at too great a depth.
        placeholders = []
        for n in too_deep:
            match = False
            for p in placeholders:
                if p.is_standin(n.modules):
                    match = True
                    break
            if match == False:
                placeholders.append(ModuleNode(n.modules[:depth]))

        # Replace endpoints below the requested depth with their stand-in node.
        # Edges within the same collapsed module become self-edges and disappear,
        # while dependencies between different collapsed modules are preserved.
        new_edges = []
        for e in self.edges:
            src_mods = DotNode._label_to_modules(e.source)
            tgt_mods = DotNode._label_to_modules(e.target)

            source = e.source
            target = e.target

            if is_too_deep(src_mods):
                source = find_placeholder(src_mods).label
            if is_too_deep(tgt_mods):
                target = find_placeholder(tgt_mods).label

            if source == target:
                continue

            if source == e.source and target == e.target:
                new_edges.append(e)
            else:
                new_edges.append(DotEdge(source, target, fmt=e.fmt, edge_type=e.edge_type))

        # make sure we haven't got any duplicate edges.
        final_edges = []
        for e in new_edges:
            if not find_edge(final_edges, e):
                final_edges.append(e)
        self.edges = final_edges

        # add placeholder nodes, remove nodes beyond specified module_depth.
        self.nodes = list(OrderedSet(placeholders) | (OrderedSet(self.nodes) - OrderedSet(too_deep)))
    

    def center(self, node):
        '''
        prunes graph to include only (1) the given node, (2) its 
        dependencies, and nodes that depend on it.
        '''
        edges_by_source = {}
        for e in self.edges:
            if e.source in edges_by_source:
                edges_by_source[e.source].append(e)
            else:
                edges_by_source[e.source] = [ e ]

        edges_by_target = {}
        for e in self.edges: 
            if e.target in edges_by_target:
                edges_by_target[e.target].append(e)
            else:
                edges_by_target[e.target] = [ e ]

        edges_to_save = OrderedSet() # edge objects
        nodes_to_save = OrderedSet([node.label]) # label strings

        q = deque([node.label])
        visited = set()
        while q:
            source = q.popleft()
            if source in visited:
                continue
            visited.add(source)
            for e in edges_by_source.get(source, []):
                edges_to_save.add(e)
                nodes_to_save.add(e.target)
                if e.target not in visited:
                    q.append(e.target)

        q = deque([node.label])
        visited = set()
        while q:
            target = q.popleft()
            if target in visited:
                continue
            visited.add(target)
            for e in edges_by_target.get(target, []):
                edges_to_save.add(e)
                nodes_to_save.add(e.source)
                if e.source not in visited:
                    q.append(e.source)

        self.edges = list(edges_to_save)
        self.nodes = [ n for n in self.nodes if n.label in nodes_to_save ]

    def focus(self, node):
        '''
        prunes graph to include only the given node and its dependencies.
        '''
        edges_by_source = {}
        for e in self.edges:
            if e.source in edges_by_source:
                edges_by_source[e.source].append(e)
            else:
                edges_by_source[e.source] = [ e ]

        edges_to_save = OrderedSet() # edge objects
        nodes_to_save = OrderedSet([node.label]) # label strings

        q = deque([node.label])
        visited = set()
        while q:
            source = q.popleft()
            if source in visited:
                continue
            visited.add(source)
            for e in edges_by_source.get(source, []):
                edges_to_save.add(e)
                nodes_to_save.add(e.target)
                if e.target not in visited:
                    q.append(e.target)

        self.edges = list(edges_to_save)
        self.nodes = [ n for n in self.nodes if n.label in nodes_to_save ]


    
    #
    # Formatting templates.
    #

    dot_template_str = """
digraph {
    compound = "true"
    graph [fontname = "courier new",fontsize=8];
    node [fontname = "courier new",fontsize=8];
    edge [fontname = "courier new",fontsize=8];

    {# just the root module #}
    {% for cluster in clusters %}
        subgraph "{{cluster}}" {
            style=invis;
            {% for node in nodes %}
                {% if node.cluster == cluster and node.module == 'root' %}
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

    {# non-root modules #}
    {% for node in nodes %}
        {% if node.module != 'root' %}

            {% if node.collapsed %}
                "{{node.label}}" [ shape=none, margin=0, id={{node.svg_id}} label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
                {% for module in node.modules %}<TR><TD>(M) {{module}}</TD></TR>{% endfor %}
                <TR><TD>(collapsed)</TD></TR>
                <TR><TD>...</TD></TR>
               </TABLE>>];
            {% else %}
            "{{node.label}}" [ shape=none, margin=0, id={{node.svg_id}} label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
                {% for module in node.modules %}<TR><TD>(M) {{module}}</TD></TR>{% endfor %}
                <TR><TD>{{node.type}}</TD></TR>
                <TR><TD>{{node.resource_name}}</TD></TR>
                </TABLE>>];
            {% endif %}
        {% endif %}

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

        self.label          = DotNode._label_fixup(label)
        self.fmt            = fmt if fmt else Format('') # graphviz formatting.
        self.simple_name    = re.sub(r'\[root\]\s+', '', self.label) # strip root module notation.
        self.type           = DotNode._resource_type(self.label) # e.g. var, aws_instance, output...
        self.resource_name  = DotNode._resource_name(self.label) #
        self.svg_id         = 'node_' + str(Node.svg_id_counter()) #
        self.definition     = {} # 
        self.group          = 20000 # for coloration. placeholder. replaced in javascript.
        self.module         = DotNode._module(self.label) # for module groupings. 'root' or 'module.foo.module.bar'
        self.cluster        = None # for stacked resources (usually var/output).
        self.collapsed      = False

        self.fmt.add(id=self.svg_id, shape='box')

        self.modules = DotNode._label_to_modules(self.label)

    def __iter__(self):
        for key in {'label', 'simple_name', 'type', 'resource_name', 'group', 'svg_id', 'definition', 'cluster', 'module', 'modules'}:
           yield (key, getattr(self, key))

    #
    # static utilities mostly for converting "labels"--which uniquely identify
    # DotNodes--to other useful things like a list of parent modules, the isolated
    # resource name, the resource type, etc.
    #

    @staticmethod
    def _label_fixup(label):
        # fix the resources belonging to removed modules by naming them "removed."
        return re.sub(r'\s+\(removed\)', r'.removed (removed)', label)

    @staticmethod
    def _resource_type(label):
        m = re.match(r'(\[root\]\s+)*((?P<modprefix>\S+)\.)*(?P<type>\S+)\.\S+', label)
        return m.groupdict()['type'] if m else ''

    @staticmethod
    def _resource_name(label):
        m = re.match(r'(\[root\]\s+)*(?P<type>\S+)\.(?P<name>\S+)', label)
        return m.groupdict()['name'] if m else ''

    @staticmethod
    def _module_names(label):
        address = re.sub(r'^\[root\]\s+', '', label).split(maxsplit=1)[0]
        remaining = address
        modules = []
        module_re = re.compile(r'^module\.([^.\s\[]+(?:\[[^\]]+\])?)(?:\.|$)')

        while remaining:
            match = module_re.match(remaining)
            if not match:
                break
            modules.append(match.group(1))
            remaining = remaining[match.end():]

        return modules

    @staticmethod
    def _module(label):
        modules = DotNode._module_names(label)
        if not modules:
            return 'root'
        return 'module.' + '.module.'.join(modules)

    @staticmethod
    def _label_to_modules(label):
        modules = DotNode._module_names(label)
        return modules if modules else ['root']


class ModuleNode(DotNode):
    '''
    Stands in for multiple DotNodes at the same module depth...
    '''
    def __init__(self, modules):
        label = '[root] ' + 'module.' + '.module.'.join(modules) + '.collapsed.etc'
        super().__init__(label, fmt=Format(''))
        self.collapsed      = True

    def is_standin(self, modules):
        'should this ModuleNode standin for the provided DotNode?'
        if len(modules) < len(self.modules):
            return False
        for i in range(len(self.modules)):
            if self.modules[i] != modules[i]:
                return False
        return True


class EdgeType:
    '''
    Sometimes we want to hide edges, and sometimes we want to add 
    edges in order to influence layout.
    '''
    NORMAL        = 1 # what we talk about when we're talking about edges.
    HIDDEN        = 2 # these are normal edges, but aren't drawn.
    LAYOUT_SHOWN  = 3 # these edges are drawn, but aren't "real" edges
    LAYOUT_HIDDEN = 4 # these edges are not drawn, aren't "real" edges, but inform layout.

    def __init__(self):
        pass


class DotEdge(Edge):
    '''
    Distinguished from a Regular Edge, by its Dot language format string.
    '''
    def __init__(self, source, target, fmt=None, edge_type=EdgeType.NORMAL):
        self.source = DotNode._label_fixup(source)
        self.target = DotNode._label_fixup(target)
        self.svg_id = 'edge_' + str(Edge.svg_id_counter())
        self.fmt    = fmt
        self.edge_type = edge_type

        self.fmt.add(id=self.svg_id)

    def __iter__(self):
        for key in {'source', 'target', 'svg_id', 'edge_type'}: 
            yield (key, getattr(self, key))
