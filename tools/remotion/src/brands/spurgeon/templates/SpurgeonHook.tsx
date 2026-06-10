import React, { useEffect, useState } from "react";
import { AbsoluteFill, Audio as RemotionAudio, Img, staticFile, useVideoConfig, delayRender, continueRender } from "remotion";
import { SubtitleLayer, Word } from "../components/SubtitleLayer";

interface HookProps {
	hookAudioUrl?: string;
	hookTranscriptSlug?: string;
	marketingTitle?: string;
	disableBgm?: boolean;
}

export const SpurgeonHook: React.FC<HookProps> = ({
	hookAudioUrl,
	hookTranscriptSlug,
	marketingTitle,
	disableBgm,
}) => {
	const [words, setWords] = useState<Word[]>([]);
	const [handle] = useState(() => delayRender("Loading Hook Data"));

	useEffect(() => {
		const loadData = async () => {
			if (!hookTranscriptSlug) {
				continueRender(handle);
				return;
			}
			try {
				const jsonPath = hookTranscriptSlug.replace(/^\/?/, '');
				
				const response = await fetch(staticFile(jsonPath));
				if (!response.ok) throw new Error(`Failed to load: ${jsonPath}`);
				
				const data = await response.json();
				if (data.words) setWords(data.words);
				continueRender(handle);
			} catch (e) {
				console.error("[SpurgeonHook] Fetch error:", e);
				continueRender(handle);
			}
		};
		loadData();
	}, [hookTranscriptSlug, handle]);

	const { fps } = useVideoConfig();

	return (
		<AbsoluteFill style={{ backgroundColor: "#050505" }}>
			{/* Dramatic B&W to Color Background */}
			<AbsoluteFill>
				<Img 
					src={staticFile("images/cathedral_bg_cf_1.png")}
					style={{
						width: "100%",
						height: "100%",
						objectFit: "cover",
						opacity: 0.15,
						filter: "grayscale(100%) blur(2px)",
					}}
				/>
				<div style={{ position: "absolute", inset: 0, backgroundColor: "rgba(0,0,0,0.4)" }} />
			</AbsoluteFill>

			{/* Audio Track for the Hook (Kokoro) */}
			{hookAudioUrl && <RemotionAudio src={staticFile(hookAudioUrl.replace(/^\/?/, ''))} />}

			{/* BGM low volume for dramatic effect */}
			{!disableBgm && <RemotionAudio src={staticFile("storage/audio/library/premium_frequencial/432hz_01.mp3")} volume={0.05} />}

			{/* Visual Hook Layout: Big centered text */}
			<AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
				{hookTranscriptSlug && words.length > 0 ? (
					<SubtitleLayer words={words} style={{ position: "relative", bottom: "auto", left: "auto" }} />
				) : (
					<div style={{ padding: "0 150px", textAlign: "center" }}>
						<h2 style={{ 
							fontFamily: "Georgia, serif", 
							fontSize: 64, 
							color: "#fff", 
							fontStyle: "italic",
							textShadow: "0 10px 30px rgba(0,0,0,0.8)",
							lineHeight: 1.2
						}}>
							{marketingTitle || "Every promise of Scripture is a writing of God..."}
						</h2>
					</div>
				)}
			</AbsoluteFill>

			{/* Vignette Overlay */}
			<div
				style={{
					position: "absolute",
					inset: 0,
					background: "radial-gradient(circle at center, transparent 30%, rgba(0,0,0,0.8) 100%)",
				}}
			/>
		</AbsoluteFill>
	);
};
