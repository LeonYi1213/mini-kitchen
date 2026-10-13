"""Private single-owner import service. Real stages; never manufactures recipes on read failure."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from import_video import validate
sys.path.insert(0, str(ROOT / 'backend'))
from recipe_format import PROMPT, FORMAT_VERSION, asset_path, current_recipe, materialize, validate_visual_plan

STORAGE = Path(os.environ.get('KITCHEN_DATA_DIR', ROOT / 'imports/service'))
LOCK = threading.Lock()
POOL = ThreadPoolExecutor(max_workers=1)


def initialize():
    STORAGE.mkdir(parents=True, exist_ok=True)
    (STORAGE/'uploads').mkdir(exist_ok=True)
    for path in (STORAGE/'uploads').glob('*.video'):
        path.unlink()
    with sqlite3.connect(STORAGE / 'jobs.sqlite') as db:
        db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        for job_id, payload in db.execute('SELECT id, payload FROM jobs').fetchall():
            job = json.loads(payload)
            if job['status'] in ('uploading', 'queued', 'running'):
                job.update(status='failed', message='服务已重启，请重试。')
                db.execute('UPDATE jobs SET payload=? WHERE id=?', (json.dumps(job), job_id))


def read(job_id):
    with sqlite3.connect(STORAGE / 'jobs.sqlite') as db:
        row = db.execute('SELECT payload FROM jobs WHERE id=?', (job_id,)).fetchone()
    return json.loads(row[0]) if row else None


def write(job):
    with sqlite3.connect(STORAGE / 'jobs.sqlite') as db:
        db.execute('INSERT OR REPLACE INTO jobs VALUES (?, ?)', (job['id'], json.dumps(job, ensure_ascii=False)))


def stage(job_id, count, **values):
    with LOCK:
        job = read(job_id)
        if not job or job['status'] == 'cancelled':
            raise InterruptedError()
        job.update(completedStages=count, **values)
        write(job)


def valid_recipe(recipe):
    if not isinstance(recipe, dict) or not isinstance(recipe.get('title'), str) or not recipe['title'].strip():
        return False
    ingredients = recipe.get('ingredients')
    if not isinstance(ingredients, list) or not ingredients:
        return False
    for item in ingredients:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not item['name'].strip() or not isinstance(item.get('unit'), str):
            return False
        amount = item.get('amount')
        if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 0 <= amount <= 100000):
            return False
    for part in ('prep', 'cook'):
        steps = recipe.get(part)
        if not isinstance(steps, list) or (part == 'cook' and not steps) or not all(isinstance(s, str) and s.strip() for s in steps):
            return False
        timing = recipe.get('timing')
        if not isinstance(timing, dict):
            return False
        times = timing.get(part)
        if not isinstance(times, list) or len(times) != len(steps):
            return False
        for value in times:
            if not isinstance(value, dict) or any(type(value.get(k)) is not int for k in ('min', 'max')):
                return False
            if not 0 <= value['min'] <= value['max'] <= 10080 or ('wait' in value and type(value['wait']) is not bool):
                return False
    return True


def model_config():
    """Support the user's existing Kimi environment without copying keys to iOS."""
    if os.environ.get('KIMI_API_KEY'):
        model = os.environ.get('KIMI_MODEL', '').strip()
        if not model:
            raise ValueError('Set a vision-capable KIMI_MODEL')
        return (os.environ['KIMI_API_KEY'], os.environ.get('KIMI_BASE_URL', 'https://api.moonshot.cn/v1'), model)
    key = os.environ.get('OPENAI_API_KEY', '')
    if not key:
        raise ValueError('Missing model key')
    return (key, os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'), os.environ.get('OPENAI_MODEL', 'gpt-4.1'))


def run(job_id, url=None, uploaded=None, digest=None):
    asset_folder = None
    try:
        stage(job_id, 0, status='running')
        with tempfile.TemporaryDirectory(prefix='recipe-', dir=STORAGE) as folder:
            folder = Path(folder)
            prefix = 'video' if uploaded else 'xhs'
            if uploaded:
                target = folder/'upload.mp4'
                shutil.move(str(uploaded), target)
                videos = [target]
                note_id = digest[:24]
                metadata = {'note': {}}
            else:
                # Normal reader; never bypass source access restrictions.
                subprocess.run([sys.executable, str(ROOT/'scripts/import_video.py'), url,
                                '--browser', '--output', str(folder)], capture_output=True, timeout=150, check=True)
                infos = list(folder.glob('*.info.json'))
                videos = list(folder.glob('*.mp4'))
                if len(infos) != 1 or len(videos) != 1:
                    raise ValueError('No content')
                metadata = json.loads(infos[0].read_text())
                note_id = metadata.get('id', '')
                if not re.fullmatch(r'[a-fA-F0-9]{24}', note_id):
                    raise ValueError('Invalid note id')
            stage(job_id, 1)
            # Canonical ID deduplication happens before invoking a paid model.
            for path in (ROOT/'web/recipes').glob('*/recipe.json'):
                recipe = json.loads(path.read_text())
                if recipe['id'] == prefix + '-' + note_id:
                    # Use the same bundled names as the native catalog.
                    for step in recipe.get('illustrated_steps', []):
                        step['image'] = path.parent.name + '-' + step['image']
                    recipe['cover'] = recipe['illustrated_steps'][-1]['image'] if recipe.get('illustrated_steps') else None
                    stage(job_id, 4, status='completed', recipe=recipe, cacheHit=True)
                    return
            with sqlite3.connect(STORAGE/'jobs.sqlite') as db:
                previous = [json.loads(row[0]) for row in db.execute('SELECT payload FROM jobs')]
            for job in previous:
                if job.get('status') == 'completed' and (job.get('recipe') or {}).get('id') == prefix + '-' + note_id and current_recipe(job['recipe'], STORAGE):
                    stage(job_id, 4, status='completed', recipe=job['recipe'], cacheHit=True)
                    return
            duration = float(subprocess.check_output(['ffprobe', '-f', 'mov', '-protocol_whitelist', 'file,pipe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(videos[0])], timeout=20))
            if not 0 < duration <= 900:
                raise ValueError('Video too long')
            interval = max(1, duration / 80)
            subprocess.run(['ffmpeg', '-f', 'mov', '-protocol_whitelist', 'file,pipe', '-v', 'error', '-i', str(videos[0]), '-vf', f'fps=1/{interval}:start_time=0,scale=768:-2', '-frames:v', '80', str(folder/'frame-%03d.jpg')], capture_output=True, timeout=90, check=True)
            frames = sorted(folder.glob('frame-*.jpg'))
            if not frames:
                raise ValueError('No frames')
            stage(job_id, 2)
            note = metadata.get('note', {})
            content = [{'type': 'text', 'text': json.dumps({'title': note.get('title'), 'description': note.get('desc')}, ensure_ascii=False)}]
            for index, frame in enumerate(frames, 1):
                seconds = (index - 1) * interval
                content.append({'type': 'text', 'text': f'frame_index={index}; approximate video time={seconds:.1f}s'})
                content.append({'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(frame.read_bytes()).decode()}})
            api_key, base_url, model = model_config()
            endpoint = base_url.rstrip('/') + '/chat/completions'
            if urlsplit(endpoint).scheme != 'https':
                raise ValueError('HTTPS required')
            messages = [{'role': 'system', 'content': PROMPT}, {'role': 'user', 'content': content}]
            for attempt in range(2):
                stage(job_id, 2, model=model, formatVersion=FORMAT_VERSION, cacheHit=False)
                body = {'model': model, 'response_format': {'type': 'json_object'}, 'messages': messages}
                request = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'})
                with urllib.request.urlopen(request, timeout=180) as response:
                    result = json.load(response)
                raw = result['choices'][0]['message']['content']
                recipe = None
                try:
                    recipe = json.loads(raw)
                    if not valid_recipe(recipe):
                        raise ValueError('Invalid ingredients, steps or matching timing arrays')
                    validate_visual_plan(recipe, len(frames))
                    break
                except (ValueError, TypeError, KeyError) as error:
                    if attempt == 1 or (isinstance(recipe, dict) and recipe.get('error') == 'unreadable'):
                        raise
                    messages += [{'role': 'assistant', 'content': raw},
                                 {'role': 'user', 'content': '修正格式后重新输出完整 JSON，不改变素材事实：' + str(error)}]
            stage(job_id, 3)
            generation = uuid.uuid4().hex
            asset_folder = STORAGE / f'assets/{prefix}-{note_id}/{generation}'
            recipe = materialize(recipe, frames, interval, note_id, generation, STORAGE, prefix=prefix)
            stage(job_id, 4, status='completed', recipe=recipe)
            asset_folder = None  # Published images survive temporary video cleanup.
    except InterruptedError:
        pass
    except Exception as error:
        # Never return source tokens, provider errors or API keys to clients/logs.
        try:
            job = read(job_id)
            message = '无法整理该视频，请确认包含清晰的烹饪画面、时长不超过 15 分钟。' if uploaded else '暂时无法读取或整理这篇笔记，请重试。'
            if isinstance(error, subprocess.CalledProcessError) and b'XHS_NETWORK_RESTRICTED' in (error.stderr or b''):
                message = '小红书暂时限制了服务器网络访问（300012），未能读取笔记；当前无法通过此链接生成菜谱。'
            stage(job_id, job['completedStages'], status='failed', message=message)
        except InterruptedError:
            pass
    finally:
        if uploaded:
            Path(uploaded).unlink(missing_ok=True)
        if asset_folder is not None:
            shutil.rmtree(asset_folder, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, body):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        token = os.environ.get('KITCHEN_SERVICE_TOKEN', '')
        if not token or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
            self.reply(401, {'error': 'unauthorized'})
            return False
        return True

    def do_POST(self):
        if not self.authorized(): return
        if self.path == '/imports/video': return self.upload_video()
        if self.path != '/imports': return self.reply(404, {})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192: return self.reply(413, {})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not isinstance(payload.get('url'), str): raise ValueError()
            url = validate(payload['url'])
            if urlsplit(url).scheme != 'https': raise ValueError()
        except (ValueError, KeyError, TypeError):
            return self.reply(400, {'error': 'invalid_link'})
        try:
            model_config()
        except ValueError:
            return self.reply(503, {'error': 'unavailable'})
        with LOCK:
            with sqlite3.connect(STORAGE/'jobs.sqlite') as db:
                active = sum(json.loads(row[0])['status'] in ('uploading', 'queued', 'running') for row in db.execute('SELECT payload FROM jobs'))
            if active >= 3: return self.reply(429, {'error': 'busy'})
            job = {'id': str(uuid.uuid4()), 'status': 'queued', 'completedStages': 0}
            write(job)
        POOL.submit(run, job['id'], url)
        self.reply(202, job)

    def upload_video(self):
        # Raw file body, streamed to disk; never load a 200 MiB video in memory.
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.reply(400, {'error': 'invalid_length'})
        if not 0 < length <= 200 * 1024 * 1024:
            return self.reply(413, {'error': 'video_too_large'})
        if self.headers.get('Content-Type', '').split(';')[0] not in ('video/mp4', 'video/quicktime', 'application/octet-stream'):
            return self.reply(415, {'error': 'unsupported_video'})
        try:
            model_config()
        except ValueError:
            return self.reply(503, {'error': 'unavailable'})
        with LOCK:
            with sqlite3.connect(STORAGE/'jobs.sqlite') as db:
                active = sum(json.loads(row[0])['status'] in ('uploading', 'queued', 'running') for row in db.execute('SELECT payload FROM jobs'))
            if active >= 3: return self.reply(429, {'error': 'busy'})
            job = {'id': str(uuid.uuid4()), 'status': 'uploading', 'completedStages': 0}
            write(job)
        target = STORAGE/'uploads'/(job['id'] + '.video')
        try:
            self.connection.settimeout(60)
            digest = hashlib.sha256()
            remaining = length
            with target.open('wb') as file:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk: raise ValueError('incomplete_upload')
                    file.write(chunk); digest.update(chunk); remaining -= len(chunk)
            stage(job['id'], 0, status='queued')
            POOL.submit(run, job['id'], uploaded=target, digest=digest.hexdigest())
        except Exception:
            target.unlink(missing_ok=True)
            stage(job['id'], 0, status='failed', message='视频上传中断，请重新选择视频。')
            return self.reply(400, {'error': 'upload_failed'})
        self.reply(202, read(job['id']))

    def job_id(self):
        match = re.fullmatch(r'/imports/([0-9a-f-]{36})', self.path)
        return match[1] if match else None

    def do_GET(self):
        if not self.authorized(): return
        if self.path.startswith('/assets/'):
            path = asset_path(STORAGE, self.path[1:])
            if path is None or not path.is_file(): return self.reply(404, {})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Cache-Control', 'private, max-age=31536000, immutable')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        job = read(self.job_id()) if self.job_id() else None
        self.reply(200 if job else 404, job or {})

    def do_DELETE(self):
        if not self.authorized(): return
        with LOCK:
            job = read(self.job_id()) if self.job_id() else None
            if job and job['status'] in ('uploading', 'queued', 'running'):
                job['status'] = 'cancelled'
                write(job)
        self.reply(200 if job else 404, job or {})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    if not os.environ.get('KITCHEN_SERVICE_TOKEN'):
        parser.error('Set KITCHEN_SERVICE_TOKEN before starting the private service')
    initialize()
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
