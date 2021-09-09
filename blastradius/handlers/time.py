from __future__ import print_function

from os import path
import json


class Time():
    def __init__(self,filename=None):
        self.resource_time_info = []
        if filename == None:
            if(path.exists("time.json")):
                with open("time.json", 'r') as f:
                    data = json.load(f)
            else:
                data = ""
        else:
            with open(filename, 'r') as f:
                data = json.load(f)
        
        if (data) :
            temp_data = dict()
            for (index, var) in data.items():
                temp_data[index] = var

            self.resource_time_info.append(data)

        else:
            self.resource_time_info.append("not available")

    
    def json(self):
        my_time_json = json.dumps(self.resource_time_info,indent=4, sort_keys=True)
        return my_time_json 