import {Easing} from 'remotion';
import {after, landAt} from '../motion';
import {HEIGHT} from '../timeline';
import {theme} from '../theme';

/** One short sentence. Wrap keywords in 【】 to highlight them. Settles ~0.25 s after `atMs`. */
export const Caption: React.FC<{frame: number; text: string; atMs: number; untilMs: number}> = ({frame, text, atMs, untilMs}) => {
	const enter = landAt(frame, atMs + 250, 250);
	const exit = after(frame, untilMs - 150, 150, Easing.in(Easing.cubic));
	const opacity = enter * (1 - exit);
	if (opacity <= 0) return null;
	const parts = text.split(/【|】/);
	return (
		<div
			style={{
				position: 'absolute',
				left: 0,
				right: 0,
				bottom: HEIGHT * 0.1,
				textAlign: 'center',
				fontFamily: theme.font,
				fontSize: 64,
				fontWeight: 700,
				color: theme.fg,
				opacity,
				transform: `translateY(${(1 - enter) * 24}px)`,
			}}
		>
			{parts.map((p, i) => (
				<span key={i} style={i % 2 ? {color: theme.accent} : undefined}>
					{p}
				</span>
			))}
		</div>
	);
};
