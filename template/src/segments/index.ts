import type {FC} from 'react';
import type {Segment} from '../timeline';
import * as S01 from './S01';

/** A sound effect hit; `atMs` is absolute song time, `src` is relative to public/. */
export type Cue = {atMs: number; src: string; volume?: number};
export type SegmentModule = {Component: FC<{seg: Segment}>; sfx: Cue[]};

/** Keys must match ids in segments.json. */
export const registry: Record<string, SegmentModule> = {
	'01': S01,
};
