import {createContext, useContext} from 'react';
import {useCurrentFrame} from 'remotion';
import beatsData from '../public/beats.json';
import project from './project.json';
import segmentsData from './segments.json';

export const {width: WIDTH, height: HEIGHT, fps: FPS} = project;
export const DURATION_MS = beatsData.durationMs;

type Hit = {timeMs: number; strength: number};
export const beats = beatsData.beats;
export const onsets: Hit[] = beatsData.onsets;
export const tonalOnsets: Hit[] = beatsData.tonalOnsets;
/** downbeats[n] = ms of bar n's first beat (bar 0 = first full bar). */
export const downbeats = beats.filter((b) => b.downbeat).map((b) => b.timeMs);

export const msToFrame = (ms: number) => Math.round((ms / 1000) * FPS);

/** ms of bar `n`, beat `beatInBar` (0-based). Bars past the song's end clamp to the end. */
export const bar = (n: number, beatInBar = 0): number => {
	const b = beats.find((x) => x.bar === n && x.beatInBar === beatInBar);
	return b ? b.timeMs : DURATION_MS;
};

/**
 * First bar of segment `id` (from segments.json). Segment files write their bars relative to it,
 * so a segment can be moved, or others cut, by editing segments.json alone.
 */
export const startBar = (id: string) => {
	const s = segmentsData.find((x) => x.id === id);
	if (!s) throw new Error(`segment "${id}" is not in segments.json`);
	return s.fromBar;
};

export type Segment = {id: string; fromBar: number; toBar: number; startMs: number; endMs: number};
export const segments: Segment[] = segmentsData.map((s) => ({
	...s,
	// The first segment also owns the pickup before bar 0, so the video starts with the music.
	startMs: s.fromBar === 0 ? 0 : bar(s.fromBar),
	endMs: bar(s.toBar),
}));

/** Hits within [fromMs, toMs), optionally only those at least `minStrength`. */
export const hitsIn = (list: Hit[], fromMs: number, toMs: number, minStrength = 0) =>
	list.filter((h) => h.timeMs >= fromMs && h.timeMs < toMs && h.strength >= minStrength).map((h) => h.timeMs);

export const beatsIn = (fromMs: number, toMs: number) =>
	beats.filter((b) => b.timeMs >= fromMs && b.timeMs < toMs).map((b) => b.timeMs);

/** Absolute song frame of the segment being rendered; set by Main around each segment. */
export const SegmentStart = createContext(0);

/** Current absolute frame in the song (music is the only clock). */
export const useSongFrame = () => useCurrentFrame() + useContext(SegmentStart);
