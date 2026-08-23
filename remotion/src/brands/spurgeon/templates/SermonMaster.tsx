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
import { MarketingLayer } from "../components/MarketingLayer";
import { SubscribeUpperThird } from "../components/SubscribeUpperThird";
import { resolveAsset } from "../../../core/library/resolveAsset";

export const SermonMaster: React.FC<SermonMasterProps> = (props) => {
	const { 
		narrationUrl, 
		bgmUrl, 
		bgmVolume, 
		backgroundImageUrl, 
		preacherImageUrl, 
		transcriptSlug,
		qrCodeUrl,
		ctaBookTitle,
		channelName
	} = props;

	const [words, setWords] = useState<Word[]>([]);
	const [handle] = useState(() => delayRender("Loading sermon data"));

	useEffect(() => {
		const loadData = async () => {
			try {
				// transcriptSlug pode ser: URL do R2 (http...), caminho local, ou slug puro
				const jsonPath = /^https?:\/\//i.test(transcriptSlug) || transcriptSlug.includes("/")
					? transcriptSlug
					: `storage/transcriptions/sermons/${transcriptSlug}.json`;

				const response = await fetch(resolveAsset(jsonPath));
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
					src={resolveAsset(backgroundImageUrl)}
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
					src={resolveAsset(preacherImageUrl)}
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
			<Audio src={resolveAsset(narrationUrl)} />


			{/* 5. LEGENDAS */}
			<SubtitleLayer words={words} />

			{/* 6. VISUALIZER — REMOVIDO: useAudioData decodificava o WAV inteiro (~35min/800MB)
			     a cada frame, estourando a memória do worker (OOM) no render contínuo.
			     Era só uma linha pontilhada quase invisível. Se quiser reintroduzir,
			     alimentar com um áudio downsampled/curto, nunca a narração completa. */}

			{/* 7. SUBSCRIBE UPPER THIRD - Repete a cada 5 minutos */}
			<SubscribeUpperThird 
				channelName={channelName || "Treasures"} 
				repeatInterval={300 * 30} 
			/>

		</AbsoluteFill>
	);
};
