# standard libraries
import os
import subprocess
import itertools

# 3rd-party libraries
from flask import Flask
from flask import render_template
import jinja2

# 1st-party libraries
from blastradius.handlers.dot import DotGraph, Format, DotNode
from blastradius.handlers.terraform import Terraform
from blastradius.util import which
from blastradius.graph import Node, Edge, Counter

app = Flask(__name__)

@app.route('/')
def index():
    # we need terraform, graphviz, and an init-ed terraform project.
    if not which('terraform') or not which('dot') or not os.path.exists('.terraform'):
        return render_template('error.html')

    return render_template('index.html', directory=os.getcwd())

@app.route('/graph.svg')
def graph_svg():
    Node.reset_counter()
    Edge.reset_counter() # FIXME: NO!

    dot = DotGraph('', file_contents=run_tf_graph())
    return dot.svg()


@app.route('/graph.json')
def graph_json():
    Node.reset_counter() # FIXME: NO!
    Edge.reset_counter() # FIXME: NO!

    dot = DotGraph('', file_contents=run_tf_graph())

    tf = Terraform(os.getcwd())
    for node in dot.nodes:
        node.definition = tf.get_def(node)

    return dot.json()

def run_tf_graph():
    completed = subprocess.run(['terraform', 'graph'], stdout=subprocess.PIPE)
    if completed.returncode != 0:
        raise
    return completed.stdout.decode('utf-8')
