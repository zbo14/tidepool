from functools import wraps

def unexpected_type(name, exp, val):
    if isinstance(exp, tuple):
        exp = ' '.join(['%s or' % x for x in exp[:-1]]) + '%s' % exp[-1]
    raise TypeError('expected "%s" to be %s, got %s' % (name, exp, type(val)))

def has_valid_type(argname, argtypes, val):
    for argtype in argtypes:
        if isinstance(val, argtype):
            return
    unexpected_type(argname, val)

## from https://stackoverflow.com/a/15577293 ##

def argtypes(**decls):

    def decorator(f):
        code = f.__code__
        names = code.co_varnames[:code.co_argcount]

        @wraps(f)
        def decorated(*args, **kwargs):
            for argname, argtypes in decls.items():
                try:
                    val = args[names.index(argname)]
                except (IndexError, ValueError):
                    val = kwargs.get(argname)
                if argtypes == callable:
                    if not callable(val):
                        unexpected_type(argname, 'function', val)
                elif isinstance(argtypes, tuple):
                    has_valid_type(argname, argtypes, val)
                elif not isinstance(val, argtypes):
                    unexpected_type(argname, argtypes, val)
            return f(*args, **kwargs)
        return decorated
    return decorator

################################################