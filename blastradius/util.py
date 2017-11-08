import re
import os

class Re:
    '''A bit of a hack to simplify conditionals with 
    multiple regexes. e.g. 
    
    if (match = re.match(pattern, ...)) { 
        match.groupdict(...)[key]
    }
    
    isn't possible, so instead:

    r = Re()
    if r.match(pattern1, string):
        r.last_match.groupdict()[key] ...
    elif r.match(pattern1, string)
        r.last_match.groupdict()[key] ...
    '''
    def __init__(self):
        self.last_match = None

    def match(self,pattern,text):
        self.last_match = re.match(pattern,text)
        return self.last_match

    def search(self,pattern,text):
        self.last_match = re.search(pattern,text)
        return self.last_match

def to_seconds(string):
    '''Parse Terraform time interval into an integer representing seconds.'''
    m = re.match(r'(?P<hours>\d*h)*(?P<minutes>)\d*m)*(?P<seconds>\d*s)*', string)
    if not m:
        return TypeError
    d = m.groupdict()

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

