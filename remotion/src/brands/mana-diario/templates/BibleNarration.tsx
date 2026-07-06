import { AbsoluteFill, Audio, Sequence, useCurrentFrame, useVideoConfig, interpolate, staticFile } from "remotion";
import { EpisodeProps } from "../../../data/sampleEpisode";
import { VerseDisplay } from "../components/VerseDisplay";
import { ChannelBranding } from "../components/ChannelBranding";
import { Background } from "../../../core/components/Background";
import { Intro } from "../components/Intro";
import { Outro } from "../components/Outro";

// Duração da intro e outro em frames (30fps)

// Duração da intro e outro em frames (30fps)
const INTRO_DURATION = 90;   // 3 segundos
const OUTRO_DURATION = 150;  // 5 segundos

export const BibleNarration: React.FC<EpisodeProps> = ({
    channel,
    reference,
    sections,
    audioSrc,
    bgAsset,
    durationInFrames,
    ambientSrc = "/audio/ambient_night.mp3",
    bgMusicSrc = "/audio/bg_music_piano.mp3",
}) => {
    const frame = useCurrentFrame();

    // Fade in/out global do vídeo
    const globalOpacity = interpolate(
        frame,
        [0, 20, durationInFrames - 30, durationInFrames],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    const contentStart = INTRO_DURATION;
    const contentEnd = durationInFrames - OUTRO_DURATION;

    return (
        <AbsoluteFill style={{ opacity: globalOpacity }}>
            {/* Fundo atmosférico */}
            <Background frame={frame} totalFrames={durationInFrames} bgAsset={bgAsset} />

            {/* Narração Principal — Mantida para Estabilidade Máxima */}
            {audioSrc ? (
                <Audio src={staticFile(audioSrc)} startFrom={0} volume={1.0} />
            ) : null}

            {/* INTRO: logo + nome do canal surgindo */}
            <Sequence from={0} durationInFrames={INTRO_DURATION}>
                <Intro channel={channel} reference={reference} />
            </Sequence>

            {/* CONTEÚDO: versículos aparecem conforme a narração avança */}
            <Sequence from={contentStart} durationInFrames={contentEnd - contentStart}>
                {/* Branding fixo (logo pequeno + referência no canto) */}
                <ChannelBranding channel={channel} reference={reference} />

                {/* Versículos — cada seção tem seu tempo de entrada */}
                {sections.map((section) => {
                    const sectionStart = section.startFrame - contentStart;
                    // Próxima seção começa quando? Calcular duração
                    const nextIdx = sections.findIndex(s => s.id === section.id) + 1;
                    const nextStart = nextIdx < sections.length
                        ? sections[nextIdx].startFrame - contentStart
                        : contentEnd - contentStart;
                    const sectionDuration = nextStart - sectionStart;

                    if (sectionStart < 0) return null;

                    return (
                        <Sequence
                            key={section.id}
                            from={sectionStart}
                            durationInFrames={sectionDuration}
                        >
                            <VerseDisplay
                                text={section.text}
                                verseRef={section.verseRef}
                            />
                        </Sequence>
                    );
                })}
            </Sequence>

            {/* OUTRO: CTA para inscrição */}
            <Sequence from={contentEnd} durationInFrames={OUTRO_DURATION}>
                <Outro channel={channel} />
            </Sequence>
        </AbsoluteFill>
    );
};
