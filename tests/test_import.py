import unittest
from scripts.import_video import resolve, validate, describe_error
import urllib.error
from unittest.mock import patch, MagicMock

class Links(unittest.TestCase):
    def test_proxy_denial_diagnostic(self):
        error = urllib.error.URLError(OSError('Tunnel connection failed: 403 Forbidden'))
        self.assertIn('尚未到达小红书', describe_error(error))

    def test_http_error_does_not_leak_url(self):
        error = urllib.error.HTTPError('https://example.com/?xsec_token=secret', 403, 'Forbidden', {}, None)
        self.assertNotIn('secret', describe_error(error))
        self.assertIn('页面返回 HTTP 403', describe_error(error))

    def test_login_redirect(self):
        response = MagicMock()
        response.__enter__.return_value.url = 'https://www.xiaohongshu.com/login?redirectPath=hidden'
        with patch('scripts.import_video.urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, '登录页'):
                resolve('https://xhslink.cn/o/9Fra5qevqvo')

    def test_cn_share_host(self):
        self.assertEqual(validate("https://xhslink.cn/o/9Fra5qevqvo"), "https://xhslink.cn/o/9Fra5qevqvo")

    def test_preserve_token(self):
        url='https://www.xiaohongshu.com/explore/abc123?xsec_token=test'
        self.assertEqual(resolve('分享 '+url+' 更多'),url)
    def test_reject_hosts(self):
        for url in ['http://localhost/a','https://www.xiaohongshu.com.evil.com/explore/abc','https://u:p@www.xiaohongshu.com/explore/abc','file:///tmp/x']:
            with self.assertRaises(ValueError): validate(url)
    def test_require_note(self):
        with self.assertRaises(ValueError): resolve('https://www.xiaohongshu.com/user/profile/abc')
