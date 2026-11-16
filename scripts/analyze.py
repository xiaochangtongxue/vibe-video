#!/usr/bin/env python3
"""Analyze music into beats.json: beats with inferred downbeats, onsets, key.

Downbeats and key are inferred from audio features, not ground truth; check
them by ear in the first preview. Requires FFmpeg and numpy. Beat/onset
detection for music without a matching cache also requires librosa.

Onset layering (beats / percussive onsets / tonal onsets) follows the approach
of xiaominggpT7890/vibe-bgm-skill (MIT).
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

SR = 22050
N_FFT, HOP = 2048, 512
NAMES = 'C C# D D# E F F# G G# A A# B'.split()
# Krumhansl-Kessler key profiles
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
MAJOR_STEPS, MINOR_STEPS = [0, 2, 4, 5, 7, 9, 11], [0, 2, 3, 5, 7, 8, 10]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def spectrogram(y):
    frames = np.lib.stride_tricks.sliding_window_view(y, N_FFT)[::HOP]
    S = np.abs(np.fft.rfft(frames * np.hanning(N_FFT).astype(np.float32), axis=1))
    times_ms = (np.arange(len(S)) * HOP + N_FFT / 2) / SR * 1000
    return S, np.fft.rfftfreq(N_FFT, 1 / SR), times_ms


def chroma(S, freqs):
    band = (freqs > 60) & (freqs < 5000)
    pitch_class = (np.round(12 * np.log2(freqs[band] / 440)) + 9) % 12
    power = S[:, band] ** 2
    return np.stack([power[:, pitch_class == k].sum(1) for k in range(12)], axis=1)


def detect_events(y):
    """Beats and two onset layers via librosa (only needed without a cache)."""
    import librosa
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=SR, hop_length=HOP, trim=False)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    harmonic, percussive = librosa.effects.hpss(y)

    def onsets(signal):
        e = librosa.onset.onset_strength(y=signal, sr=SR, hop_length=HOP)
        frames = librosa.onset.onset_detect(onset_envelope=e, sr=SR, hop_length=HOP, backtrack=False)
        peak = e.max() or 1
        return [{'timeMs': round(float(librosa.frames_to_time(f, sr=SR, hop_length=HOP)) * 1000),
                 'strength': round(float(e[f] / peak), 4)} for f in frames]

    peak = env.max() or 1
    beats = [{'timeMs': round(float(librosa.frames_to_time(f, sr=SR, hop_length=HOP)) * 1000),
              'strength': round(float(env[f] / peak), 4)} for f in beat_frames]
    return float(np.atleast_1d(tempo)[0]), beats, onsets(percussive), onsets(harmonic)


def from_cache(path):
    """Read a vibe-bgm-skill `bgm-rhythm-v1` cache."""
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    pick = lambda items: [{'timeMs': e['timeMs'], 'strength': e['strength']} for e in items]
    return d['audioSha256'], d['bpm'], pick(d['beats']), pick(d['onsets']), pick(d['tonalOnsets'])


def downbeat_phase(beat_ms, S, freqs, times_ms, duration_ms, meter):
    """Pick the beat phase where bass hits and harmony changes concentrate.

    Bass onset (kick) and chord changes both favor bar starts; a single strong
    onset does not. Returns (phase, confidence = margin over runner-up).
    """
    low = np.log1p(S[:, (freqs > 30) & (freqs < 150)].sum(1))
    low_flux = np.maximum(0, np.diff(low, prepend=low[0]))
    t = np.asarray(beat_ms, float)
    bass = np.array([low_flux[np.abs(times_ms - x) <= 50].max(initial=0) for x in t])

    C = chroma(S, freqs)
    edges = np.append(t, duration_ms)
    spans = np.array([C[(times_ms >= a) & (times_ms < b)].mean(0) if ((times_ms >= a) & (times_ms < b)).any()
                      else np.zeros(12) for a, b in zip(edges[:-1], edges[1:])])
    spans /= np.linalg.norm(spans, axis=1, keepdims=True) + 1e-9
    change = np.r_[0, 1 - (spans[1:] * spans[:-1]).sum(1)]

    z = lambda a: (a - a.mean()) / (a.std() or 1)
    score = z(bass) + z(change)
    idx = np.arange(len(t))
    by_phase = np.array([score[idx % meter == p].mean() for p in range(meter)])
    order = np.argsort(by_phase)[::-1]
    return int(order[0]), round(float(by_phase[order[0]] - by_phase[order[1]]), 3)


def detect_key(S, freqs):
    profile = chroma(S, freqs).sum(0)
    scores = [(np.corrcoef(profile, np.roll(p, r))[0, 1], r, mode)
              for r in range(12) for mode, p in (('major', MAJOR), ('minor', MINOR))]
    scores.sort(reverse=True)
    best, root, mode = scores[0]
    steps = MAJOR_STEPS if mode == 'major' else MINOR_STEPS
    return {'tonic': NAMES[root], 'mode': mode, 'correlation': round(float(best), 3),
            'runnerUp': f'{NAMES[scores[1][1]]} {scores[1][2]}',
            'scalePitchClasses': [(root + s) % 12 for s in steps]}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('audio', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--cache', type=Path, help='vibe-bgm-skill rhythm.json for this exact audio (skips librosa)')
    p.add_argument('--meter', type=int, default=4, help='beats per bar (default 4)')
    p.add_argument('--downbeat-phase', type=int, help='override inferred phase: index of the first downbeat in beats')
    a = p.parse_args()

    digest = sha256(a.audio)
    y = decode(a.audio)
    duration_ms = round(len(y) / SR * 1000)
    if a.cache:
        cache_sha, bpm, beats, onsets, tonal = from_cache(a.cache)
        if cache_sha != digest:
            p.error(f'cache is for audio {cache_sha[:12]}…, not this file {digest[:12]}…')
    else:
        bpm, beats, onsets, tonal = detect_events(y)

    S, freqs, times_ms = spectrogram(y)
    phase, confidence = downbeat_phase([b['timeMs'] for b in beats], S, freqs, times_ms, duration_ms, a.meter)
    if a.downbeat_phase is not None:
        phase, confidence = a.downbeat_phase % a.meter, None
    for i, b in enumerate(beats):
        b['beatInBar'] = (i - phase) % a.meter
        b['bar'] = (i - phase) // a.meter  # bar 0 = first full bar; pickup beats get bar -1
        b['downbeat'] = b['beatInBar'] == 0

    result = {
        'schema': 'vibe-beats-v1',
        'audioSha256': digest,
        'durationMs': duration_ms,
        'bpm': round(bpm, 1),
        'meter': a.meter,
        'downbeatPhase': phase,
        'downbeatConfidence': confidence,
        'key': detect_key(S, freqs),
        'beats': beats,
        'onsets': onsets,
        'tonalOnsets': tonal,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    downbeats = [b['timeMs'] for b in beats if b['downbeat']]
    print(f"{a.out}: {result['bpm']} BPM, {len(beats)} beats, {len(downbeats)} downbeats "
          f"(phase {phase}, confidence {confidence}), key {result['key']['tonic']} {result['key']['mode']} "
          f"(r={result['key']['correlation']}, runner-up {result['key']['runnerUp']})")
    print('first downbeats (s):', ', '.join(f'{t / 1000:.3f}' for t in downbeats[:8]))


if __name__ == '__main__':
    main()
