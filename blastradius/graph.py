# standard libraries
from abc import ABC, abstractmethod
import itertools
import subprocess
from io import StringIO

# 3rd party libraries 
import jinja2

class Graph:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def __iter__(self):
        for key in {'nodes', 'edges'}:
            yield (key, getattr(self, key))

    def dot(self):
        'returns a dot/graphviz representation of the graph (a string)'
        return self.dot_template.render({ 'nodes': self.nodes, 'edges': self.edges })

    def svg(self):
        'returns an svg representation of the graph (via graphviz/dot)'
        dot_str = self.dot()
        completed = subprocess.run(['dot', '-Tsvg'], input=dot_str.encode('utf-8'), stdout=subprocess.PIPE)
        if completed.returncode != 0:
            raise
        return completed.stdout.decode('utf-8')

    def json(self):
        'returns a json representation of the graph (a string)'
        return json.dumps({ 'nodes' : dict(nodes), 'edges' : dict(edges) }, indent=4, sort=True)

    dot_template_str = """
digraph {
    compound = "true"
    newrank = "true"
    graph [fontname = "courier new",fontsize=8];
    node [fontname = "courier new",fontsize=8];
    edge [fontname = "courier new",fontsize=8];
    subgraph "root" {
        {% for node in nodes %}
            "{{node.label}}" {% if node.fmt %} [{{node.fmt}}] {% endif %}
        {% endfor %}
        {% for edge in edges %}
            "{{edge.source}}" -> "{{edge.target}}" {% if edge.fmt %} [{{edge.fmt}}] {% endif %}
        {% endfor %}
    }
}
"""
    dot_template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(dot_template_str)

class Edge:

    # we need unique ids for each edge, for SVG output,
    # svg_id_counter provides this facility.
    svg_id_counter = itertools.count().__next__

    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.svg_id = 'edge_' + str(self.svg_id_counter())

    def __iter__(self):
        for key in {'source', 'target'}: 
            yield (key, getattr(self, key))


class Node(ABC):

    # we need unique ids for each node, for SVG output,
    # svg_id_counter provides this facility.
    svg_id_counter = itertools.count().__next__

    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError
