"""Command-line interface for Blast Radius."""

import argparse
import os
import sys

from blastradius.handlers.dot import DotGraph
from blastradius.handlers.terraform import Terraform
from blastradius.server.server import app


def build_parser():
    parser = argparse.ArgumentParser(
        description="blast-radius: Interactive Terraform Graph Visualizations"
    )
    parser.add_argument(
        "directory",
        type=str,
        help="terraform configuration directory",
        default=os.getcwd(),
        nargs="?",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="specify an IP to bind to other than the default 0.0.0.0",
        default=os.getenv("BLAST_RADIUS_HOST", "0.0.0.0"),
    )
    parser.add_argument(
        "--port",
        type=int,
        help="specify a port other than the default 5000",
        default=os.getenv("BLAST_RADIUS_PORT", "5000"),
    )

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="print a JSON representation of the Terraform graph",
    )
    output_group.add_argument(
        "--dot",
        action="store_true",
        help="print the Graphviz DOT representation of the Terraform graph",
    )
    output_group.add_argument(
        "--svg",
        action="store_true",
        help="print the SVG representation of the Terraform graph",
    )
    output_group.add_argument(
        "--serve",
        action="store_true",
        help="start a web server with an interactive Terraform graph",
    )

    parser.add_argument(
        "--graph",
        type=str,
        help="`terraform graph` output (defaults to stdin)",
        default=sys.stdin,
    )

    constraint_group = parser.add_mutually_exclusive_group()
    constraint_group.add_argument(
        "--module-depth", type=int, help="hide module details"
    )
    constraint_group.add_argument("--focus", type=str)
    constraint_group.add_argument("--center", type=str)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.serve:
        os.chdir(args.directory)
        app.run(host=args.host, port=args.port)
        return

    if not (args.json or args.dot or args.svg):
        parser.print_help()
        return

    if args.graph is sys.stdin:
        dot = DotGraph("", file_contents=sys.stdin.read())
    else:
        dot = DotGraph(args.graph)

    if args.module_depth is not None:
        if args.module_depth < 0:
            parser.error("--module-depth must be zero or greater")
        dot.set_module_depth(args.module_depth)

    if args.center:
        center_node = dot.get_node_by_name(args.center)
        if not center_node:
            parser.error("the requested --center node was not found")
        dot.center(center_node)

    if args.focus:
        focus_node = dot.get_node_by_name(args.focus)
        if not focus_node:
            parser.error("the requested --focus node was not found")
        dot.focus(focus_node)

    if args.json:
        terraform = Terraform(args.directory)
        for node in dot.nodes:
            node.definition = terraform.get_def(node)
        print(dot.json())
    elif args.dot:
        print(dot.dot())
    elif args.svg:
        print(dot.svg())


if __name__ == "__main__":
    main()
