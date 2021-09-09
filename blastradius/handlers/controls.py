import json
import os.path
from os import path

class Controls():
    def __init__(self,filename=None):
        self.resource_controls_info = []
        if filename == None:
            if(path.exists("policy.json")):
                with open("policy.json", 'r') as f:
                    data = json.load(f)
            else:
                data = ""
        else:
            with open(filename, 'r') as f:
                data = json.load(f)
        
        if (data) :
            for _, var in enumerate(data["resources"]):
                temp_data = dict()
                temp_data = var
                self.resource_controls_info.append(temp_data)

        else:
            self.resource_controls_info.append("not available")
        
    
    def json(self):
        controls_json = json.dumps(self.resource_controls_info,indent=4, sort_keys=True)
        return controls_json 