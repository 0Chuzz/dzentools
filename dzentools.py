#!/usr/bin/python
'''dzentools module
contains the core utilities to output information with dzen syntax. this
module does not mess with the OS as it cares only about syntax so it doesn't
need any external library. 
'''

import os.path

class DzenString(str):
    '''Dzen syntax aware string

    this subclass of string keep tracks of syntax elements and plain text, in
    order to avoid problems when nesting/blending many text chunks.
    '''
    def __new__(cls, *args):
        '''DzenString "costructor"
        accept one or more plaintext string, or 2-tuples representing a dzen
        entity. string creation is done here, as string are unmutable
        '''
        str_elements = []
        for elm in args:
            if isinstance(elm, tuple):
                str_elm = "^{0}({1})".format(*elm)
            else:
                str_elm = elm.replace("^", "^^")
            str_elements.append(str_elm)
        ret = str.__new__(cls, ''.join(str_elements))
        ret.elements = args
        return ret

    def __add__(self, other):
        if isinstance(other, DzenString):
            ret = self.elements + other.elements
        else:
            ret = self.elements + (other,)
        return DzenString(*ret)

    def __radd__(self, other):
        if isinstance(other, DzenString):
            ret = other.elements + self.elements
        else:
            ret = (other,) + self.elements
        return DzenString(*ret)


class ForegroundColour(object):
    def __init__(self, colour):
        self.colour = colour

    def __call__(self, my_string):
        if hasattr(my_string, "elements"):
            ret = [('fg', str(self.colour))]
            for elm in my_string.elements:
                if elm == ('fg', ''):
                    ret.append(('fg', str(self.colour)))
                else:
                    ret.append(elm)
            ret.append(('fg', ''))
            ret = tuple(ret)
        else:
            ret = (("fg", str(self.colour)), my_string, ("fg", ""))
        return DzenString(*ret)


class BarElement(object):
    DEFAULT_PARAMS = {}
    def __init__(self, params={}, size=None, scroll=0):
        self.size = size
        self.scroll = scroll
        self.scroll_cursor = 0
        self.last = None
        self.params = {}
        self.params.update(self.DEFAULT_PARAMS)
        self.params.update(params)
        self.start()

    def start(self):
        pass

    def update(self):
        pass

    def check_update(self):
        return True

    def next(self):
        if self.last and not self.check_update():
            ret = self.last
        else:
            try:
                ret = self.update()
            except StandardError as e:
                ret = repr(e)
        if not ret:
            raise StopIteration
        self.last = ret
        if self.size is None:
            pass
        elif len(ret) < self.size:
            ret = ret.rjust(self.size)
        elif len(ret) >= self.size:
            ret += ' | '
        if self.scroll:
            self.scroll_cursor %= len(ret)
            ret = ret[self.scroll_cursor:] + ret[:self.scroll_cursor]
            self.scroll_cursor += self.scroll
        ret = ret[:self.size]
        col = self.params.get('colour')
        if col:
            ret = "^fg(" + col.colour +")" + ret +"^fg()" #XXX 
        return ret

    def __iter__(self):
        return self


class Icon(object):
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)
        if not os.access(base_dir, os.R_OK):
            raise IOError("cannot access '{0.base_dir}' directory".format(self))

    def get_icon(self, icon_name):
        ipath = os.path.join(self.base_dir, icon_name)
        if not os.access(ipath, os.R_OK):
            raise IOError("cannot access icon")
        return DzenString(('i', ipath))

    def __getitem__(self, name):
        return self.get_icon(name)
