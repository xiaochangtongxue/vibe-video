import {Composition} from 'remotion';
import {SegmentCut, Timeline} from './Main';
import {FPS, HEIGHT, msToFrame, segments, WIDTH} from './timeline';

export const RemotionRoot: React.FC = () => {
	const size = {fps: FPS, width: WIDTH, height: HEIGHT};
	const end = msToFrame(segments[segments.length - 1].endMs);
	return (
		<>
			<Composition id="Main" component={Timeline} durationInFrames={end} {...size} />
			{segments.map((seg) => {
				const startFrame = msToFrame(seg.startMs);
				return (
					<Composition
						key={seg.id}
						id={`seg-${seg.id}`}
						component={SegmentCut}
						defaultProps={{startFrame}}
						durationInFrames={msToFrame(seg.endMs) - startFrame}
						{...size}
					/>
				);
			})}
		</>
	);
};
