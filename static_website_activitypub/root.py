from __future__ import absolute_import, print_function
import cherrypy
from well_known import WellKnown
from actors import Actors
    
class Root(object):
    """The root website implementation"""
    def __init__(self, args, conf):
        # Preinitialise handlers for our endpoints
        self.well_known = WellKnown(args, conf)
        self.actors_endpoint = args.actors_endpoint[1:]
        self.actors = Actors(args, conf, self.actors_endpoint)
        
    def _cp_dispatch(self, vpath):
        if len(vpath) >= 1:
            if vpath[0] == '.well-known':
                return self.well_known
            elif vpath[0] == self.actors_endpoint:
                return self.actors
        return vpath
