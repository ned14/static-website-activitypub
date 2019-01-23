from __future__ import absolute_import, print_function
import cherrypy

# From https://www.w3.org/TR/activitypub/:
#
# - You can POST to someone's inbox to send them a message (server-to-server / federation only... this is federation!)
# - You can GET from your inbox to read your latest messages (client-to-server; this is like reading your social network stream)
# - You can POST to your outbox to send messages to the world (client-to-server)
# - You can GET from someone's outbox to see what messages they've posted (or at least the ones you're authorized to see). (client-to-server and/or server-to-server)
#
# So we only care about implementing:
#   - POST outbox, so you can add new posts to your website
#     - Create https://www.w3.org/TR/activitystreams-vocabulary/#dfn-create
#     - Delete https://www.w3.org/TR/activitystreams-vocabulary/#dfn-delete
#     - Update https://www.w3.org/TR/activitystreams-vocabulary/#dfn-update
#   - GET  outbox, which returns all posts on your website
#
# We implement GET inbox only to return no posts without error
#
# We implement POST inbox to return failure, as we don't support
# others posting comments to our posts.

class Actors(object):
    """Implements the /actors REST endpoint used to query user specifics"""
    def __init__(self, args, conf, actors_endpoint):
        self.user_account = args.user_account
        self.actors_endpoint = actors_endpoint
        # We only have one user, so pregenerate it
        self.cached_response = {
            '@context' : [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1"
            ],
            'id' : args.user_actor_href,
            'type' : 'Person',
            'preferredUsername' : args.user_account,
            'inbox' : args.user_actor_href + '/inbox',
            'outbox' : args.user_actor_href + '/outbox',
            
            # Mastodon seems to need this bit, but it's not required in W3C ActivityPub spec
            #'publicKey' : {
            #    'id' : args.user_actor_href + '#main-key',
            #    'owner' : args.user_actor_href,
            #    'publicKeyPem' : 
            #}
        }
        # Update the conf to be given to cherrypy
        conf[args.actors_endpoint] = {
            'tools.staticdir.on' : False,
            'tools.encode.on' : True,
            'tools.encode.encoding' : 'utf-8',
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/ld+json')],
        }

    def _cp_dispatch(self, vpath):
        if len(vpath) == 1:
            cherrypy.request.params['actor'] = vpath.pop()
            return self
        return vpath

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self, actor):
        if actor == self.user_account:
            return self.cached_response
        raise cherrypy.HTTPError(404, 'Actor not found')