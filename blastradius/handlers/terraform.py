# standard libraries
from glob import iglob
import io

# 3rd party libraries 
import hcl    # hashicorp configuration language (.tf)

class Terraform:
    """Finds terraform/hcl files (*.tf) in CWD or a supplied directory, parses
    them with pyhcl, and exposes the configuration via self.config."""

    def __init__(self, directory=None):
        config_str = ''
        iterator = iglob( directory + '/*.tf') if directory else iglob('*.tf')
        for fname in iterator:
            with open(fname, 'r', encoding='utf-8') as f:
                config_str += f.read() + ' '
        config_io = io.StringIO(config_str)

        self.config = hcl.load(config_io)

    def get_def(self, node):

        # non resource types
        types = { 'var'  : lambda x: self.config['variable'][x.resource_name],
          'provider'     : lambda x: self.config['provider'][x.resource_name],
          'output'       : lambda x: self.config['output'][x.resource_name],
          'data'         : lambda x: self.config['data'][x.resource_name],
          'meta'         : lambda x: '',
          'provisioner'  : lambda x: '',
          ''             : lambda x: '' }
        if node.type in types:
            return types[node.type](node)

        # resources are a little different _many_ possible types,
        # nested within the 'resource' field. 
        else:
            return self.config['resource'][node.type][node.resource_name]