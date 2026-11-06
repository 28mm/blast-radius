#Allow print function to work in Python 2
from __future__ import print_function

# standard libraries
from asyncio import run
import os
import glob
import subprocess
import itertools
import json
import platform

# 3rd-party libraries
from flask import Flask, render_template, request, flash, redirect, jsonify, send_file
import jinja2

# 1st-party libraries
from blastradius.handlers.dot import DotGraph, Format, DotNode
from blastradius.handlers.terraform import Terraform
from blastradius.util import which
from blastradius.graph import Node, Edge, Counter, Graph

app = Flask(__name__)
MAX_DOT_BYTES = 2 * 1024 * 1024


@app.route('/')
def index():
    is_terraform_installation = True
    is_terraform_directory = True
    tf_data_dir = os.getenv('TF_DATA_DIR') #Might remove later, not sure what to do with it yet

    # we need terraform, graphviz, and an init-ed terraform project.
    if not which('terraform') and not which('terraform.exe'):
        is_terraform_installation = False
    if not os.path.exists('.terraform') and not (tf_data_dir is not None and os.path.exists(tf_data_dir)):
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
        return graph_error(
            400,
            'missing_dot',
            'Submit a Graphviz DOT file in the "file" field.',
        )
    file = request.files['file']

    filecontent = file.read().decode("utf-8")

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus = request.args.get('refocus', default=None, type=str)

    try:
        dot, _warnings = render_dot_graph(
            content=filecontent,
            module_depth=module_depth,
            refocus=refocus,
        )
    except ValueError as error:
        return graph_error(422, 'invalid_graph', str(error))

    resp = {"SVG": dot.svg(), "JSON": dot.json()}
    return jsonify(resp)


@app.route('/input', methods=['POST'])
def input():
    if 'input' not in request.form:
        return graph_error(
            400,
            'missing_dot',
            'Submit Graphviz DOT text in the "input" field.',
        )
    dot_input = request.form['input']

    module_depth = request.args.get('module_depth', default=None, type=int)
    refocus = request.args.get('refocus', default=None, type=str)

    try:
        dot, _warnings = render_dot_graph(
            content=dot_input,
            module_depth=module_depth,
            refocus=refocus,
        )
    except ValueError as error:
        return graph_error(422, 'invalid_graph', str(error))

    resp = {"SVG": dot.svg(), "JSON": dot.json()}
    return jsonify(resp)


@app.route('/api/graphs/render', methods=['POST'])
def render_graph():
    if request.content_length and request.content_length > MAX_DOT_BYTES:
        return graph_error(
            413,
            'payload_too_large',
            'The DOT document exceeds the 2 MiB request limit.',
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return graph_error(
            400,
            'invalid_request',
            'Send a JSON object containing a "dot" string.',
        )

    dot_input = payload.get('dot')
    if not isinstance(dot_input, str) or not dot_input.strip():
        return graph_error(
            400,
            'missing_dot',
            'The "dot" field must be a non-empty string.',
        )
    if len(dot_input.encode('utf-8')) > MAX_DOT_BYTES:
        return graph_error(
            413,
            'payload_too_large',
            'The DOT document exceeds the 2 MiB request limit.',
        )

    module_depth = payload.get('module_depth')
    if (
        module_depth is not None
        and (
            isinstance(module_depth, bool)
            or not isinstance(module_depth, int)
            or module_depth < 0
        )
    ):
        return graph_error(
            400,
            'invalid_module_depth',
            '"module_depth" must be a non-negative integer.',
        )

    refocus = payload.get('refocus')
    if refocus is not None and not isinstance(refocus, str):
        return graph_error(
            400,
            'invalid_refocus',
            '"refocus" must be a node label string.',
        )

    Graph.reset_counters()
    try:
        dot, warnings = render_dot_graph(
            content=dot_input,
            module_depth=module_depth,
            refocus=refocus,
        )
        svg = dot.svg()
    except (OSError, RuntimeError, ValueError) as error:
        return graph_error(422, 'invalid_graph', str(error))

    return jsonify(
        {
            'svg': svg,
            'graph': json.loads(dot.json()),
            'warnings': warnings,
        }
    )


def graph_error(status, code, message):
    return jsonify({'error': {'code': code, 'message': message}}), status


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
    completed = subprocess.run(['terraform', 'graph'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise Exception('Execution error', completed.stderr)
    return completed.stdout.decode('utf-8')


def render_dot_graph(content, module_depth=None, refocus=None):
    dot = DotGraph('', file_contents=content)
    if not dot.nodes and not dot.edges:
        raise ValueError(
            'No Graphviz node or edge declarations were found in the DOT document.'
        )

    if module_depth is not None and module_depth >= 0:
        dot.set_module_depth(module_depth)

    warnings = []
    try:
        tf = Terraform(os.getcwd())
        for node in dot.nodes:
            node.definition = tf.get_def(node)
    except (OSError, RuntimeError) as error:
        warnings.append(
            'Terraform definitions were unavailable: {}'.format(error)
        )

    if refocus is not None:
        node = dot.get_node_by_name(refocus)
        if node:
            dot.center(node)
        else:
            warnings.append(
                'The requested refocus node was not found; the full graph was rendered.'
            )

    return dot, warnings


def initalizeDotGraph(content, module_depth=None, refocus=None):
    dot, _warnings = render_dot_graph(
        content=content,
        module_depth=module_depth,
        refocus=refocus,
    )

    return dot


def removeExistingFiles():
    for filename in glob.glob(os.path.join(os.getcwd(), "converter*")):
        os.remove(filename)


def get_help():
    terraform_executable = get_terraform_exe()
    return {'tf_version': get_terraform_version(terraform_executable),
            'tf_exe': terraform_executable or 'Not installed',
            'cwd': os.getcwd(),
            'python_version': get_python_version()}


def get_terraform_version(executable=None):
    if executable is None:
        return 'Not installed'

    try:
        completed = subprocess.run(
            [executable, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        return 'Unavailable'

    if completed.returncode != 0:
        return 'Unavailable'

    lines = completed.stdout.decode('utf-8', errors='replace').splitlines()
    if not lines:
        return 'Unavailable'
    return lines[0].split(' ')[-1]


def get_terraform_exe():
    return which('terraform') or which('terraform.exe')


def get_python_version():
    return platform.python_version()
