from __future__ import print_function
import json
import sys
import graphviz
import jinja2
import json

class Plan():
    def __init__(self,filename=None):
        self.resource_info = []
        #create json reading from tfplan.json file
        with open("tfplan.json", 'r') as f:
            data = json.load(f)
        for index, var in enumerate(data["planned_values"]["root_module"]["resources"]):
            temp_data = dict()
            temp_data = var
            for attribute, variable in enumerate(data["resource_changes"]):
                if temp_data["address"] == variable["address"]:
                    temp_data["change"] = variable["change"]
            self.resource_info.append(temp_data)
    
    def json(self):
        my_json_string = json.dumps(self.resource_info,indent=4, sort_keys=True)
        return my_json_string 