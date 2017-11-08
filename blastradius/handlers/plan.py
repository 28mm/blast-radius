# standard libraries
import re
import json

# 1st party libraries
from blastradius.graph import Graph, Node, Edge
from blastradius.handlers.dot import DotNode

class Plan(Graph):
    def __init__(self, filename):
        self.filename = filename
        self.contents = ''
        self.nodes    = [] # we can populate this, 
        self.edges    = [] # but not this!

        ansi_escape = re.compile(r'\x1b[^m]*m')
        with open(filename, 'r') as f:
            self.contents = ansi_escape.sub('', f.read())

        node_re = re.compile(r'\s+(?P<action>(\+|\-))\s+(?P<name>\S+)')
        attr_re = re.compile(r'\s+(?P<key>\S+)\:\s+(?P<value>.*)')

        action     = None
        name       = None
        definition = {}
        for line in self.contents.splitlines():
            for p in [ node_re, attr_re ]:
                m = p.match(line)
                if m:
                    d = m.groupdict()
                    if 'action' in d:
                        if action:
                            self.nodes.append(PlanNode(action, name, definition))                            
                        action = d['action']
                        name   = d['name']
                        definition = {}
                    elif 'key' in d:
                        definition[d['key']] = d['value']
                    break

        print(json.dumps([ dict(n) for n in self.nodes], indent=4))

class PlanNode(Node):
    def __init__(self, action, name, definition):
        self.action      = action
        self.simple_name = name
        self.definition  = definition
        self.type        = DotNode._resource_type(self.simple_name)
        self.resource_name = DotNode._resource_name(self.simple_name)
        self.svg_id        = 'node_' + str(Node.svg_id_counter())

    def __iter__(self):
        for key in ['action', 'simple_name', 'definition', 'type', 'resource_name', 'svg_id']:
            yield (key, getattr(self, key))
