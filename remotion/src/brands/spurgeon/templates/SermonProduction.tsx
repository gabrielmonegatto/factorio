import { AbsoluteFill, Audio, staticFile } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { SermonMaster } from "./SermonMaster";
import { SpurgeonHook } from "./SpurgeonHook";
import { SpurgeonCTA } from "./SpurgeonCTA";
import { YouTubeEndScreen } from "./YouTubeEndScreen";
import { SermonMasterProps } from "../schema";

/**
 * Composition wrapper V2 - Retenção de Algoritmo YouTube
 * Sequence 1: Hook Intro (20s)
 * Sequence 2: Brand CTA (14s)
 * Sequence 3: Main Sermon (Dinâmico)
 * Sequence 4: Brand CTA Reprise (14s)
 * Sequence 5: YouTube End Screen (20s)
 */
export const SermonProduction: React.FC<SermonMasterProps & { totalSermonFrames: number }> = (props) => {
	const fps = 30;
	// Duração dinâmica baseada no áudio ou fallback
	const HOOK_DURATION = props.hookDurationFrames || (20 * fps);
	const INTRO_CTA_DURATION = props.introCtaDurationFrames || (16 * fps);
	const OUTRO_HOOK_DURATION = props.outroHookDurationFrames || (28 * fps); 
	const OUTRO_CTA_DURATION = props.outroCtaDurationFrames || (14 * fps);
	const ENDSCREEN_DURATION = 20 * fps; 

	const TRANSITION_DURATION = 10; // 0.3s - Curto para não encavalar o áudio

	// Cálculo do frame exato onde o sermão começa para entrar a BGM
	const startSermonFrame = HOOK_DURATION + INTRO_CTA_DURATION - (2 * TRANSITION_DURATION);

	const cleanPath = (path: string) => path?.startsWith("/") ? path.slice(1) : path;

	return (
		<AbsoluteFill style={{ backgroundColor: "black" }}>
			{/* MÚSICA DE FUNDO GLOBAL (Começa no sermão e vai até o fim) */}
			{props.bgmUrl && (
				<Audio 
					src={staticFile(cleanPath(props.bgmUrl))} 
					volume={props.bgmVolume ?? 0.05} 
					startFrom={0}
					pauseWhenBuffering
					loop
					// Entra exatamente no início do bloco do sermão
					startInFrame={startSermonFrame} 
				/>
			)}

			<TransitionSeries>
				{/* 1. HOOK INTRO (Dynamic) */}
				<TransitionSeries.Sequence durationInFrames={HOOK_DURATION}>
					<SpurgeonHook 
						hookAudioUrl={props.hookAudioUrl} 
						hookTranscriptSlug={props.hookTranscriptSlug} 
						marketingTitle={props.marketingTitle}
					/>
				</TransitionSeries.Sequence>

				<TransitionSeries.Transition 
					timing={linearTiming({ durationInFrames: TRANSITION_DURATION })} 
					presentation={fade()} 
				/>

				{/* 2. INTRO CTA (Fixed) */}
				<TransitionSeries.Sequence durationInFrames={INTRO_CTA_DURATION}>
					<SpurgeonCTA ctaAudioUrl={props.introCtaAudioUrl} />
				</TransitionSeries.Sequence>

				<TransitionSeries.Transition 
					timing={linearTiming({ durationInFrames: TRANSITION_DURATION })} 
					presentation={fade()} 
				/>

				{/* 3. CORE CONTENT (Sermon) */}
				<TransitionSeries.Sequence durationInFrames={props.totalSermonFrames}>
					<SermonMaster {...props} />
				</TransitionSeries.Sequence>

				<TransitionSeries.Transition 
					timing={linearTiming({ durationInFrames: TRANSITION_DURATION })} 
					presentation={fade()} 
				/>

				{/* 4. OUTRO HOOK (Dynamic Reflection) */}
				<TransitionSeries.Sequence durationInFrames={OUTRO_HOOK_DURATION}>
					<SpurgeonHook 
						hookAudioUrl={props.outroHookAudioUrl} 
						hookTranscriptSlug={props.outroHookTranscriptSlug} 
						marketingTitle="Share this Rock-Solid Hope"
						disableBgm
					/>
				</TransitionSeries.Sequence>

				<TransitionSeries.Transition 
					timing={linearTiming({ durationInFrames: TRANSITION_DURATION })} 
					presentation={fade()} 
				/>

				{/* 5. OUTRO CTA (Fixed Subscribe Call over Background) */}
				<TransitionSeries.Sequence durationInFrames={OUTRO_CTA_DURATION}>
					<SpurgeonCTA ctaAudioUrl={props.outroCtaAudioUrl} />
				</TransitionSeries.Sequence>

				<TransitionSeries.Transition 
					timing={linearTiming({ durationInFrames: TRANSITION_DURATION })} 
					presentation={fade()} 
				/>

				{/* 6. YOUTUBE END SCREEN */}
				<TransitionSeries.Sequence durationInFrames={ENDSCREEN_DURATION}>
					<YouTubeEndScreen />
				</TransitionSeries.Sequence>
			</TransitionSeries>
		</AbsoluteFill>
	);
};
