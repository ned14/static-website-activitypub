from __future__ import absolute_import, print_function
import cherrypy

class WellKnown(object):
    """Implements the /.well-known REST endpoint used to query user account info"""
    def __init__(self, args, conf):
       # We only have one user, so pregenerate it
       self.cached_user = 'acct:' + args.user_account + '@' + args.user_domain
       self.cached_response = {
           'subject' : self.cached_user,
           'links' : [
               {
                   'rel': 'self',
                   'type': 'application/activity+json',
                   'href': args.user_actor_href
               }
           ]
       }
       # Update the conf to be given to cherrypy
       conf['/.well-known'] = {
           'tools.staticdir.on' : False,
           'tools.encode.on' : True,
           'tools.encode.encoding' : 'utf-8',
           'tools.response_headers.on': True,
           'tools.response_headers.headers': [('Content-Type', 'application/jrd+json')],
        }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def webfinger(self, resource):
        if resource == self.cached_user:
            return self.cached_response
        raise cherrypy.HTTPError(404, 'Resource not found')