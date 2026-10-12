#!/usr/bin/env python3
"""Clone the handoff bundle or safely copy it into an existing local project."""
import argparse
from datetime import datetime
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import uuid


def install(bundle, target):
    bundle = bundle.expanduser().resolve()
    target = target.expanduser().resolve()
    if not bundle.is_file():
        raise SystemExit(f'找不到 Git 包：{bundle}')
    if not target.exists() or (target.is_dir() and not any(target.iterdir())):
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', str(bundle), str(target)], check=True)
        return target
    if not target.is_dir():
        raise SystemExit('目标必须是项目目录。')
    with tempfile.TemporaryDirectory(prefix='mini-kitchen-import-') as staging:
        source = Path(staging) / 'source'
        subprocess.run(['git', 'clone', '--quiet', str(bundle), str(source)], check=True)
        tracked = subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).decode().split('\0')
        changes = []
        for relative in filter(None, tracked):
            path = Path(relative)
            if any(part in ('.git', '.env', 'node_modules', 'Local.xcconfig') or part.startswith('.env.') for part in path.parts):
                continue
            src, dst = source/path, target/path
            if not src.is_file() or src.is_symlink():
                raise SystemExit(f'不支持的源文件：{relative}')
            for ancestor in [dst, *dst.parents]:
                if ancestor == target: break
                if ancestor.is_symlink() or (ancestor.exists() and ancestor != dst and not ancestor.is_dir()):
                    raise SystemExit(f'目标路径存在链接或文件冲突，尚未写入：{relative}')
            if dst.exists() and not dst.is_file():
                raise SystemExit(f'目标目录与文件冲突，尚未写入：{relative}')
            data = src.read_bytes()
            if relative == '.gitignore' and dst.exists():
                old = dst.read_text()
                additions = [line for line in data.decode().splitlines() if line and line not in old.splitlines()]
                data = (old.rstrip('\n')+'\n'+'\n'.join(additions)+'\n').encode()
            if not dst.exists() or dst.read_bytes() != data:
                changes.append((path, src, dst, data))
        if not changes:
            print('本地已经是这份交接代码，无需修改。')
            return target
        backup = target.parent / (target.name + '.before-import-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
        backup.mkdir()
        # Back up every affected existing file before making any project changes.
        for relative, src, dst, data in changes:
            if dst.exists():
                copy = backup/relative; copy.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(dst, copy)
        (backup/'imported-files.txt').write_text('\n'.join(str(item[0]) for item in changes)+'\n')
        print(f'改动前备份：{backup}')
        for relative, src, dst, data in changes:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as handle:
                handle.write(data); temp = Path(handle.name)
            shutil.copymode(src, temp)
            temp.replace(dst)
        print(f'已导入 {len(changes)} 个文件，原有 Git 历史和私有配置保持不变。')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path, help='本地小厨房项目完整路径')
    parser.add_argument('--bundle', type=Path, default=Path(__file__).with_name('MiniKitchen.bundle'))
    args = parser.parse_args()
    target = install(args.bundle, args.target)
    print('打开 Xcode：open ' + shlex.quote(str(target/'ios/MiniKitchen.xcodeproj')))
