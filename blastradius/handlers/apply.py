# standard libraries
import re
import json

# 1st party libraries
from blastradius.graph import Graph, Node, Edge
from blastradius.handlers.dot import DotNode
from blastradius.util import Re

class Apply(Graph):
    def __init__(self, filename):
        self.filename = filename
        self.contents = ''
        self.nodes    = [] # we can populate this, 
        self.edges    = [] # but not this!

        ansi_escape = re.compile(r'\x1b[^m]*m')
        with open(filename, 'r') as f:
            self.contents = ansi_escape.sub('', f.read())

        # example output:
        #
        # aws_vpc.default: Creation complete after 4s (ID: vpc-024f7a64)
        # ...
        # aws_key_pair.auth: Creating...
        #   fingerprint: "" => "<computed>"
        #   key_name:    "" => "default-key"
        #   ...
        # aws_instance.web: Still creating... (10s elapsed)
        # aws_instance.web: Still creating... (20s elapsed)
        # aws_instance.web (remote-exec): Connecting to remote host via SSH...
        # aws_instance.web (remote-exec):   Host: 1.2.3.4
        # aws_instance.web (remote-exec):   User: ubuntu
        # ...

        node_begin_re =r'(?P<name>\S+)\:\s+Creating...'
        node_compl_re = r'(?P<name>\S+)\:\s+Creation\s+complete\s+after\s+(?P<duration>\S+)\s+'
        node_still_re = r'(?P<name>\S+)\:\s+Still\s+creating\.\.\.\s+\((?P<duration>\S+)\s+'

        for line in self.contents.splitlines():

            r = Re()
            if r.match(node_begin_re, line):
                



                    break




        print(self.contents)


