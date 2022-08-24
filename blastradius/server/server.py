#Allow print function to work in Python 2
from __future__ import print_function

# standard libraries
from asyncio import run
import os
import glob
import subprocess
import itertools
import json

# 3rd-party libraries
from flask import Flask, render_template, request, flash, redirect, jsonify, send_file
import jinja2

# 1st-party libraries
from blastradius.handlers.dot import DotGraph, Format, DotNode
from blastradius.handlers.terraform import Terraform
from blastradius.util import which
from blastradius.graph import Node, Edge, Counter, Graph

app = Flask(__name__)


@app.route('/')
def index():
    is_terraform_installation = True
    is_terraform_directory = True
    tf_data_dir = os.getenv('TF_DATA_DIR') #Might remove later, not sure what to do with it yet

    # we need terraform, graphviz, and an init-ed terraform project.
    if not which('terraform') and not which('terraform.exe'):
        is_terraform_installation = False
    if not os.path.exists('.terraform'):
        if not (tf_data_dir is not None and os.path.exists(tf_data_dir)):
            is_terraform_directory = False
    if not which('dot') and not which('dot.exe'):
        #Return error page. Graphviz is a dependency that has to exist.
        return render_template('error.html', tf_dir=is_terraform_directory, gviz_install=False,
                               tf_install=is_terraform_installation)

    if tf_data_dir is not None and os.path.exists(tf_data_dir):
        folder_name = os.path.basename(os.path.dirname(tf_data_dir))
    else:
        folder_name = os.path.basename(os.path.dirname(os.getcwd()))

    if is_terraform_directory is False or is_terraform_installation is False:
        # Blast Radius template without default graph
        print("Blast Radius could not find a Terraform directory ") if is_terraform_directory is False else print("Blast Radius could not find a Terraform installation. ")
        template = 'non_tf_dir.html'
    else:
        # Blast Radius template with default graph
        print("Blast Radius is generating graphs for your Terraform directory. ")
        template = 'index.html'

    #Run Blast Radius presenting a default graph
    return render_template(template, help=get_help(), folder_name=folder_name)


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file submitted')
        return redirect("/")
    file = request.files['file']

    filecontent = file.read().decode("utf-8")

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus = request.args.get('refocus', default=None, type=str)

    dot = initalizeDotGraph(content=filecontent,
                            module_depth=module_depth, refocus=refocus)

    resp = {"SVG": dot.svg(), "JSON": dot.json()}
    return jsonify(resp)


@app.route('/input', methods=['POST'])
def input():
    if 'input' not in request.form:
        flash('No input submitted')
        return redirect("/")
    dot_input = request.form['input']

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus = request.args.get('refocus', default=None, type=str)

    dot = initalizeDotGraph(content=dot_input,
                            module_depth=module_depth, refocus=refocus)

    resp = {"SVG": dot.svg(), "JSON": dot.json()}
    return jsonify(resp)


# @app.route('/convert/<filetype>', methods=['POST'])
# def convert(filetype):
#     removeExistingFiles()
#
#     if 'file' not in request.files:
#         flash('No file was submitted for conversion')
#         return redirect("/")
#
#     filecontent = request.files['file'].read().decode("utf-8")
#     file = None
#
#     if filetype == "pdf":
#         file = './converter.pdf'
#         svg2pdf(file_obj=filecontent, write_to=file)
#     elif filetype == "ps":
#         file = './converter.ps'
#         svg2png(file_obj=filecontent, write_to=file)
#     elif filetype == "png":
#         file = './converter.png'
#         svg2ps(file_obj=filecontent, write_to=file)
#     else:
#         flash('Only PDF, PNG, PS files are supported for download')
#         return redirect("/")
#
#     return send_file(file)


@app.route('/error')
def error():
    return render_template('error.html', tf_dir="Not sure", gviz_install="Not sure", tf_install="Not sure")


@app.route('/graph.svg')
def graph_svg():
    Graph.reset_counters()

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus = request.args.get('refocus', default=None, type=str)

    dot = initalizeDotGraph(content=run_tf_graph(),
                            module_depth=module_depth, refocus=refocus)

    # dot = DotGraph('', file_contents=test_content_tfproj)

    # module_depth = request.args.get('module_depth', default=None, type=int)
    # refocus      = request.args.get('refocus', default=None, type=str)

    # if module_depth is not None and module_depth >= 0:
    #     dot.set_module_depth(module_depth)

    # if refocus is not None:
    #     node = dot.get_node_by_name(refocus)
    #     if node:
    #         dot.center(node)
    return dot.svg()


@app.route('/graph.json')
def graph_json():
    Graph.reset_counters()

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus = request.args.get('refocus', default=None, type=str)

    dot = initalizeDotGraph(content=run_tf_graph(),
                            module_depth=module_depth, refocus=refocus)

    # dot = DotGraph('', file_contents=run_tf_graph())
    # module_depth = request.args.get('module_depth', default=None, type=int)
    # refocus      = request.args.get('refocus', default=None, type=str)
    # if module_depth is not None and module_depth >= 0:
    #     dot.set_module_depth(module_depth)

    # tf = Terraform(os.getcwd())
    # for node in dot.nodes:
    #     node.definition = tf.get_def(node)

    # if refocus is not None:
    #     node = dot.get_node_by_name(refocus)
    #     if node:
    #         dot.center(node)

    return dot.json()


# @app.route('/fupload/<filename>')
# def uploadFile(filename):
#     path = os.path.join(os.getcwd(), filename)
#     if not os.path.exists(path):
#         return "File/filepath "
#     with open(path) as f:
#         contents = f.read()

#     Graph.reset_counters()

#     module_depth = request.args.get('module_depth', default=None, type=int)
#     refocus = request.args.get('refocus', default=None, type=str)

#     dot = initalizeDotGraph(content=contents,
#                             module_depth=module_depth, refocus=refocus)

#     return dot.svg()


def run_tf_graph():
    completed = subprocess.run(['terraform', 'graph'], stdout=subprocess.PIPE)
    if completed.returncode != 0:
        raise
    return completed.stdout.decode('utf-8')


def initalizeDotGraph(content, module_depth, refocus):
    dot = DotGraph('', file_contents=content)

    # module_depth = request.args.get('module_depth', default=None, type=int)
    # refocus      = request.args.get('refocus', default=None, type=str)

    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth)

    tf = Terraform(os.getcwd())
    for node in dot.nodes:
        node.definition = tf.get_def(node)

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)

    return dot


def removeExistingFiles():
    for filename in glob.glob(os.path.join(os.getcwd(), "converter*")):
        os.remove(filename)


def get_help():
    return {'tf_version': get_terraform_version(),
            'tf_exe': get_terraform_exe(),
            'cwd': os.getcwd(),
            'python_version': get_python_version()}


def get_terraform_version():
    completed = subprocess.run(
        ['terraform', '--version'], stdout=subprocess.PIPE)
    if completed.returncode != 0:
        raise
    return completed.stdout.decode('utf-8').splitlines()[0].split(' ')[-1]


def get_terraform_exe():
    return which('terraform')


def get_python_version():
    completed = subprocess.run(
        ['python', '--version'], stdout=subprocess.PIPE)
    if completed.returncode != 0:
        raise
    return completed.stdout.decode('utf-8').splitlines()[0].split(' ')[-1]
