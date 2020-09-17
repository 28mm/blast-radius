# standard libraries
import os
import subprocess
import itertools
import json
import re

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
    if not which('terraform') and not which('terraform.exe'):
        return render_template('error.html')
    elif not which('dot') and not which('dot.exe'):
        return render_template('error.html')
    elif not os.path.exists('.terraform'):
        return render_template('error.html')
    else:
        return render_template('index.html', help=get_help())

@app.route('/graph.svg')
def graph_svg():
    Graph.reset_counters()
    dot = DotGraph('','', file_contents=run_tf_graph())

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus      = request.args.get('refocus', default=None, type=str)

    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth)

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)

    return dot.svg()


@app.route('/graphnew.svg')
def graphnew_svg():
    Graph.reset_counters()
    dot = DotGraph('ext','',file_contents=run_tf_graph())

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus      = request.args.get('refocus', default=None, type=str)

    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth)

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)

    return dot.svg()

@app.route('/graphsimple.svg')
def graphsimple_svg():
    Graph.reset_counters()
    dot = DotGraph('ext','',file_contents=simple_graph())

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus      = request.args.get('refocus', default=None, type=str)

    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth)

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)

    return dot.svg()


def simple_graph():
    file_contents=run_tf_graph()
    new_file_content = ''
    for line in file_contents.splitlines():
        if re.search("var",line) or re.search("provider",line) or re.search("meta.count-boundary",line) or re.search("output",line):
            if re.search("meta.count-boundary",line) and not (re.search("output",line) or re.search("var",line) or re.search('\[root\] root',line)):
                new_line = line.replace("meta.count-boundary (EachMode fixup)","root")
                new_file_content+=new_line +'\n'
        else:
            new_file_content+=line +'\n'
    
    
    return new_file_content


@app.route('/graph.json')
def graph_json():
    Graph.reset_counters()
    dot = DotGraph('','',file_contents=run_tf_graph())
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
        raise Exception('Execution error', completed.stderr)
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