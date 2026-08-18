import { Composition, getInputProps } from "remotion";
import { getAudioDurationInSeconds } from "@remotion/media-utils";
import { resolveAsset } from "./core/library/resolveAsset";
import { BibleNarration } from "./brands/mana-diario/templates/BibleNarration";
import { LetterboxDemo } from "./brands/mana-diario/templates/LetterboxDemo";
import { FilmGrainDemo } from "./brands/mana-diario/templates/FilmGrainDemo";
import { sampleBibleEpisode, EpisodeProps } from "./data/sampleEpisode";
import { salmo1PortraitData, salmo1LandscapeData } from "./data/salmo1";

// TREASURES TEMPLATES (Unused - Commented out to prevent build failures)
// import { OptionA_Minimalista } from "./brands/treasures/templates/OptionA_Minimalista";
// import { OptionB_Cinematic } from "./brands/treasures/templates/OptionB_Cinematic";
// import { OptionC_Vintage } from "./brands/treasures/templates/OptionC_Vintage";
// import { OptionD_ModernBold } from "./brands/treasures/templates/OptionD_ModernBold";

// CORE COMPONENTS
import { YouTubeLowerThird } from "./core/components/YouTubeLowerThird";
import { SermonPreview } from "./brands/spurgeon/templates/SermonPreview";
import { SermonMaster } from "./brands/spurgeon/templates/SermonMaster";
import { SermonProduction } from "./brands/spurgeon/templates/SermonProduction";
import { sermonMasterSchema } from "./brands/spurgeon/schema";
import { QRCodePreview } from "./brands/spurgeon/templates/QRCodePreview";
import { CTAPreview } from "./brands/spurgeon/templates/CTAPreview";
import { SpurgeonCTA } from "./brands/spurgeon/templates/SpurgeonCTA";
import { SubscribePreview } from "./brands/spurgeon/templates/SubscribePreview";
import { SpurgeonHook } from "./brands/spurgeon/templates/SpurgeonHook";
import { SpurgeonBrandAd } from "./brands/spurgeon/templates/SpurgeonBrandAd";
import { YouTubeEndScreen } from "./brands/spurgeon/templates/YouTubeEndScreen";
import { SermonBodyBase, ClipIntro, calcClipIntro, ClipOutro, calcClipOutro, Thumbnail } from "./brands/spurgeon/templates/HybridClips";
import { ShortSermon, calcShortSermon } from "./brands/spurgeon/templates/ShortSermon";

const FPS = 30;
const TRANSITION_FRAMES = 10; // deve casar com SermonProduction
const SEGMENT_PAD = 15;       // 0.5s de respiro por segmento de marketing
const SERMON_TAIL = 90;       // 3s de respiro no fim do sermão
const ENDSCREEN_FRAMES = 20 * FPS;

// Mede a duração de um áudio (segundos → frames). Se falhar/ausente, usa o fallback.
const measureFrames = async (url: string | undefined, fallbackFrames: number, pad = 0): Promise<number> => {
	if (!url) return fallbackFrames;
	try {
		const sec = await getAudioDurationInSeconds(resolveAsset(url));
		return Math.ceil(sec * FPS) + pad;
	} catch (e) {
		console.warn(`[calculateMetadata] falha ao medir "${url}" — usando fallback ${fallbackFrames}f`, e);
		return fallbackFrames;
	}
};

/**
 * calcula a duração REAL do vídeo a partir dos áudios (mata o bug do vídeo de 3h,
 * que vinha de durationInFrames escrito na mão). Injeta as durações medidas de volta
 * nos props pra que SermonProduction use exatamente os mesmos números.
 */
const calcSermonMetadata = async ({ props }: { props: any }) => {
	const hook = await measureFrames(props.hookAudioUrl, 20 * FPS, SEGMENT_PAD);
	const introCta = await measureFrames(props.introCtaAudioUrl, 16 * FPS, SEGMENT_PAD);
	const sermon = await measureFrames(props.narrationUrl, 30 * 60 * FPS, SERMON_TAIL);
	const outroHook = await measureFrames(props.outroHookAudioUrl, 24 * FPS, SEGMENT_PAD);
	const outroCta = await measureFrames(props.outroCtaAudioUrl, 14 * FPS, SEGMENT_PAD);

	// 6 sequências, 5 transições sobrepostas
	const durationInFrames =
		hook + introCta + sermon + outroHook + outroCta + ENDSCREEN_FRAMES - 5 * TRANSITION_FRAMES;

	return {
		durationInFrames,
		fps: FPS,
		props: {
			...props,
			hookDurationFrames: hook,
			introCtaDurationFrames: introCta,
			totalSermonFrames: sermon,
			outroHookDurationFrames: outroHook,
			outroCtaDurationFrames: outroCta,
		},
	};
};

