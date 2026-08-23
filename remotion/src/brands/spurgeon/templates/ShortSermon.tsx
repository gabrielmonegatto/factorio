import React, { useMemo } from "react";
import {
	AbsoluteFill,
	Audio as RemotionAudio,
	Img,
	Video,
	interpolate,
	useCurrentFrame,
	useVideoConfig,
} from "remotion";
import { resolveAsset } from "../../../core/library/resolveAsset";

/**
 * SHORT SERMON — composição 9:16 da fábrica de shorts (F4).
 *
 * Recebe um CLIPE já minerado (mine_clips.py): áudio cortado do sermão master
 * + word-level re-baseado em 0ms. Tudo vem por props, nada de fetch.
 *
 * Estrutura (12_FABRICA_SHORTS.md):
 *   - hook card nos primeiros ~2.5s (texto do minerador, Georgia, alto contraste)
 *   - legenda karaokê palavra a palavra, 3-4 palavras por linha, centro da tela
 *   - visual do canal: catedral + gradiente + vinheta (mesma identidade do longo)
 *   - fundo estático → o loop fecha sozinho (fim emenda no começo)
 */

export interface ShortWord {
	text: string;
	start: number; // ms, re-baseado no início do clipe
	end: number;
}

export interface ShortSermonProps {
	audioUrl: string;
	words: ShortWord[];
	hookText: string;
	backgroundImageUrl?: string;
	preacherImageUrl?: string;
	attribution?: string;
	/** vídeo de retenção (loop, mudo) na faixa superior; sem ele, layout full-bleed */
	anchorVideoUrl?: string;
	/**
	 * LINHA DO TEMPO DE CENAS: a âncora TROCA conforme a fala avança.
	 * Cada corte cai numa fronteira de frase, escolhida por `casar_ancora.py`
	 * a partir do tema do trecho. Aceita imagem (com push-in lento) ou vídeo.
	 */
	anchorShots?: {
		start: number;   // ms, relativo ao início do clipe
		end: number;
		src: string;
		kind?: "image" | "video";
		nome?: string;   // só pra depuração
	}[];
	/** trilha de fundo. Volume MUITO baixo de propósito: a voz é o produto. */
	bgmUrl?: string;
	bgmVolume?: number;
}

const HOOK_SECONDS = 2.5;
const MAX_WORDS_PER_GROUP = 4;

