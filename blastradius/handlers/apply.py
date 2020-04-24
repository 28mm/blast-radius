from __future__ import print_function
import json
import sys
import graphviz
import jinja2
import json
import subprocess
import os.path
from os import path

class Apply():
    def __init__(self,filename=None):
        self.apply_resource_info = []
        #create json for apply
        #reading from state file
        if filename == None:
            if(path.exists("terraform.tfstate")):
                with open("terraform.tfstate", 'r') as f:
                    data = json.load(f)
            else:
                data = ""
        else:
            with open(filename, 'r') as f:
                data = json.load(f)
        
        if (data) :
            for index, var in enumerate(data["resources"]):
                temp_data = dict()
                temp_data = var
                self.apply_resource_info.append(temp_data)

        else:
            self.apply_resource_info.append("not applied")

    def json(self):
        my_json_string = json.dumps(self.apply_resource_info,indent=4, sort_keys=True)
        return my_json_string 