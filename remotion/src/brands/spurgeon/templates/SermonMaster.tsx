import React, { useEffect, useState } from "react";
import { 
	AbsoluteFill, 
	Audio, 
	staticFile, 
	useCurrentFrame,
	Img,
	delayRender,
	continueRender,
	interpolate
} from "remotion";
import { SermonMasterProps } from "../schema";
import { SubtitleLayer, Word } from "../components/SubtitleLayer";
import { AudioVisualizer } from "../components/AudioVisualizer";
import { MarketingLayer } from "../components/MarketingLayer";
import { SubscribeUpperThird } from "../components/SubscribeUpperThird";

export const SermonMaster: React.FC<SermonMasterProps> = (props) => {
	const { 
		narrationUrl, 
		bgmUrl, 
		bgmVolume, 
		backgroundImageUrl, 
		preacherImageUrl, 
		transcriptSlug,
		qrCodeUrl,
		ctaBookTitle
	} = props;

	const [words, setWords] = useState<Word[]>([]);
	const [handle] = useState(() => delayRender("Loading sermon data"));

	const cleanPath = (path: string) => path.startsWith("/") ? path.slice(1) : path;

	useEffect(() => {
		const loadData = async () => {
			try {
				// Tenta carregar a transcrição no novo padrão simplificado
				const jsonPath = transcriptSlug.includes("/") 
					? transcriptSlug 
					: `storage/transcriptions/sermons/${transcriptSlug}.json`;
				
				const response = await fetch(staticFile(cleanPath(jsonPath)));
				if (!response.ok) throw new Error(`Failed to load: ${jsonPath}`);
				
				const data = await response.json();
				if (data.words) setWords(data.words);
				continueRender(handle);
			} catch (e) {
				console.error("[SermonMaster] Fetch error:", e);
				continueRender(handle);
			}
		};
		loadData();
	}, [transcriptSlug, handle]);

	const frame = useCurrentFrame();
	const kenBurnsScale = 1 + (frame * 0.000002);
	const masterOpacity = interpolate(frame, [0, 45], [0, 1], { extrapolateRight: "clamp" });

	return (
		<AbsoluteFill style={{ backgroundColor: "#000", opacity: masterOpacity }}>

			{/* 1. FUNDO */}
			<AbsoluteFill style={{ overflow: "hidden" }}>
				<Img 
					src={staticFile(cleanPath(backgroundImageUrl))} 
					style={{ 
						width: '100%', 
						height: '100%', 
						objectFit: 'cover',
						transform: `scale(${kenBurnsScale})`,
						transformOrigin: 'center center',
						opacity: 0.85
					}} 
				/>
				<AbsoluteFill style={{
					background: "linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.5) 35%, rgba(0,0,0,0) 100%)"
				}} />
			</AbsoluteFill>

			{/* 2. SPURGEON */}
			<AbsoluteFill style={{ 
				justifyContent: 'flex-end', 
				alignItems: 'flex-end', 
				paddingBottom: '0', 
				paddingRight: '2%', 
			}}>
				<Img 
					src={staticFile(cleanPath(preacherImageUrl))} 
					style={{
						height: '65%',
						mixBlendMode: 'screen', 
						opacity: 0.9,
						filter: 'contrast(1.1) brightness(1.1)'
					}} 
				/>
			</AbsoluteFill>

			{/* 3. QR CODE MARKETING */}
			<MarketingLayer 
				qrCodeUrl={qrCodeUrl} 
			/>

			{/* 4. AUDIO */}
			<Audio src={staticFile(cleanPath(narrationUrl))} />


			{/* 5. LEGENDAS */}
			<SubtitleLayer words={words} />

			{/* 6. VISUALIZER */}
			<AbsoluteFill style={{
				justifyContent: 'flex-end',
				alignItems: 'center',
				paddingBottom: '25%',
				pointerEvents: 'none'
			}}>
				<AudioVisualizer 
					audioSrc={cleanPath(narrationUrl)} 
					numberOfSamples={128} 
					color="#ffd700" 
				/>
			</AbsoluteFill>

			{/* 7. SUBSCRIBE UPPER THIRD - Repete a cada 5 minutos */}
			<SubscribeUpperThird 
				channelName="Charles Spurgeon Treasures" 
				repeatInterval={300 * 30} 
			/>

		</AbsoluteFill>
	);
};
