"""Download an accessible Xiaohongshu video for the recipe skill."""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.error

SHORT_HOSTS = {'xhslink.cn', 'www.xhslink.cn', 'xhslink.com', 'www.xhslink.com'}
ALLOWED = SHORT_HOSTS | {'xhslink.com', 'www.xhslink.com', 'xiaohongshu.com', 'www.xiaohongshu.com'}

def validate(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ('http', 'https') or p.hostname not in ALLOWED or p.username or p.password or p.port:
        raise ValueError('只接受小红书或 xhslink.cn / xhslink.com 分享链接')
    return url

class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def resolve(text):
    match = re.search(r'https?://[^\s<>]+', text)
    if not match:
        raise ValueError('未找到分享链接')
    url = validate(match[0].rstrip('。，！）)'))
    if urllib.parse.urlsplit(url).hostname in SHORT_HOSTS:
        with urllib.request.build_opener(Redirect).open(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
            url = validate(response.url)
    if urllib.parse.urlsplit(url).path.rstrip('/') == '/login':
        raise ValueError('小红书将分享链接跳转至登录页；尚未取得笔记或视频。请提供自行下载的视频或字幕，无需在聊天中提供 Cookie 或密码。')
    if not re.match(r'^/(explore|discovery/item)/[a-fA-F0-9]+/?$', urllib.parse.urlsplit(url).path):
        raise ValueError('请提供具体笔记的完整分享链接')
    return url

def describe_error(error):
    # Do not echo exception URLs: they may contain share authentication tokens.
    if isinstance(error, urllib.error.HTTPError):
        return f'页面返回 HTTP {error.code}；需检查笔记访问条件，不能据此断言笔记失效。'
    if isinstance(error, urllib.error.URLError):
        reason = str(error.reason)
        if 'Tunnel connection failed: 403' in reason:
            return '环境代理拒绝 HTTPS CONNECT（403），请求尚未到达小红书。请在环境设置保存网络放行规则，再重试；更换 Cookie 或视频解析器不能解决此问题。'
        return '网络连接失败；请检查环境网络策略、代理与连接状态。'
    if isinstance(error, subprocess.CalledProcessError):
        return '视频解析器未能完成下载，请检查笔记访问条件与解析器输出。'
    if isinstance(error, ValueError):
        return str(error)
    return '本地文件或工具操作失败，请检查依赖安装和输出目录权限。'

def browser_download(share, out):
    match = re.search(r'https?://[^\s<>]+', share)
    if not match:
        raise ValueError('未找到分享链接')
    url = validate(match[0].rstrip('。，！）)'))
    helper = pathlib.Path(__file__).with_name('browser_note.cjs')
    result = subprocess.run(['node', str(helper)], input=url, text=True,
                            capture_output=True, timeout=65)
    if result.returncode:
        raise ValueError('正常浏览器也未取得公开视频；请检查浏览器依赖或使用已授权的视频文件。')
    data = json.loads(result.stdout)
    streams = data['note']['video']['media']['stream']
    candidates = [v for group in streams.values() for v in group if v.get('masterUrl')]
    if not candidates:
        raise ValueError('笔记中没有可下载视频')
    video_url = candidates[0]['masterUrl']
    p = urllib.parse.urlsplit(video_url)
    if p.scheme not in ('http', 'https') or not (p.hostname or '').endswith('.xhscdn.com'):
        raise ValueError('视频 CDN 域名不在当前支持范围')
    video_url = urllib.parse.urlunsplit(('https', p.netloc, p.path, p.query, ''))
    out.mkdir(parents=True, exist_ok=True)
    (out / (data['id'] + '.info.json')).write_text(json.dumps(data, ensure_ascii=False))
    target = out / (data['id'] + '.mp4')
    partial = target.with_suffix('.mp4.part')
    request = urllib.request.Request(video_url, headers={'Referer': 'https://www.xiaohongshu.com/', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(request, timeout=40) as response, partial.open('wb') as f:
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 200 * 1024 * 1024:
                    raise ValueError('视频超过 200 MiB 限制')
                f.write(chunk)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    print(f'浏览器解析并下载成功：{target.name}')

if __name__ == '__main__':
    if sys.platform == 'darwin':
        import truststore
        truststore.inject_into_ssl()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('share')
    parser.add_argument('--output', default='imports')
    parser.add_argument('--browser', action='store_true', help='使用正常 Chromium 浏览器读取公开笔记')
    args = parser.parse_args()
    try:
        if args.browser:
            browser_download(args.share, pathlib.Path(args.output).resolve())
            sys.exit(0)
        url = resolve(args.share)
        out = pathlib.Path(args.output).resolve()
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, '-m', 'yt_dlp', '--no-playlist', '--write-info-json', '--max-filesize', '200M', '--socket-timeout', '30', '-o', str(out / '%(id)s.%(ext)s'), url], check=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'解析或下载失败：{describe_error(error)}\n请保留完整分享参数；登录或访问限制时改用自行提供的视频/字幕，不绕过访问限制。\n')
