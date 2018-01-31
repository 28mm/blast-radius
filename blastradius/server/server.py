# standard libraries
import os
import subprocess
import itertools
import json

# 3rd-party libraries
from flask import Flask
from flask import render_template
from flask import request
import jinja2

# 1st-party libraries
from blastradius.handlers.dot import DotGraph, Format, DotNode
from blastradius.handlers.terraform import Terraform
from blastradius.util import which
from blastradius.graph import Node, Edge, Counter, Graph

app = Flask(__name__)

@app.route('/')
def index():
    # we need terraform, graphviz, and an init-ed terraform project.
    if not which('terraform') or not which('dot') or not os.path.exists('.terraform'):
        return render_template('error.html')

    return render_template('index.html', help=get_help())

@app.route('/graph.svg')
def graph_svg():
    Graph.reset_counters()
    dot = DotGraph('', file_contents=run_tf_graph())

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus      = request.args.get('refocus', default=None, type=str)

    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth)

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)

    return dot.svg()


@app.route('/graph.json')
def graph_json():
    Graph.reset_counters()
    dot = DotGraph('', file_contents=run_tf_graph())
    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus      = request.args.get('refocus', default=None, type=str)
    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth) 

    tf = Terraform(os.getcwd())
    for node in dot.nodes:
        node.definition = tf.get_def(node)

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)

    return dot.json()

def run_tf_graph():
    completed = subprocess.run(['terraform', 'graph'], stdout=subprocess.PIPE)
    if completed.returncode != 0:
        raise
    return completed.stdout.decode('utf-8')

def get_help():
    return { 'tf_version' : get_terraform_version(),
             'tf_exe'   : get_terraform_exe(),
             'cwd'        : os.getcwd() }

def get_terraform_version():
    completed = subprocess.run(['terraform', '--version'], stdout=subprocess.PIPE)
    if completed.returncode != 0:
        raise
    return completed.stdout.decode('utf-8').splitlines()[0].split(' ')[-1]
    
def get_terraform_exe():
    return which('terraform')





