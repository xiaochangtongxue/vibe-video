#!/usr/bin/env python3
"""Create a Remotion project from the template, with music, beats.json and SFX ready.

Audio whose SHA-256 matches a track listed in assets/MUSIC.md gets its
precomputed beats; other audio is analyzed with analyze.py.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from analyze import sha256

SKILL = Path(__file__).resolve().parent.parent
SIZES = {'16:9': (1920, 1080), '9:16': (1080, 1920)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('dir', type=Path)
    p.add_argument('--audio', type=Path, required=True)
    p.add_argument('--ratio', choices=sorted(SIZES), default='16:9')
    p.add_argument('--fps', type=int, default=30)
    a = p.parse_args()

    if a.dir.exists() and any(a.dir.iterdir()):
        p.error(f'{a.dir} is not empty')
    if not a.audio.is_file():
        p.error(f'audio not found: {a.audio}')

    shutil.copytree(SKILL / 'template', a.dir, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('node_modules', 'out'))
    music = f'music{a.audio.suffix.lower()}'
    (a.dir / 'public').mkdir(exist_ok=True)
    shutil.copy2(a.audio, a.dir / 'public' / music)

    beats = a.dir / 'public' / 'beats.json'
    digest = sha256(a.audio)
    bundled = next((f for f in sorted((SKILL / 'assets').glob('*.beats.json'))
                    if json.loads(f.read_text(encoding='utf-8'))['audioSha256'] == digest), None)
    if bundled:
        shutil.copy2(bundled, beats)
        print(f'bundled track: using precomputed beats ({bundled.name})', flush=True)
    else:
        subprocess.run([sys.executable, str(SKILL / 'scripts' / 'analyze.py'), str(a.audio), '--out', str(beats)], check=True)

    w, h = SIZES[a.ratio]
    (a.dir / 'src' / 'project.json').write_text(
        json.dumps({'width': w, 'height': h, 'fps': a.fps, 'music': music}, indent=2), encoding='utf-8')

    subprocess.run([sys.executable, str(SKILL / 'scripts' / 'sfx.py'), '--manifest', str(a.dir / 'src' / 'sfx.json'),
                    '--beats', str(beats), '--outdir', str(a.dir / 'public' / 'sfx')], check=True)
    print(f'\nready: {a.dir}  ({w}x{h} @ {a.fps}fps)\n  cd {a.dir}\n  npm install\n  npm run studio')


if __name__ == '__main__':
    main()
