import React, { useEffect, useState } from "react";
import { 
	AbsoluteFill, 
	Audio, 
	staticFile, 
	useVideoConfig
} from "remotion";
import { SubtitleLayer, Word } from "../components/SubtitleLayer";

interface SermonPreviewProps {
	slug: string;
	mode: "vertical" | "landscape";
}

export const SermonPreview: React.FC<SermonPreviewProps> = ({ slug, mode }) => {
	const [words, setWords] = useState<Word[]>([]);

	useEffect(() => {
		fetch(staticFile(`/storage/transcriptions/sermons/${slug}.json`))
			.then((r) => r.json())
			.then((data) => {
				if (data.words) setWords(data.words);
			})
			.catch((e) => console.error("Failed to load transcription", e));
	}, [slug]);

	const audioUrl = staticFile(`/storage/audio/sermons/${slug}.wav`);

	return (
		<AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
			<div style={{
				position: "absolute",
				width: "100%",
				height: "100%",
				background: mode === "vertical" 
					? "radial-gradient(circle, #1e293b 0%, #0f172a 100%)"
					: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
			}} />

			<Audio src={audioUrl} />

			<SubtitleLayer words={words} />

			<div style={{
				position: "absolute",
				top: 40,
				left: 0,
				width: "100%",
				textAlign: "center",
				color: "rgba(255,255,255,0.3)",
				fontFamily: "Inter, sans-serif",
				fontSize: 24,
				letterSpacing: 2
			}}>
				SPURGEON PROD / VERIFICAÇÃO 1.0
			</div>
		</AbsoluteFill>
	);
};
