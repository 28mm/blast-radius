# standard libraries
from glob import iglob
import io
import os
import re

# 3rd party libraries
import hcl2 as hcl    # hashicorp configuration language (.tf)

class Terraform:
    """Finds terraform/hcl files (*.tf) in CWD or a supplied directory, parses
    them with hcl2, and exposes the configuration via self.config."""

    def __init__(self, directory=None, settings=None):
        self.settings = settings if settings else {}

        # handle the root module first...
        self.directory = directory if directory else os.getcwd()
        #print(self.directory)

        self.config = {}
        iterator = iglob( self.directory + '/*.tf')
        for fname in iterator:
            with open(fname, 'r', encoding='utf-8') as f:
                try:
                    raw = io.StringIO(f.read())
                    parsed = hcl.load(raw)
                    self.config.update(parsed)
                except Exception as e:
                    raise RuntimeError('Exception occurred while parsing ' + fname) from e


        # then any submodules it may contain
        self.modules = {}
        if 'module' in self.config:
            for name, mod in [(k, v) for x in self.config['module'] for (k, v) in x.items()]:
                if 'source' not in mod:
                    continue
                source = mod['source'][0]

                path = os.path.join(self.directory, source)
                if os.path.exists(path):
                    # local module
                    self.modules[name] = Terraform(directory=path, settings=mod)
                else:
                    # remote module
                    # Since terraform must be init'd before use, we can
                    # assume remote modules have been downloaded to .terraform/modules
                    path = os.path.join(os.getcwd(), '.terraform', 'modules', name)

                    # Get the subdir if any
                    match = re.match(r'.*(\/\/.*)(?!:)', source)
                    if re.match(r'.*\/(\/.*)(?!:)', source):
                        path = os.path.join(path, match.groups()[0])

                    self.modules = Terraform(directory=path, settings=mod)




    def get_def(self, node, module_depth=0):

        # FIXME 'data' resources (incorrectly) handled as modules, necessitating
        # the try/except block here.
        if len(node.modules) > module_depth and node.modules[0] != 'root':
            try:
                tf = self.modules[ node.modules[module_depth] ]
                return tf.get_def(node, module_depth=module_depth+1)
            except:
                return ''

        try:
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
        except:
            return ''
