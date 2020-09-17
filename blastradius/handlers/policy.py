import json
import os.path
from os import path

class Policy():
    def __init__(self,filename=None):
        self.resource_policy_info = []
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
            for index, var in enumerate(data["resources"]):
                temp_data = dict()
                temp_data = var
                self.resource_policy_info.append(temp_data)

        else:
            self.resource_policy_info.append("not available")
        
    
    def json(self):
        my_policy_json = json.dumps(self.resource_policy_info,indent=4, sort_keys=True)
        return my_policy_json 
        