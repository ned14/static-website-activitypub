from __future__ import absolute_import, print_function
import unittest, cherrypy, sys, os, inspect, json, static_website_activitypub

try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode
try:
    from StringIO import StringIO
except:
    from io import StringIO

class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._local = cherrypy.lib.httputil.Host('127.0.0.1', 50000, "")
        cls._remote = cherrypy.lib.httputil.Host('127.0.0.1', 50001, "")
        cherrypy.server.unsubscribe()
        cls._instance = static_website_activitypub.main(['static-website-activitypub',
            '--quiet',
            '--serve-directory', '.',
            '--user-account', 'test@nowhere',
            '--website', 'http://nowhere'
        ], testing = True)
        next(cls._instance, None)
    
    @classmethod
    def tearDownClass(cls):
        next(cls._instance, None)
        del cls._instance
        
    # Borrowed from https://bitbucket.org/Lawouach/cherrypy-recipes/src/50aff88dc4e24206518ec32e1c32af043f2729da/testing/unit/serverless?at=default
    @classmethod
    def request(cls, path='/', method='GET', app_path='', scheme='http',
                proto='HTTP/1.1', data=None, headers=None, **kwargs):
        """
        CherryPy does not have a facility for serverless unit testing.
        However this recipe demonstrates a way of doing it by
        calling its internal API to simulate an incoming request.
        This will exercise the whole stack from there.

        Remember a couple of things:

        * CherryPy is multithreaded. The response you will get
          from this method is a thread-data object attached to
          the current thread. Unless you use many threads from
          within a unit test, you can mostly forget
          about the thread data aspect of the response.

        * Responses are dispatched to a mounted application's
          page handler, if found. This is the reason why you
          must indicate which app you are targetting with
          this request by specifying its mount point.

        You can simulate various request settings by setting
        the `headers` parameter to a dictionary of headers,
        the request's `scheme` or `protocol`.

        .. seealso: http://docs.cherrypy.org/stable/refman/_cprequest.html#cherrypy._cprequest.Response
        """
        # This is a required header when running HTTP/1.1
        h = {'Host': '127.0.0.1'}

        if headers is not None:
            h.update(headers)

        # If we have a POST/PUT request but no data
        # we urlencode the named arguments in **kwargs
        # and set the content-type header
        if method in ('POST', 'PUT') and not data:
            data = urlencode(kwargs)
            kwargs = None
            h['content-type'] = 'application/x-www-form-urlencoded'

        # If we did have named arguments, let's
        # urlencode them and use them as a querystring
        qs = None
        if kwargs:
            qs = urlencode(kwargs)

        # if we had some data passed as the request entity
        # let's make sure we have the content-length set
        fd = None
        if data is not None:
            h['content-length'] = '%d' % len(data)
            fd = StringIO(data)

        # Get our application and run the request against it
        app = cherrypy.tree.apps.get(app_path)
        if not app:
            # XXX: perhaps not the best exception to raise?
            raise AssertionError("No application mounted at '%s'" % app_path)

        # Cleanup any previous returned response
        # between calls to this method
        app.release_serving()

        # Let's fake the local and remote addresses
        request, response = app.get_serving(cls._local, cls._remote, scheme, proto)
        try:
            h = [(k, v) for k, v in h.items()]
            response = request.run(method, path, qs, proto, h, fd)
        finally:
            if fd:
                fd.close()
                fd = None

        if response.output_status.startswith(b'500'):
            print(response.body)
            raise AssertionError("Unexpected error")

        # collapse the response into a bytestring
        response.collapse_body()
        return response

class webfinger(TestCase):
    def runTest(self):
        resp = self.request('/.well-known/webfinger', resource = 'acct:test@nowhere')
        self.assertEqual(resp.output_status, b'200 OK')
        resp = json.loads(resp.body[0])
        matching = (link['href'] for link in resp['links'] if link['type'] == 'application/activity+json')
        user_url = next(matching, None)
        self.assertEqual(user_url, 'http://nowhere/actors/test')

class webfinger404(TestCase):
    def runTest(self):
        resp = self.request('/.well-known/webfinger', resource = 'acct:different@nowhere')
        self.assertEqual(resp.output_status, b'404 Not Found')
        resp = self.request('/.well-known/webfiner', resource = 'acct:different@nowhere')
        self.assertEqual(resp.output_status, b'404 Not Found')
        resp = self.request('/.well-known/')
        self.assertEqual(resp.output_status, b'404 Not Found')

class actor(TestCase):
    def runTest(self):
        resp = self.request('/actors/test/')
        self.assertEqual(resp.output_status, b'200 OK')
        resp = json.loads(resp.body[0])
        self.assertEqual(resp['inbox'], 'http://nowhere/actors/test/inbox')

class actor404(TestCase):
    def runTest(self):
        resp = self.request('/actors/different/')
        self.assertEqual(resp.output_status, b'404 Not Found')
        resp = self.request('/actors/')
        self.assertEqual(resp.output_status, b'404 Not Found')

if __name__ == '__main__':
    unittest.main()
    