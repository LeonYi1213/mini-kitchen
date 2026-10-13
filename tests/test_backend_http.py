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

    def upload(self, data=b'video-bytes', declared=None, token='local-test-token', media='video/mp4'):
        import http.client
        conn = http.client.HTTPConnection('127.0.0.1', self.http.server_address[1], timeout=5)
        conn.request('POST', '/imports/video', body=data, headers={'Authorization': 'Bearer ' + token,
                     'Content-Type': media, 'Content-Length': str(len(data) if declared is None else declared)})
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result

    def test_video_upload_stream_and_identity(self):
        import hashlib
        code, job = self.upload()
        self.assertEqual(code, 202)
        args = self.worker.call_args
        self.assertEqual(args.kwargs['uploaded'].read_bytes(), b'video-bytes')
        self.assertEqual(args.kwargs['digest'], hashlib.sha256(b'video-bytes').hexdigest())
        self.assertEqual(job['status'], 'queued')

    def test_upload_rejection_does_not_queue(self):
        self.assertEqual(self.upload(token='wrong')[0], 401)
        self.assertEqual(self.upload(media='text/plain')[0], 415)
        self.assertEqual(self.upload(data=b'')[0], 413)
        self.assertEqual(self.upload(data=b'', declared=200*1024*1024+1)[0], 413)
        self.worker.assert_not_called()
        self.assertEqual(list((server.STORAGE/'uploads').iterdir()), [])

    def test_uploads_share_queue_limit_and_restart_cleanup(self):
        for _ in range(3): self.assertEqual(self.upload()[0], 202)
        self.assertEqual(self.upload()[0], 429)
        self.assertEqual(self.request('/imports', 'POST', {'url':'https://xhslink.cn/o/test'})[0], 429)
        server.initialize()
        self.assertEqual(list((server.STORAGE/'uploads').iterdir()), [])

    def test_images_require_auth_and_reject_traversal(self):
        reference = 'assets/xhs-' + 'a' * 24 + '/' + 'b' * 32 + '/frame-001.jpg'
        path = server.STORAGE / reference
        path.parent.mkdir(parents=True)
        path.write_bytes(b'jpeg-image')
        self.assertEqual(self.request('/' + reference, token='wrong')[0], 401)
        req = urllib.request.Request(self.base + '/' + reference, headers={'Authorization': 'Bearer local-test-token'})
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
            self.assertEqual(response.read(), b'jpeg-image')
        self.assertEqual(self.request('/assets/../../jobs.sqlite')[0], 404)
