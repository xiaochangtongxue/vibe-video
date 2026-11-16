import {AbsoluteFill, Audio, interpolate, Sequence, staticFile} from 'remotion';
import {registry} from './segments';
import {DURATION_MS, FPS, msToFrame, SegmentStart, segments} from './timeline';
import {theme} from './theme';
import project from './project.json';

const moduleFor = (id: string) => {
	const mod = registry[id];
	if (!mod) throw new Error(`segments.json has segment "${id}" but segments/index.ts does not register it`);
	return mod;
};

const MUSIC_VOLUME = 0.6;
const END_MS = segments[segments.length - 1].endMs;
// A video that stops before the track ends fades the music out instead of cutting it mid-phrase.
const FADE_FRAMES = END_MS < DURATION_MS - 500 ? Math.round(FPS * 1.5) : 0;
const musicVolume = (frame: number) =>
	FADE_FRAMES === 0
		? MUSIC_VOLUME
		: MUSIC_VOLUME * interpolate(frame, [msToFrame(END_MS) - FADE_FRAMES, msToFrame(END_MS)], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

/** The whole song timeline. Segment compositions render a window of it, so timing never diverges. */
export const Timeline: React.FC = () => (
	<AbsoluteFill style={{background: theme.bg}}>
		{/* Mastered tracks peak near 0 dBFS; leave ~4.4 dB headroom so SFX on top don't clip. */}
		<Audio src={staticFile(project.music)} volume={musicVolume} />
		{segments.map((seg) => {
			const {Component} = moduleFor(seg.id);
			const from = msToFrame(seg.startMs);
			return (
				<Sequence key={seg.id} name={`seg-${seg.id}`} from={from} durationInFrames={msToFrame(seg.endMs) - from}>
					<SegmentStart.Provider value={from}>
						<Component seg={seg} />
					</SegmentStart.Provider>
				</Sequence>
			);
		})}
		{segments.flatMap((seg) =>
			moduleFor(seg.id).sfx.map((cue, i) => (
				<Sequence key={`${seg.id}-${i}`} name={`sfx ${cue.src}`} from={msToFrame(cue.atMs)} layout="none">
					<Audio src={staticFile(cue.src)} volume={cue.volume ?? 0.6} />
				</Sequence>
			)),
		)}
	</AbsoluteFill>
);

export const SegmentCut: React.FC<{startFrame: number}> = ({startFrame}) => (
	<Sequence from={-startFrame}>
		<Timeline />
	</Sequence>
);