export const RemotionRoot: React.FC = () => {
    return (
        <>
            {/* Piloto Salmo 1 - Vertical (Reels/TikTok/Shorts) */}
            <Composition
                id="Salmo1-Portrait"
                component={BibleNarration}
                durationInFrames={salmo1PortraitData.durationInFrames}
                fps={30}
                width={1080}
                height={1920}
                defaultProps={salmo1PortraitData}
            />

            {/* Piloto Salmo 1 - Landscape (YouTube) */}
            <Composition
                id="Salmo1-Landscape"
                component={BibleNarration}
                durationInFrames={salmo1LandscapeData.durationInFrames}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={salmo1LandscapeData}
            />

            {/* Formato Original (Exemplo) */}
            <Composition
                id="BibleNarration-Sample"
                component={BibleNarration}
                durationInFrames={sampleBibleEpisode.durationInFrames}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={sampleBibleEpisode}
            />

            {/* Gerador em Massa (Recebe props via CLI) */}
            <Composition
                id="BibleNarration-Bulk"
                component={BibleNarration}
                durationInFrames={(getInputProps() as any).durationInFrames || 1800}
                fps={30}
                width={1080}
                height={1920}
                defaultProps={getInputProps() as unknown as EpisodeProps}
            />

            {/* DEMOS DE LETTERBOX (PROCEDURAL) */}
            <Composition
                id="Demo-Letterbox-Horizontal"
                component={LetterboxDemo}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ type: 'horizontal' }}
            />

            <Composition
                id="Demo-Letterbox-Vertical"
                component={LetterboxDemo}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ type: 'vertical' }}
            />

            {/* DEMOS DE FILM GRAIN (PROCEDURAL) */}
            <Composition
                id="Demo-FilmGrain-Subtle"
                component={FilmGrainDemo}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ opacity: 0.03, label: 'Grão Sutil' }}
            />

            <Composition
                id="Demo-FilmGrain-Cinematic"
                component={FilmGrainDemo}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ opacity: 0.12, label: 'Grão Cinematográfico' }}
            />

            {/* ===== TREASURES TEMPLATES (Disabled due to missing folder/files) ===== */}

            {/* ===== SERMON PREVIEWS (PRODUÇÃO) ===== */}
            <Composition
                id="Sermon-Landscape"
                component={SermonPreview as any}
                durationInFrames={18000} // ~10 minutos a 30fps
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    slug: "0001 - The Immutability of God",
                    mode: "landscape"
                }}
            />

            <Composition
                id="Sermon-Vertical"
                component={SermonPreview as any}
                durationInFrames={18000} // ~10 minutos a 30fps
                fps={30}
                width={1080}
                height={1920}
                defaultProps={{
                    slug: "0001 - The Immutability of God",
                    mode: "vertical"
                }}
            />

            {/* ===== SERMON MASTER (FASES DE DESENVOLVIMENTO) ===== */}
            <Composition
                id="Sermon-Master-Pilot"
                component={SermonMaster}
                durationInFrames={63084} // 35:02 @ 30fps
                fps={30}
                width={1920}
                height={1080}
                schema={sermonMasterSchema}
                defaultProps={{
                    narrationUrl: "/storage/audio/sermons/sermon_01.wav",
                    bgmUrl: "/storage/audio/library/worship_instrumental/worship_piano_01.mp3",
                    bgmVolume: 0.05,
                    backgroundImageUrl: "/images/cathedral_bg_cf_1.png",
                    preacherImageUrl: "/images/spurgeon_bust_cf_1.png",
                    transcriptSlug: "sermon_01",
                    sermonTitle: "The Immutability of God",
                    sermonNumber: "0001",
                    qrCodeUrl: "/images/sample_qr.png",
                    kenBurnsIntensity: "subtle",
                    subtitleStyle: "classic",
                    ctaBookTitle: "The Eternal Preacher",
                }}
            />

            {/* ===== SERMON PRODUCTION (VÍDEO COMPLETO V2) ===== */}
            <Composition
                id="Sermon-Full-Production"
                component={SermonProduction}
                durationInFrames={18000} // fallback; a duração real é calculada por calculateMetadata (mede os áudios)
                calculateMetadata={calcSermonMetadata}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    totalSermonFrames: 63084 + 90, // +3 segundos de respiro final
                    narrationUrl: "/storage/audio/sermons/sermon_01.wav",
                    bgmUrl: "/storage/audio/library/worship_instrumental/worship_piano_01.mp3",
                    bgmVolume: 0.05,
                    backgroundImageUrl: "/images/cathedral_bg_cf_1.png",
                    preacherImageUrl: "/images/spurgeon_bust_cf_1.png",
                    transcriptSlug: "sermon_01",
                    sermonTitle: "The Immutability of God",
                    sermonNumber: "0001",
                    qrCodeUrl: "/images/sample_qr.png",
                    kenBurnsIntensity: "subtle",
                    subtitleStyle: "classic",
                    ctaBookTitle: "The Eternal Preacher",
					hookAudioUrl: "/storage/audio/sermons/marketing/0001_-_the_immutability_of_god/hook.wav",
                    hookTranscriptSlug: "/storage/audio/sermons/marketing/0001_-_the_immutability_of_god/hook.json",
					hookDurationFrames: 733,
                    introCtaAudioUrl: "/storage/audio/library/marketing/spurgeon/intro_cta_fixed.wav",
                    introCtaTranscriptSlug: "/storage/audio/library/marketing/spurgeon/intro_cta_fixed.json",
                    introCtaDurationFrames: 480, // ~15.9s
                    outroHookAudioUrl: "/storage/audio/sermons/marketing/0001_-_the_immutability_of_god/cta_narration.wav",
                    outroHookTranscriptSlug: "/storage/audio/sermons/marketing/0001_-_the_immutability_of_god/cta_narration.json",
                    outroHookDurationFrames: 663, // Cortado em "consumed." (22.1s)
                    outroCtaAudioUrl: "/storage/audio/library/marketing/spurgeon/outro_cta_fixed.wav",
                    outroCtaTranscriptSlug: "/storage/audio/library/marketing/spurgeon/outro_cta_fixed.json",
                    outroCtaDurationFrames: 440, // ~14.4s
					marketingTitle: "The Only Safe Harbor in a World That Never Stops Changing",
                }}
            />

            {/* ===== HÍBRIDO: clipes curtos (Remotion) — o corpo vai pro ffmpeg ===== */}
            <Composition
                id="Clip-Intro"
                component={ClipIntro as any}
                durationInFrames={1200}
                calculateMetadata={calcClipIntro}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ sermonNumber: "0001" } as any}
            />
            <Composition
                id="Clip-Outro"
                component={ClipOutro as any}
                durationInFrames={1800}
                calculateMetadata={calcClipOutro}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ sermonNumber: "0001" } as any}
            />
            <Composition
                id="Thumbnail"
                component={Thumbnail as any}
                durationInFrames={1}
                fps={30}
                width={1280}
                height={720}
                defaultProps={{ sermonNumber: "0001" } as any}
            />
            <Composition
                id="Sermon-Body-Base"
                component={SermonBodyBase as any}
                durationInFrames={1}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{ sermonNumber: "0001" } as any}
            />

            {/* ===== FÁBRICA DE SHORTS (9:16) ===== */}
            <Composition
                id="Short-Sermon"
                component={ShortSermon as any}
                durationInFrames={1350}
                calculateMetadata={calcShortSermon}
                fps={30}
                width={1080}
                height={1920}
                defaultProps={{
                    audioUrl: "",
                    words: [],
                    hookText: "THE BEST STUDY FOR YOUR SOUL?",
                } as any}
            />

            {/* ===== SPURGEON MARKETING PREVIEWS (V2) ===== */}
            <Composition
                id="Spurgeon-Hook-Preview"
                component={SpurgeonHook}
                durationInFrames={600} // 20s
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />

            <Composition
                id="Spurgeon-BrandAd-Preview"
                component={SpurgeonBrandAd}
                durationInFrames={300} // 10s
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />

            <Composition
                id="Spurgeon-YouTubeEndScreen"
                component={YouTubeEndScreen}
                durationInFrames={600} // 20s
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />

            <Composition
                id="Spurgeon-QRCode-Preview"
                component={QRCodePreview}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />

            <Composition
                id="Spurgeon-CTA-Preview"
                component={CTAPreview}
                durationInFrames={150}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />

            <Composition
                id="Spurgeon-Subscribe-Preview"
                component={SubscribePreview}
                durationInFrames={300}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />

            {/* ===== YOUTUBE LOWER THIRD ===== */}
            <Composition
                id="YouTube-LowerThird-Remotion"
                component={YouTubeLowerThird}
                durationInFrames={210}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    channelName: "Remotion",
                    subscriberCount: "46.6K",
                    avatarUrl: "https://yt3.googleusercontent.com/ytc/AIdro_kGRH-S253Qm8TqMj2V3PmV4y7Kq8V5z0xJ5w=s88-c-k-c0x00ffffff-no-rj",
                    accentColor: "#FF0000",
                }}
            />

            {/* ===== COMPOSITIONS PARA PRÉ-RENDERIZAÇÃO FFMEPG ===== */}
            <Composition
                id="Intro-CTA-Fixed"
                component={SpurgeonCTA}
                durationInFrames={480}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    ctaAudioUrl: "/storage/audio/library/marketing/spurgeon/intro_cta_fixed.wav"
                }}
            />

            <Composition
                id="Outro-CTA-Fixed"
                component={SpurgeonCTA}
                durationInFrames={440}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    ctaAudioUrl: "/storage/audio/library/marketing/spurgeon/outro_cta_fixed.wav"
                }}
            />

            <Composition
                id="End-Screen-Fixed"
                component={YouTubeEndScreen}
                durationInFrames={600}
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{}}
            />
        </>
    );
};
