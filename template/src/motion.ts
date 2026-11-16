import {Easing, interpolate} from 'remotion';
import {FPS, msToFrame} from './timeline';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/**
 * 0→1 that starts `leadMs` early and lands exactly on the frame of `atMs`:
 * the motion prepares before the beat and makes contact on it.
 */
export const landAt = (frame: number, atMs: number, leadMs = 400, easing = Easing.out(Easing.cubic)) => {
	const end = msToFrame(atMs);
	const start = Math.min(end - 1, msToFrame(atMs - leadMs));
	return interpolate(frame, [start, end], [0, 1], {...clamp, easing});
};

/** 0→1 starting on `atMs` (for exits and follow-through after a hit). */
export const after = (frame: number, atMs: number, durMs = 300, easing = Easing.out(Easing.cubic)) => {
	const start = msToFrame(atMs);
	return interpolate(frame, [start, start + Math.max(1, (durMs / 1000) * FPS)], [0, 1], {...clamp, easing});
};

/** Decaying impulse from the most recent hit: 1 on the hit frame, ~0 after `decayMs`. */
export const pulse = (frame: number, hitsMs: number[], decayMs = 250) => {
	let last = -Infinity;
	for (const h of hitsMs) {
		const f = msToFrame(h);
		if (f <= frame && f > last) last = f;
	}
	if (last === -Infinity) return 0;
	return Math.exp((-(frame - last) / FPS) * 1000 * (4.6 / decayMs)); // e^-4.6 ≈ 1%
};

/** Number of hits reached so far (drives counters, staggered reveals). */
export const countReached = (frame: number, hitsMs: number[]) => hitsMs.filter((h) => msToFrame(h) <= frame).length;

export const mix = (a: number, b: number, t: number) => a + (b - a) * t;
