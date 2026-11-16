// Example segment (bars 0–5): replace with the real topic. Shows the patterns:
// scene changes land on downbeats, local motion follows beats/onsets, captions hold for reading.
import {AbsoluteFill, Easing, interpolate} from 'remotion';
import {Caption} from '../components/Caption';
import {after, countReached, landAt, mix, pulse} from '../motion';
import type {Cue} from '.';
import {bar, startBar, beatsIn, HEIGHT, hitsIn, msToFrame, tonalOnsets, useSongFrame, WIDTH} from '../timeline';
import {theme} from '../theme';
import type {Segment} from '../timeline';

const BAR0 = startBar('01');
const B = [0, 1, 2, 3, 4, 5].map((n) => bar(BAR0 + n)); // B[k] = downbeat of the segment's k-th bar
const RING_BEATS = beatsIn(B[0], B[4]);
const WOBBLE = hitsIn(tonalOnsets, B[2], B[3], 0.5);
const SHAKE_BEATS = beatsIn(B[3], B[4]);

const SRC = {x: WIDTH * 0.28, y: HEIGHT * 0.45};
const GLASS = {x: WIDTH * 0.7, y: HEIGHT * 0.42};
const GLASS_PATH = 'M -110 -200 C -110 -40, -60 20, 0 30 C 60 20, 110 -40, 110 -200 M 0 30 L 0 190 M -80 200 L 80 200';
const SHARDS = [-150, -105, -60, -15, 30, 75, 120, 165].map((deg, i) => ({deg, dist: 260 + (i % 3) * 90, spin: (i % 2 ? 1 : -1) * 200}));

export const sfx: Cue[] = [
	{atMs: B[0], src: 'sfx/kick.wav', volume: 0.6},
	{atMs: B[2], src: 'sfx/bell-1.wav', volume: 0.5},
	{atMs: B[3], src: 'sfx/pluck-5.wav'},
	{atMs: B[3], src: 'sfx/kick.wav', volume: 0.6},
	{atMs: B[4], src: 'sfx/shatter.wav', volume: 0.6},
	{atMs: B[4], src: 'sfx/tick.wav'},
];

export const Component: React.FC<{seg: Segment}> = () => {
	const f = useSongFrame();

	// Sound source drops in and lands on bar 0, squashing on contact.
	const drop = landAt(f, B[0], 450, Easing.in(Easing.quad));
	const squash = pulse(f, [B[0]], 220);
	const beat = pulse(f, RING_BEATS, 300);

	// Glass outline finishes drawing exactly on bar 2.
	const draw = landAt(f, B[2], 900, Easing.inOut(Easing.cubic));
	// Bar 3→4: shake grows with every beat; tonal onsets add small wobbles before that.
	const shake = countReached(f, SHAKE_BEATS) * 3 * (0.4 + pulse(f, SHAKE_BEATS, 400)) + 4 * pulse(f, WOBBLE, 200);
	const shatter = after(f, B[4], 1400);
	const broken = f >= msToFrame(B[4]);
	const keyword = landAt(f, B[3], 350, Easing.out(Easing.back(1.8)));
	const keywordOut = after(f, B[4], 300);

	return (
		<AbsoluteFill style={{fontFamily: theme.font}}>
			<svg width={WIDTH} height={HEIGHT}>
				{/* Rings: one per beat, travelling from source toward the glass. */}
				{RING_BEATS.map((t) => {
					const age = after(f, t, 1600, Easing.linear);
					if (age <= 0 || age >= 1 || broken) return null;
					return (
						<circle key={t} cx={SRC.x} cy={SRC.y} r={80 + age * (GLASS.x - SRC.x)} fill="none"
							stroke={theme.accent} strokeWidth={6 * (1 - age)} opacity={1 - age} />
					);
				})}
				<g transform={`translate(${SRC.x} ${mix(-200, SRC.y, drop)}) scale(${1 + 0.18 * squash + 0.06 * beat} ${1 - 0.18 * squash + 0.06 * beat})`}>
					<circle r={80} fill={theme.accent} />
					<circle r={34} fill={theme.bg} />
				</g>
				{!broken ? (
					<g transform={`translate(${GLASS.x + Math.sin(f * 2.1) * shake} ${GLASS.y}) scale(1.4)`}>
						<path d={GLASS_PATH} pathLength={1} fill="none" stroke={theme.fg} strokeWidth={6}
							strokeLinecap="round" strokeDasharray={1} strokeDashoffset={1 - draw} />
					</g>
				) : (
					SHARDS.map((s) => {
						const rad = (s.deg * Math.PI) / 180;
						const fall = shatter * shatter * 300;
						return (
							<polygon key={s.deg} points="-30,-20 34,-6 -8,30" fill="none" stroke={theme.fg} strokeWidth={5}
								opacity={1 - shatter}
								transform={`translate(${GLASS.x + Math.cos(rad) * s.dist * shatter} ${GLASS.y - 120 + Math.sin(rad) * s.dist * shatter + fall}) rotate(${s.spin * shatter})`} />
						);
					})
				)}
			</svg>
			<div style={{
				position: 'absolute', left: 0, right: 0, top: HEIGHT * 0.06, textAlign: 'center',
				fontSize: 200, fontWeight: 900, color: theme.accent,
				opacity: keyword * (1 - keywordOut),
				transform: `scale(${interpolate(keyword, [0, 1], [0.6, 1]) * (1 + 0.3 * keywordOut)})`,
			}}>
				共振
			</div>
			<Caption frame={f} text="声音，是空气在【振动】" atMs={B[0]} untilMs={B[2]} />
			<Caption frame={f} text="玻璃也有自己的【固有频率】" atMs={B[2]} untilMs={B[3]} />
			<Caption frame={f} text="频率对上，振动就会【叠加】" atMs={B[3]} untilMs={B[4]} />
			<Caption frame={f} text="振幅越过极限 —— 【碎】" atMs={B[4]} untilMs={B[5]} />
		</AbsoluteFill>
	);
};
