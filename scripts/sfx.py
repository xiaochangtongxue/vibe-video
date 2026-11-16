#!/usr/bin/env python3
"""Synthesize deterministic 48 kHz stereo action sounds (needs numpy).

Batch: --manifest src/sfx.json --beats public/beats.json --outdir public/sfx

Pitched kinds take --note (e.g. F4) or --degree with --beats: degree 1-7 in the
key detected by analyze.py, so accents stay inside the song's scale.
"""
import argparse
import json
import wave
from pathlib import Path

import numpy as np

SR = 48000
NAMES = 'C C# D D# E F F# G G# A A# B'.split()
PITCHED = {'pluck', 'bell', 'marimba', 'piano'}
DEFAULT_SECONDS = {'pluck': .8, 'bell': 1.6, 'marimba': .5, 'piano': 1.2,
                   'kick': .35, 'tick': .06, 'whoosh': .45, 'riser': 1.0, 'blade': .9, 'boom': 1.4}


def note_hz(name):
    letter = name.rstrip('0123456789-')
    return 440 * 2 ** ((NAMES.index(letter) + 12 * (int(name[len(letter):]) + 1) - 69) / 12)


def degree_hz(beats_path, degree, octave):
    key = json.loads(Path(beats_path).read_text(encoding='utf-8'))['key']
    scale = key['scalePitchClasses']
    pc = scale[(degree - 1) % 7]
    octave += (degree - 1) // 7 + (pc < scale[0])  # scale steps past B wrap into the next octave
    return 440 * 2 ** ((pc + 12 * (octave + 1) - 69) / 12)


def synth(kind, seconds, hz, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(round(seconds * SR)) / SR
    if kind == 'pluck':  # Karplus-Strong string
        period = max(2, round(SR / hz))
        buf = rng.uniform(-1, 1, period)
        out = np.empty(len(t))
        for i in range(len(t)):
            out[i] = buf[i % period]
            buf[i % period] = .996 * .5 * (buf[i % period] + buf[(i + 1) % period])
        v = out
    elif kind == 'bell':
        v = sum(a * np.sin(2 * np.pi * hz * r * t) * np.exp(-d * t)
                for r, a, d in [(1, .6, 2.5), (2.76, .25, 4), (5.4, .15, 7)])
    elif kind == 'marimba':
        v = sum(a * np.sin(2 * np.pi * hz * r * t) * np.exp(-d * t)
                for r, a, d in [(1, .8, 9), (3.93, .2, 30), (9.2, .05, 60)])
    elif kind == 'piano':  # slightly stretched partials, faster decay up the series
        v = sum(np.sin(2 * np.pi * hz * n * np.sqrt(1 + 4e-4 * n * n) * t) * np.exp(-(1.5 + .8 * n) * t) / n
                for n in range(1, 8))
    elif kind == 'kick':
        f = 45 + 110 * np.exp(-28 * t)
        v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-9 * t)
    elif kind == 'blade':  # metal being drawn: inharmonic high partials gliding up, with a scrape at the start
        glide = 1 + .04 * t / seconds
        v = sum(a * np.sin(2 * np.pi * f0 * glide * t + ph) * np.exp(-d * t / seconds)
                for f0, a, d, ph in [(2350, .5, 4, 0), (3170, .35, 5, 1), (4410, .3, 7, 2), (5930, .2, 9, 3)])
        v = v + .5 * np.diff(rng.uniform(-1, 1, len(t)), prepend=0) * np.exp(-25 * t)
    elif kind == 'boom':  # deep impact: pitch drop to sub-bass plus a dull noise thump
        f = 32 + 78 * np.exp(-6 * t)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-4 * t / seconds)
        noise = rng.uniform(-1, 1, len(t)); thump = np.empty(len(t)); acc = 0.
        for i, x in enumerate(noise):
            acc += .03 * (x - acc); thump[i] = acc
        v = body + 3 * thump * np.exp(-30 * t)
    elif kind == 'tick':
        v = (.6 * np.sin(2 * np.pi * 1800 * t) + .4 * rng.uniform(-1, 1, len(t))) * np.exp(-70 * t)
    else:  # whoosh / riser: band-limited noise with a moving low-pass
        noise = rng.uniform(-1, 1, len(t))
        sweep = np.linspace(.02, .35, len(t)) if kind == 'riser' else .05 + .3 * np.sin(np.pi * t / seconds)
        v = np.empty(len(t)); acc = 0.
        for i, (x, k) in enumerate(zip(noise, sweep)):
            acc += k * (x - acc); v[i] = acc
        v *= (t / seconds) ** 2 if kind == 'riser' else np.sin(np.pi * t / seconds) ** 2
    v = v * np.minimum(1, t / .002)                       # 2 ms attack, avoids clicks
    v *= np.minimum(1, (len(t) - 1 - np.arange(len(t))) / 96)  # 2 ms release
    return v / (np.abs(v).max() or 1) * .5                # peak -6 dBFS, mix level set in Remotion


def render(out, kind, beats=None, duration=None, note=None, degree=None, octave=5, seed=7):
    if kind not in DEFAULT_SECONDS:
        raise ValueError(f'unknown kind {kind!r}; choose from {sorted(DEFAULT_SECONDS)}')
    seconds = duration or DEFAULT_SECONDS[kind]
    if not .02 <= seconds <= 10:
        raise ValueError('duration must be 0.02–10 s')
    hz = 440.
    if kind in PITCHED:
        if degree is not None:
            if not beats:
                raise ValueError('degree needs a beats.json for the key')
            hz = degree_hz(beats, degree, octave)
        elif note:
            hz = note_hz(note)
        else:
            raise ValueError(f'{kind} needs a note or a degree')

    pcm = (synth(kind, seconds, hz, seed) * 32767).astype('<i2')
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.repeat(pcm, 2).tobytes())
    print(f'{out} ({kind}, {seconds:.2f}s{f", {hz:.1f} Hz" if kind in PITCHED else ""})')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', type=Path,
                   help='JSON {name: {kind, degree?, octave?, note?, duration?, seed?}}; writes <outdir>/<name>.wav')
    p.add_argument('--outdir', type=Path, help='output folder for --manifest')
    p.add_argument('--kind', choices=sorted(DEFAULT_SECONDS))
    p.add_argument('--out', type=Path)
    p.add_argument('--duration', type=float)
    p.add_argument('--note', help='e.g. F4 (pitched kinds)')
    p.add_argument('--degree', type=int, help='scale degree 1-7+ in the key from --beats')
    p.add_argument('--octave', type=int, default=5)
    p.add_argument('--beats', type=Path, help='beats.json from analyze.py (for degrees)')
    p.add_argument('--seed', type=int, default=7)
    a = p.parse_args()

    try:
        if a.manifest:
            if not a.outdir:
                p.error('--manifest needs --outdir')
            for name, spec in json.loads(a.manifest.read_text(encoding='utf-8')).items():
                render(a.outdir / f'{name}.wav', beats=a.beats, **spec)
        elif a.kind and a.out:
            render(a.out, a.kind, a.beats, a.duration, a.note, a.degree, a.octave, a.seed)
        else:
            p.error('give --manifest/--outdir or --kind/--out')
    except ValueError as e:
        p.error(str(e))


if __name__ == '__main__':
    main()
