# standard libraries
from glob import iglob
import io
import os
import re
import json

# 3rd party libraries
# hcl2json convert hcl to json
import subprocess
from pkg_resources import resource_filename

class Terraform:
    """Finds terraform/hcl files (*.tf) in CWD or a supplied directory, parses
    them with pyhcl, and exposes the configuration via self.config."""

    def __init__(self, directory=None, settings=None):
        self.settings = settings if settings else {}
        # handle the root module first...
        self.directory = directory if directory else os.getcwd()
        self.config_str:str = ''
        iterator = iglob( self.directory + '/*.tf')
        data = {}
        
        for fname in iterator:
            out=subprocess.getoutput(["hcl2json {}".format(fname)])
            file_data = json.loads(out)
            for key in file_data:
                if not key in data.keys():
                    data.update(file_data)
                else:
                    for k,v in file_data[key].items():
                        data[key][k]=v
        
        self.config = data

        # then any submodules it may contain, skipping any remote modules for
        # the time being.
        self.modules = {}
        if 'module' in self.config:
            for name, mod in self.config['module'].items():
                if 'source' not in mod:
                    continue
                source = mod['source']
                # '//' used to refer to a subdirectory in a git repo
                if re.match(r'.*\/\/.*', source):
                    continue
                # '@' should only appear in ssh urls
                elif re.match(r'.*\@.*', source):
                    continue
                # 'github.com' special behavior.
                elif re.match(r'github\.com.*', source):
                    continue
                # points to new TFE module registry
                elif re.match(r'app\.terraform\.io', source):
                    continue
                # bitbucket public and private repos
                elif re.match(r'bitbucket\.org.*', source):
                    continue
                # git::https or git::ssh sources
                elif re.match(r'^git::', source):
                    continue
                # git:// sources
                elif re.match(r'^git:\/\/', source):
                    continue
                # Generic Mercurial repos
                elif re.match(r'^hg::', source):
                    continue
                # Public Terraform Module Registry
                elif re.match(r'^[a-zA-Z0-9\-_]+\/[a-zA-Z0-9\-_]+\/[a-zA-Z0-9\-_]+', source):
                    continue
                # AWS S3 buckets
                elif re.match(r's3.*\.amazonaws\.com', source):
                    continue
                # fixme path join. eek.
                self.modules[name] = Terraform(directory=self.directory+'/'+source, settings=mod)

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