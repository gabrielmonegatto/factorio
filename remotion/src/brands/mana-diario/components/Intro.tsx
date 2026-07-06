import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

interface IntroProps {
    channel: { name: string; subtitle: string };
    reference: { book: string; chapter: number; translation: string };
}

export const Intro: React.FC<IntroProps> = ({ channel, reference }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const fadeIn = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: "clamp" });

    const titleProgress = spring({ frame: frame - 10, fps, config: { damping: 20, stiffness: 100 } });
    const subtitleProgress = spring({ frame: frame - 25, fps, config: { damping: 20, stiffness: 80 } });

    const titleY = interpolate(titleProgress, [0, 1], [30, 0]);
    const subtitleY = interpolate(subtitleProgress, [0, 1], [20, 0]);

    return (
        <AbsoluteFill
            style={{
                justifyContent: "center",
                alignItems: "center",
                opacity: fadeIn,
                flexDirection: "column",
                gap: 0,
            }}
        >
            {/* Nome do canal */}
            <div style={{ transform: `translateY(${titleY}px)`, opacity: titleProgress, textAlign: "center" }}>
                <p style={{
                    fontFamily: 'Cinzel',
                    fontSize: 72,
                    fontWeight: 700,
                    color: "#f0ede8",
                    margin: 0,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    textShadow: "0 0 40px rgba(94,184,188,0.4)",
                }}>
                    {channel.name}
                </p>
            </div>

            {/* Separador */}
            <div style={{
                width: 120, height: 1,
                background: "linear-gradient(to right, transparent, #5eb8bc, transparent)",
                margin: "20px auto",
                opacity: subtitleProgress,
            }} />

            {/* Subtítulo */}
            <div style={{ transform: `translateY(${subtitleY}px)`, opacity: subtitleProgress, textAlign: "center" }}>
                <p style={{
                    fontFamily: 'Montserrat',
                    fontStyle: "italic",
                    fontSize: 32,
                    color: "#5eb8bc",
                    margin: "0 0 40px 0",
                    letterSpacing: "0.15em",
                    textTransform: "uppercase",
                }}>
                    {channel.subtitle}
                </p>

                {/* Livro + tradução */}
                <p style={{
                    fontFamily: 'Cinzel',
                    fontSize: 28,
                    color: "#c8a96e",
                    margin: 0,
                    opacity: 0.85,
                    letterSpacing: "0.06em",
                }}>
                    {reference.book} {reference.chapter} · {reference.translation}
                </p>
            </div>
        </AbsoluteFill>
    );
};
