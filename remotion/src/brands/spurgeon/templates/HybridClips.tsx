import { AbsoluteFill, Audio, Img, staticFile } from "remotion";
import { getAudioDurationInSeconds } from "@remotion/media-utils";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { SpurgeonHook } from "./SpurgeonHook";
import { SpurgeonCTA } from "./SpurgeonCTA";
import { YouTubeEndScreen } from "./YouTubeEndScreen";
import { MarketingLayer } from "../components/MarketingLayer";
import { SermonMasterProps } from "../schema";
import { resolveAsset } from "../../../core/library/resolveAsset";

/**
 * HYBRID CLIPS — pipeline de custo otimizado.
 *
 * O corpo do sermão (95% do vídeo, ~35min estático) NÃO renderiza aqui — vai pro ffmpeg
 * (imagem-base + legenda .ass + áudio), que é ~10x mais barato.
 *
 * O Remotion renderiza SÓ os pedaços curtos animados, agrupados em 2 clipes pra manter
 * os fades bonitos DENTRO do Remotion (fade de conteúdo no ffmpeg fica feio):
 *   - ClipIntro  = Hook + fade + IntroCTA        (~40s)
 *   - SermonBodyBase = 1 still da base do corpo  (vira o fundo do ffmpeg)
 *   - ClipOutro  = OutroHook + fade + OutroCTA + fade + Endscreen  (~56s)
 *
 * O concat final (ClipIntro + corpo-ffmpeg + ClipOutro) é feito no ffmpeg com fade-pra-preto.
 */

const FPS = 30;
const TRANSITION = 10; // 0.33s — mesmo do SermonProduction

const measure = async (url: string | undefined, fallback: number): Promise<number> => {
	if (!url) return fallback;
	try {
		return Math.ceil((await getAudioDurationInSeconds(resolveAsset(url))) * FPS) + 15;
	} catch {
		return fallback;
	}
};

// ─── BASE DO CORPO (still, sem legenda/áudio) — vira o fundo do ffmpeg ───
export const SermonBodyBase: React.FC<SermonMasterProps> = (props) => {
	return (
		<AbsoluteFill style={{ backgroundColor: "#000" }}>
			<AbsoluteFill style={{ overflow: "hidden" }}>
				<Img
					src={resolveAsset(props.backgroundImageUrl)}
					style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.85 }}
				/>
				<AbsoluteFill style={{
					background: "linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.5) 35%, rgba(0,0,0,0) 100%)",
				}} />
			</AbsoluteFill>
			<AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end", paddingRight: "2%" }}>
				<Img
					src={resolveAsset(props.preacherImageUrl)}
					style={{ height: "65%", mixBlendMode: "screen", opacity: 0.9, filter: "contrast(1.1) brightness(1.1)" }}
				/>
			</AbsoluteFill>
			<MarketingLayer qrCodeUrl={props.qrCodeUrl} />
		</AbsoluteFill>
	);
};

// ─── CLIP INTRO = Hook + fade + IntroCTA ───
export const ClipIntro: React.FC<SermonMasterProps> = (props) => {
	const HOOK = props.hookDurationFrames || 24 * FPS;
	const INTRO_CTA = props.introCtaDurationFrames || 16 * FPS;
	return (
		<AbsoluteFill style={{ backgroundColor: "black" }}>
			<TransitionSeries>
				<TransitionSeries.Sequence durationInFrames={HOOK}>
					<SpurgeonHook
						hookAudioUrl={props.hookAudioUrl}
						hookTranscriptSlug={props.hookTranscriptSlug}
						marketingTitle={props.marketingTitle}
					/>
				</TransitionSeries.Sequence>
				<TransitionSeries.Transition timing={linearTiming({ durationInFrames: TRANSITION })} presentation={fade()} />
				<TransitionSeries.Sequence durationInFrames={INTRO_CTA}>
					<SpurgeonCTA ctaAudioUrl={props.introCtaAudioUrl} qrCodeUrl={props.qrCodeUrl} />
				</TransitionSeries.Sequence>
			</TransitionSeries>
		</AbsoluteFill>
	);
};

export const calcClipIntro = async ({ props }: { props: any }) => {
	const hook = await measure(props.hookAudioUrl, 24 * FPS);
	const introCta = await measure(props.introCtaAudioUrl, 16 * FPS);
	return {
		durationInFrames: hook + introCta - TRANSITION,
		fps: FPS,
		props: { ...props, hookDurationFrames: hook, introCtaDurationFrames: introCta },
	};
};

// ─── CLIP OUTRO = OutroHook + fade + OutroCTA + fade + Endscreen ───
export const ClipOutro: React.FC<SermonMasterProps> = (props) => {
	const OUTRO_HOOK = props.outroHookDurationFrames || 24 * FPS;
	const OUTRO_CTA = props.outroCtaDurationFrames || 14 * FPS;
	const ENDSCREEN = 20 * FPS;
	return (
		<AbsoluteFill style={{ backgroundColor: "black" }}>
			<TransitionSeries>
				<TransitionSeries.Sequence durationInFrames={OUTRO_HOOK}>
					<SpurgeonHook
						hookAudioUrl={props.outroHookAudioUrl}
						hookTranscriptSlug={props.outroHookTranscriptSlug}
						marketingTitle="Share this Rock-Solid Hope"
						disableBgm
					/>
				</TransitionSeries.Sequence>
				<TransitionSeries.Transition timing={linearTiming({ durationInFrames: TRANSITION })} presentation={fade()} />
				<TransitionSeries.Sequence durationInFrames={OUTRO_CTA}>
					<SpurgeonCTA ctaAudioUrl={props.outroCtaAudioUrl} qrCodeUrl={props.qrCodeUrl} />
				</TransitionSeries.Sequence>
				<TransitionSeries.Transition timing={linearTiming({ durationInFrames: TRANSITION })} presentation={fade()} />
				<TransitionSeries.Sequence durationInFrames={ENDSCREEN}>
					<YouTubeEndScreen />
				</TransitionSeries.Sequence>
			</TransitionSeries>
		</AbsoluteFill>
	);
};

export const calcClipOutro = async ({ props }: { props: any }) => {
	const outroHook = await measure(props.outroHookAudioUrl, 24 * FPS);
	const outroCta = await measure(props.outroCtaAudioUrl, 14 * FPS);
	const endscreen = 20 * FPS;
	return {
		durationInFrames: outroHook + outroCta + endscreen - 2 * TRANSITION,
		fps: FPS,
		props: { ...props, outroHookDurationFrames: outroHook, outroCtaDurationFrames: outroCta },
	};
};
