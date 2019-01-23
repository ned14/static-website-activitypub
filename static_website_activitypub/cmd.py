from __future__ import absolute_import, print_function
import sys, os, cherrypy, json
from configargparse import ArgParser, YAMLConfigFileParser

version='0.01'
args = {}

# actor response
"""           '@context' : [
               "https://www.w3.org/ns/activitystreams",
               "https://w3id.org/security/v1"
           ],
           'id' : args.user_endpoint,
           'type' : 'Person',
           'preferredUsername' : 'default',
           'inbox' : args.user_endpoint + '/inbox',
           'publicKey' : {
               'id' : args.user_endpoint + '#main-key',
               'owner' : args.user_endpoint,
               'publicKeyPem' : 
           }
"""

class WellKnown(object):
    def __init__(self):
       self.cached_response = {
           'subject' : 'acct:' + args.user_account + '@' + args.user_domain,
           'links' : [
               {
                   'rel': 'self',
                   'type': 'application/activity+json',
                   'href': args.user_endpoint + '/' + args.user_account
               }
           ]
       }
    """The /.well-known REST API implementation"""
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def webfinger(self, resource):
        if resource == 'acct:' + args.user_account + '@' + args.user_domain:
            return self.cached_response
        raise cherrypy.HTTPError(404, 'Resource not found')
    
class Root(object):
    """The root website implementation"""
    def __init__(self):
        self.well_known = WellKnown()
        
    def _cp_dispatch(self, vpath):
        if len(vpath) >= 1:
            if vpath[0] == '.well-known':
                return self.well_known
        return vpath

def abspath(path):
    if not path:
        return path
    if not os.path.isabs(path):
        return os.path.abspath(path)
    return path

def main(argv = sys.argv):
    argp = ArgParser(prog = 'static-website-activitypub',
        description =
    r'''A CherryPy-based Python web server which implements the ActivityPub
    client-to-server REST API for static website generators.''',
        config_file_parser_class = YAMLConfigFileParser,  ## Their default corrupts Windows filesystem paths
        default_config_files = ['./static-website-activitypub.yaml'],
        auto_env_var_prefix = 'SWA_',
        args_for_setting_config_path = ['-c', '--config-file'],
        args_for_writing_out_config_file = ['-w', '--write-out-config-file'])
    argp.add_argument('-q', '--quiet', action = "store_true", default = False, help = 'print nothing to stdout')
    argp.add_argument('-b', '--bind', dest = "bind_address", metavar = 'ADDRESS', default = '127.0.0.1', help = 'address to run server upon. Defaults to 127.0.0.1.')
    argp.add_argument('-p', '--port', dest = 'bind_port', metavar = "PORTNO", type = int, default = 8080, help = 'port to run server upon. Defaults to 8080.')
    argp.add_argument('--post-format', dest = 'post_format', metavar = "FORMAT", default = 'yaml-front-matter', help = 'how to write the post. Options include: yaml-front-matter', choices = ['yaml-front-matter'])
    argp.add_argument('-s', '--serve-directory', dest = 'serve_directory', metavar = '<serve directory>', type = abspath, default = '', help = 'Path to directory to serve')
    argp.add_argument('-o', '--posts-directory', dest = 'posts_directory', metavar = 'DIR', type = abspath, default = '', help = 'Path to directory containing posts')
    argp.add_argument('-r', '--regenerate-command', dest = 'regenerate_command', metavar = '<shell cmd>', default = '', help = 'shell command to execute to cause the regeneration of the static website e.g. "cd path/to/your/hugo/sources && hugo"')
    argp.add_argument('-u', '--user-account', dest = 'user_account', metavar = 'EMAIL', default = '', help = 'Email account for the user whose posts are being published.')

    argp.add_argument('--users-endpoint', dest = 'user_endpoint', metavar = 'PATH', default = '/users', help = 'REST endpoint for querying the users. Defaults to "/users" (obviously change this if you have a /users directory or file).')
    argp.add_argument('--version', action='version', version='static-website-activitypub ' + version)

    global args
    args = argp.parse_args(argv[1:])
    if not args.quiet:
        print('static-website-activitypub v' + version + ' (C) 2019 Niall Douglas http://www.nedprod.com/')
        print('Running with config:\n   ' + argp.format_values().replace('\n', '\n   '))
    if not args.serve_directory:
        print('FATAL: serve-directory is not set, cannot continue!', file = sys.stderr)
        sys.exit(1)
    elif not os.path.isabs(args.serve_directory) or not os.path.exists(args.serve_directory):
        print('FATAL: serve-directory is set to "' + args.serve_directory + '" which is not absolute, or doesn\'t exist', file = sys.stderr)
        sys.exit(1)
    if '@' not in args.user_account:
        print('FATAL: user-account is not in email address format, cannot continue!', file = sys.stderr)
        sys.exit(1)
    args.user_domain = args.user_account.split('@')[1]
    args.user_account = args.user_account.split('@')[0]
    if not args.posts_directory:
        print('WARNING: posts-directory is not set, ActivityPub service will not be able to write posts!', file = sys.stderr)
        args.posts_directory = None
    elif not os.path.isabs(args.posts_directory) or not os.path.exists(args.posts_directory):
        print('FATAL: posts-directory is set to "' + args.posts_directory + '" which is not absolute, or doesn\'t exist', file = sys.stderr)
        sys.exit(1)
    if not args.regenerate_command:
        print('WARNING: regenerate-command is not set, ActivityPub service will not be able to regenerate the static website after writing a new post!', file = sys.stderr)
        args.regenerate_command = None
        
    cherrypy.config.update({
        'server.socket_host' : args.bind_address,
        'server.socket_port' : args.bind_port,
        'log.screen' : not args.quiet,
    })
    cherrypy.tree.mount(Root(), '/', {
        '/' : {
            'tools.staticdir.on' : True,
            'tools.staticdir.debug' : not args.quiet,
            'tools.staticdir.root': os.path.abspath(args.serve_directory),
            'tools.staticdir.dir': '',
            'tools.staticdir.index': 'index.html',
        },
        '/.well-known' : {
            'tools.staticdir.on' : False,
            'tools.encode.on' : True,
            'tools.encode.encoding' : 'utf-8',
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
        }
    })
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()
    return 0
        
if __name__ == "__main__":
    sys.exit(main())
