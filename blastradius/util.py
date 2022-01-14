import re
import os
import collections.abc

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

class Counter:

    def __init__(self, start=-1):
        self.count = start

    def next(self):
        self.count += 1
        return self.count

class OrderedSet(collections.abc.MutableSet):
    '''ordered set implementation linked from StackOverflow
    http://code.activestate.com/recipes/576694/
    https://stackoverflow.com/questions/1653970/does-python-have-an-ordered-set'''

    def __init__(self, iterable=None):
        self.end = end = [] 
        end += [None, end, end]
        self.map = {}
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:        
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

def which(file_name):
    for path in os.environ["PATH"].split(os.pathsep):
        full_path = os.path.join(path, file_name)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None
