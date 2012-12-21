# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Utilities and wrappers around inspect module"""

import inspect, re

# Local imports:
from spyderlib.utils import encoding

SYMBOLS = r"[^\'\"a-zA-Z0-9_.]"

def getobj(txt, last=False):
    """Return the last valid object name in string"""
    txt_end = ""
    for startchar, endchar in ["[]", "()"]:
        if txt.endswith(endchar):
            pos = txt.rfind(startchar)
            if pos:
                txt_end = txt[pos:]
                txt = txt[:pos]
    tokens = re.split(SYMBOLS, txt)
    token = None
    try:
        while token is None or re.match(SYMBOLS, token):
            token = tokens.pop()
        if token.endswith('.'):
            token = token[:-1]
        if token.startswith('.'):
            # Invalid object name
            return None
        if last:
            #XXX: remove this statement as well as the "last" argument
            token += txt[ txt.rfind(token) + len(token) ]
        token += txt_end
        if token:
            return token
    except IndexError:
        return None
    
def getobjdir(obj):
    """
    For standard objects, will simply return dir(obj)
    In special cases (e.g. WrapITK package), will return only string elements
    of result returned by dir(obj)
    """
    return [item for item in dir(obj) if isinstance(item, basestring)]

def getdoc(obj):
    """Return text documentation generated by pydoc.TextDoc.docroutine"""
    doc = inspect.getdoc(obj) or inspect.getcomments(obj) or ''
    doc = unicode(doc)
    text = {'title': '', 'argspec': '', 'note': '', 'doc': doc}
    
    if callable(obj):
        try:
            name = obj.__name__
        except AttributeError:
            text['doc'] = doc
            return text
        if inspect.ismethod(obj):
            imclass = obj.im_class
            if obj.im_self is not None:
                text['note'] = 'Method of %s instance' \
                               % obj.im_self.__class__.__name__
            else:
                text['note'] = 'Unbound %s method' % imclass.__name__
            obj = obj.im_func
        elif hasattr(obj, '__module__'):
            text['note'] = 'Function of %s module' % obj.__module__
        else:
            text['note'] = 'Function'
        text['title'] = obj.__name__
        if inspect.isfunction(obj):
            args, varargs, varkw, defaults = inspect.getargspec(obj)
            text['argspec'] = inspect.formatargspec(args, varargs, varkw,
                                                    defaults,
                                              formatvalue=lambda o:'='+repr(o))
            if name == '<lambda>':
                text['title'] = name + ' lambda '
                text['argspec'] = text['argspec'][1:-1] # remove parentheses
        else:
            # Try to extract the argspec from the first docstring line
            doclines = text['doc'].split("\n")
            first_line = doclines[0].strip()
            argspec = getsignaturesfromtext(first_line, '')
            if argspec:
                text['argspec'] = argspec[0]
                
                # Eliminate the first docstring line if we found the argspec
                doc_st = text['doc'].find('\n') + 2
                text['doc'] = text['doc'][doc_st:]
            else:
                text['argspec'] = '(...)'
        
    return text

def getsource(obj):
    """Wrapper around inspect.getsource"""
    try:
        try:
            src = encoding.to_unicode( inspect.getsource(obj) )
        except TypeError:
            if hasattr(obj, '__class__'):
                src = encoding.to_unicode( inspect.getsource(obj.__class__) )
            else:
                # Bindings like VTK or ITK require this case
                src = getdoc(obj)
        return src
    except (TypeError, IOError):
        return

def getsignaturesfromtext(text, objname):
    """Get object signatures from text (object documentation)
    Return a list containing a single string in most cases
    Example of multiple signatures: PyQt4 objects"""
    return re.findall(objname+r'\([^\)]+\)', text)

def getargsfromtext(text, objname):
    """Get arguments from text (object documentation)"""
    signatures = getsignaturesfromtext(text, objname)
    if signatures:
        signature = signatures[0]
        argtxt = signature[signature.find('(')+1:-1]
        return argtxt.split(',')

def getargsfromdoc(obj):
    """Get arguments from object doc"""
    if obj.__doc__ is not None:
        return getargsfromtext(obj.__doc__, obj.__name__)

def getargs(obj):
    """Get the names and default values of a function's arguments"""
    if inspect.isfunction(obj) or inspect.isbuiltin(obj):
        func_obj = obj
    elif inspect.ismethod(obj):
        func_obj = obj.im_func
    elif inspect.isclass(obj) and hasattr(obj, '__init__'):
        func_obj = getattr(obj, '__init__')
    else:
        return []
    if not hasattr(func_obj, 'func_code'):
        # Builtin: try to extract info from doc
        args = getargsfromdoc(func_obj)
        if args is not None:
            return args
        else:
            # Example: PyQt4
            return getargsfromdoc(obj)
    args, _, _ = inspect.getargs(func_obj.func_code)
    if not args:
        return getargsfromdoc(obj)
    
    # Supporting tuple arguments in def statement:
    for i_arg, arg in enumerate(args):
        if isinstance(arg, list):
            args[i_arg] = "(%s)" % ", ".join(arg)
            
    defaults = func_obj.func_defaults
    if defaults is not None:
        for index, default in enumerate(defaults):
            args[index+len(args)-len(defaults)] += '='+repr(default)
    if inspect.isclass(obj) or inspect.ismethod(obj):
        if len(args) == 1:
            return None
        if 'self' in args:
            args.remove('self')
    return args

def getargtxt(obj, one_arg_per_line=True):
    """
    Get the names and default values of a function's arguments
    Return list with separators (', ') formatted for calltips
    """
    args = getargs(obj)
    if args:
        sep = ', '
        textlist = None
        for i_arg, arg in enumerate(args):
            if textlist is None:
                textlist = ['']
            textlist[-1] += arg
            if i_arg < len(args)-1:
                textlist[-1] += sep
                if len(textlist[-1]) >= 32 or one_arg_per_line:
                    textlist.append('')
        if inspect.isclass(obj) or inspect.ismethod(obj):
            if len(textlist) == 1:
                return None
            if 'self'+sep in textlist:
                textlist.remove('self'+sep)
        return textlist


def isdefined(obj, force_import=False, namespace=None):
    """Return True if object is defined in namespace
    If namespace is None --> namespace = locals()"""
    if namespace is None:
        namespace = locals()
    attr_list = obj.split('.')
    base = attr_list.pop(0)
    if len(base) == 0:
        return False
    import __builtin__
    if base not in __builtin__.__dict__ and base not in namespace:
        if force_import:
            try:
                module = __import__(base, globals(), namespace)
                if base not in globals():
                    globals()[base] = module
                namespace[base] = module
            except (ImportError, SyntaxError):
                return False
        else:
            return False
    for attr in attr_list:
        try:
            attr_not_found = not hasattr(eval(base, namespace), attr)
        except SyntaxError:
            return False
        if attr_not_found:
            if force_import:
                try:
                    __import__(base+'.'+attr, globals(), namespace)
                except (ImportError, SyntaxError):
                    return False
            else:
                return False
        base += '.'+attr
    return True
    

if __name__ == "__main__":
    class Test(object):
        def method(self, x, y=2, (u, v, w)=(None, 0, 0)):
            pass
    print getargtxt(Test.__init__)
    print getargtxt(Test.method)
    print isdefined('numpy.take', force_import=True)
    print isdefined('__import__')
    print isdefined('.keys', force_import=True)
    print getobj('globals')
    print getobj('globals().keys')
    print getobj('+scipy.signal.')
    print getobj('4.')
    print getdoc(sorted)
    print getargtxt(sorted)
