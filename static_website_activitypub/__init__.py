from .cmd import main, version
__version__ = version
def invoke_main(*args):
    return next(main(*args), None)
    