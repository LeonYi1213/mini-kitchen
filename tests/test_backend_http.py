"""Local HTTP integration checks; run with KITCHEN_RUN_HTTP_TESTS=1."""
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from test_backend import BackendTests, server


@unittest.skipUnless(os.environ.get('KITCHEN_RUN_HTTP_TESTS') == '1', 'opt in to local socket tests')
class HTTPTests(BackendTests):
    def setUp(self):
        super().setUp()
        self.env = patch.dict(os.environ, {'KITCHEN_SERVICE_TOKEN': 'local-test-token', 'OPENAI_API_KEY': 'test-placeholder'})
        self.env.start()
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.http.server_address[1])
        self.submit = patch.object(server.POOL, 'submit')
        self.worker = self.submit.start()

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        self.submit.stop(); self.env.stop()
        super().tearDown()

    def request(self, path, method='GET', body=None, token='local-test-token'):
        request = urllib.request.Request(self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                         headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_authentication_and_validation(self):
        self.assertEqual(self.request('/imports', 'POST', {'url': 'https://xhslink.cn/o/test'}, token='wrong')[0], 401)
        for invalid in ['https://example.com', 'http://xhslink.cn/o/test', 123]:
            self.assertEqual(self.request('/imports', 'POST', {'url': invalid})[0], 400)
        self.worker.assert_not_called()

    def test_create_poll_cancel_and_late_update(self):
        code, job = self.request('/imports', 'POST', {'url': 'https://xhslink.cn/o/test'})
        self.assertEqual(code, 202)
        self.assertEqual(job['completedStages'], 0)
        path = '/imports/' + job['id']
        self.assertEqual(self.request(path)[1]['status'], 'queued')
        self.assertEqual(self.request(path, 'DELETE')[1]['status'], 'cancelled')
        with self.assertRaises(InterruptedError): server.stage(job['id'], 4, status='completed')
        self.assertEqual(self.request(path)[1]['status'], 'cancelled')

    def test_unconfigured_model_does_not_queue(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            self.assertEqual(self.request('/imports', 'POST', {'url': 'https://xhslink.cn/o/test'})[0], 503)
        self.worker.assert_not_called()

    def test_bounded_queue(self):
        for _ in range(3):
            self.assertEqual(self.request('/imports', 'POST', {'url': 'https://xhslink.cn/o/test'})[0], 202)
        self.assertEqual(self.request('/imports', 'POST', {'url': 'https://xhslink.cn/o/test'})[0], 429)
