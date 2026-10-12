#!/usr/bin/env python3
"""Run the Mac import service using environment variables or local Keychain settings."""
import argparse
import base64
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def configure():
    path = ROOT / '.local/service.json'
    config = json.loads(path.read_text()) if path.exists() else {}
    for name in ('KIMI_BASE_URL', 'KIMI_MODEL', 'KITCHEN_SERVICE_TOKEN', 'CHROMIUM_PATH'):
        if config.get(name):
            os.environ.setdefault(name, config[name])
    if not os.environ.get('KIMI_API_KEY'):
        key = os.environ.get('MOONSHOT_API_KEY', '')
        if not key and config.get('keychain_service') and config.get('keychain_account'):
            result = subprocess.run(['security', 'find-generic-password', '-s', config['keychain_service'],
                                     '-a', config['keychain_account'], '-w'], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                key = result.stdout.strip()
        if not key:
            raise SystemExit('No Kimi API credential. Set KIMI_API_KEY or configure .local/service.json Keychain references.')
        os.environ['KIMI_API_KEY'] = key
    if not os.environ.get('KIMI_MODEL') or not os.environ.get('KITCHEN_SERVICE_TOKEN'):
        raise SystemExit('Set KIMI_MODEL and KITCHEN_SERVICE_TOKEN in the environment or .local/service.json.')
    # Use macOS trust roots, including locally trusted proxy certificates. Never disable TLS verification.
    import truststore
    truststore.inject_into_ssl()
    os.environ['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + os.environ.get('PATH', '')
    os.chdir(ROOT)


def check_model():
    picture = next((ROOT / 'ios/MiniKitchen/Resources').glob('*.jpg'))
    content = [{'type': 'text', 'text': 'Describe the visible food in one short sentence. Return a JSON object with a nonempty description field.'},
               {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(picture.read_bytes()).decode()}}]
    body = {'model': os.environ['KIMI_MODEL'], 'response_format': {'type': 'json_object'},
            'messages': [{'role': 'user', 'content': content}]}
    endpoint = os.environ.get('KIMI_BASE_URL', 'https://api.moonshot.cn/v1').rstrip('/')
    if not endpoint.startswith('https://'):
        raise SystemExit('Kimi endpoint must use HTTPS.')
    req = urllib.request.Request(endpoint + '/chat/completions', data=json.dumps(body).encode(),
                                 headers={'Authorization': 'Bearer ' + os.environ['KIMI_API_KEY'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.load(response)
        parsed = json.loads(result['choices'][0]['message']['content'])
        if not isinstance(parsed.get('description'), str) or not parsed['description'].strip():
            raise ValueError('Invalid JSON content')
    except Exception as error:
        raise SystemExit(f'Model check failed: {type(error).__name__} (HTTP {getattr(error, "code", "n/a")}); credentials and response omitted.') from None
    print('PASS: Kimi authentication, image input and JSON output (' + os.environ['KIMI_MODEL'] + ')')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-model', action='store_true')
    parser.add_argument('--port', type=int, default=18080)
    args = parser.parse_args()
    configure()
    if args.check_model:
        check_model()
    else:
        sys.argv = [str(ROOT / 'backend/server.py'), '--port', str(args.port)]
        runpy.run_path(sys.argv[0], run_name='__main__')