/** Agrupa as palavras em blocos de 3-4 (quebra antes em pontuação forte). */
const buildGroups = (words: ShortWord[]) => {
	const groups: ShortWord[][] = [];
	let cur: ShortWord[] = [];
	for (const w of words) {
		cur.push(w);
		const punct = /[.,;:!?…—][\"')\]]?$/.test(w.text);
		if (cur.length >= MAX_WORDS_PER_GROUP || (punct && cur.length >= 2)) {
			groups.push(cur);
			cur = [];
		}
	}
	if (cur.length) groups.push(cur);
	return groups;
};

export const ShortSermon: React.FC<ShortSermonProps> = ({
	audioUrl,
	words,
	hookText,
	backgroundImageUrl = "images/cathedral_bg_cf_3.png",
	preacherImageUrl = "images/spurgeon_bust_cf_1.png",
	attribution = "CHARLES SPURGEON",
	anchorVideoUrl,
	anchorShots,
	bgmUrl,
	bgmVolume = 0.07,
}) => {
	const frame = useCurrentFrame();
	const { fps, durationInFrames } = useVideoConfig();
	const tMs = (frame / fps) * 1000;

	const temAncora = Boolean((anchorShots && anchorShots.length) || anchorVideoUrl);
	const groups = useMemo(() => buildGroups(words || []), [words]);
	const active = groups.find((g) => tMs >= g[0].start && tMs <= g[g.length - 1].end + 250);

	const hookOpacity = interpolate(
		frame,
		[0, 8, HOOK_SECONDS * fps - 12, HOOK_SECONDS * fps],
		[0, 1, 1, 0],
		{ extrapolateLeft: "clamp", extrapolateRight: "clamp" },
	);
	// respiro final: legenda some, sobra só o fundo — o loop emenda limpo
	const endFade = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});

	return (
		<AbsoluteFill style={{ backgroundColor: "#050505" }}>
			{/* fundo do canal: catedral escura + gradiente */}
			<AbsoluteFill style={{ overflow: "hidden" }}>
				<Img
					src={resolveAsset(backgroundImageUrl)}
					style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.35 }}
				/>
				<AbsoluteFill
					style={{
						background:
							"linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.55) 40%, rgba(0,0,0,0.75) 100%)",
					}}
				/>
			</AbsoluteFill>

			{/* ÂNCORA VISUAL: faixa superior. Uma cena fixa, ou a linha do tempo
			    que troca com a fala (anchorShots vence anchorVideoUrl). */}
			{temAncora && (
				<div
					style={{
						position: "absolute",
						top: 0,
						left: 0,
						right: 0,
						height: "42%",
						overflow: "hidden",
						backgroundColor: "#050505",
					}}
				>
					{anchorShots && anchorShots.length > 0
						? anchorShots.map((shot, i) => {
								// crossfade nas pontas: corte seco em cena escura pisca feio
								const fade = 400;
								const op = interpolate(
									tMs,
									[shot.start - fade, shot.start, shot.end - fade, shot.end],
									[0, 1, 1, 0],
									{ extrapolateLeft: "clamp", extrapolateRight: "clamp" },
								);
								if (op <= 0.001) return null;
								// push-in lento: dá vida ao still sem competir com a palavra
								const prog = (tMs - shot.start) / Math.max(1, shot.end - shot.start);
								const escala = 1.04 + 0.06 * Math.min(1, Math.max(0, prog));
								const comum = {
									width: "100%",
									height: "100%",
									objectFit: "cover" as const,
									transform: `scale(${escala})`,
								};
								return (
									<div key={`${shot.src}-${i}`} style={{ position: "absolute", inset: 0, opacity: op }}>
										{shot.kind === "video" ? (
											<Video src={resolveAsset(shot.src)} loop muted style={comum} />
										) : (
											<Img src={resolveAsset(shot.src)} style={comum} />
										)}
									</div>
								);
						  })
						: anchorVideoUrl && (
								<Video
									src={resolveAsset(anchorVideoUrl)}
									loop
									muted
									style={{ width: "100%", height: "100%", objectFit: "cover" }}
								/>
						  )}
					{/* fusão da âncora com o fundo escuro */}
					<div
						style={{
							position: "absolute",
							inset: 0,
							background:
								"linear-gradient(to bottom, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 70%, rgba(5,5,5,1) 100%)",
						}}
					/>
				</div>
			)}

			{/* busto do Spurgeon, discreto, base da tela (identidade do longo) */}
			<AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
				<Img
					src={resolveAsset(preacherImageUrl)}
					style={{
						height: temAncora ? "30%" : "38%",
						mixBlendMode: "screen",
						opacity: temAncora ? 0.65 : 0.5,
						filter: "contrast(1.1) brightness(1.05)",
					}}
				/>
			</AbsoluteFill>

			<RemotionAudio src={resolveAsset(audioUrl)} />

			{/* TRILHA: entra e sai em fade pra não ter estalo no loop do short.
			    O volume default é 0.07 porque no short a voz compete com o feed:
			    trilha alta rouba inteligibilidade, que é o único ativo aqui. */}
			{bgmUrl && (
				<RemotionAudio
					src={resolveAsset(bgmUrl)}
					loop
					volume={(f) =>
						bgmVolume *
						interpolate(
							f,
							[0, fps * 1.2, durationInFrames - fps * 1.5, durationInFrames],
							[0, 1, 1, 0],
							{ extrapolateLeft: "clamp", extrapolateRight: "clamp" },
						)
					}
				/>
			)}

			{/* HOOK CARD — primeiros 2.5s */}
			<AbsoluteFill
				style={{ justifyContent: "center", alignItems: "center", opacity: hookOpacity }}
			>
				<div
					style={{
						margin: "0 70px",
						padding: "50px 60px",
						textAlign: "center",
						borderTop: "3px solid rgba(212,175,55,0.9)",
						borderBottom: "3px solid rgba(212,175,55,0.9)",
						background: "rgba(0,0,0,0.55)",
					}}
				>
					<div
						style={{
							fontFamily: "Georgia, serif",
							fontWeight: 700,
							fontSize: 92,
							lineHeight: 1.15,
							color: "#fff",
							textTransform: "uppercase",
							textShadow: "0 8px 30px rgba(0,0,0,0.9)",
						}}
					>
						{hookText}
					</div>
				</div>
			</AbsoluteFill>

			{/* LEGENDA KARAOKÊ — palavra a palavra (faixa do meio quando tem âncora) */}
			<div
				style={{
					position: "absolute",
					top: temAncora ? "42%" : 0,
					bottom: temAncora ? "28%" : 0,
					left: 0,
					right: 0,
					display: "flex",
					justifyContent: "center",
					alignItems: "center",
					opacity: (1 - hookOpacity) * endFade,
				}}
			>
				<div
					style={{
						margin: "0 60px",
						display: "flex",
						flexWrap: "wrap",
						justifyContent: "center",
						columnGap: 28,
						rowGap: 10,
						fontFamily: "Georgia, serif",
						fontWeight: 700,
						fontSize: 84,
						lineHeight: 1.25,
						textTransform: "uppercase",
						textShadow: "0 6px 24px rgba(0,0,0,0.95), 0 2px 6px rgba(0,0,0,0.9)",
					}}
				>
					{active?.map((w, i) => {
						const on = tMs >= w.start;
						const current = on && tMs <= w.end + 150;
						return (
							<span
								key={`${w.start}-${i}`}
								style={{
									color: on ? "#FFD75E" : "#FFFFFF",
									textShadow: current
										? "0 0 30px rgba(255,215,94,0.55), 0 6px 24px rgba(0,0,0,0.95)"
										: undefined,
								}}
							>
								{w.text}
							</span>
						);
					})}
				</div>
			</div>

			{/* atribuição fixa */}
			<AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
				<div
					style={{
						marginBottom: 140,
						fontFamily: "Georgia, serif",
						fontSize: 34,
						letterSpacing: 6,
						color: "rgba(212,175,55,0.85)",
						textShadow: "0 2px 10px rgba(0,0,0,0.9)",
					}}
				>
					{attribution}
				</div>
			</AbsoluteFill>

			{/* vinheta */}
			<div
				style={{
					position: "absolute",
					inset: 0,
					background: "radial-gradient(circle at center, transparent 35%, rgba(0,0,0,0.75) 100%)",
					pointerEvents: "none",
				}}
			/>
		</AbsoluteFill>
	);
};

export const calcShortSermon = async ({ props }: { props: any }) => {
	const { getAudioDurationInSeconds } = await import("@remotion/media-utils");
	const FPS = 30;
	let frames = 45 * FPS;
	try {
		frames = Math.ceil((await getAudioDurationInSeconds(resolveAsset(props.audioUrl))) * FPS) + 10;
	} catch (e) {
		console.warn("[calcShortSermon] não mediu o áudio — usando fallback 45s", e);
	}
	return { durationInFrames: frames, fps: FPS, props };
};
