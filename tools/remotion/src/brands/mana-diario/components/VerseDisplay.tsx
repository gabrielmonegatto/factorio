import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

interface VerseDisplayProps {
    text: string;
    verseRef: string;
}

export const VerseDisplay: React.FC<VerseDisplayProps> = ({ text, verseRef }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Animação de entrada: desliza de baixo + fade in
    const progress = spring({
        frame,
        fps,
        config: { damping: 18, stiffness: 80, mass: 1 },
    });

    const translateY = interpolate(progress, [0, 1], [40, 0]);
    const opacity = interpolate(progress, [0, 1], [0, 1]);

    // Fade out no final da seção
    const totalVisible = 9999; // controlado pelo Sequence pai
    const fadeOut = interpolate(
        frame,
        [totalVisible - 30, totalVisible],
        [1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    return (
        <AbsoluteFill
            style={{
                justifyContent: "center",
                alignItems: "center",
                padding: "0 160px",
            }}
        >
            <div
                style={{
                    textAlign: "center",
                    opacity: opacity * fadeOut,
                    transform: `translateY(${translateY}px)`,
                }}
            >
                {/* Separador decorativo topo */}
                <div style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 16,
                    marginBottom: 40,
                }}>
                    <div style={{ height: 1, width: 80, background: "linear-gradient(to right, transparent, #5eb8bc88)" }} />
                    <span style={{ fontSize: 22, color: "#5eb8bc88" }}>✦</span>
                    <div style={{ height: 1, width: 80, background: "linear-gradient(to left, transparent, #5eb8bc88)" }} />
                </div>

                {/* Texto do versículo */}
                <p
                    style={{
                        fontFamily: 'EB Garamond',
                        fontSize: 52,
                        fontWeight: 400,
                        color: "#f0ede8",
                        lineHeight: 1.65,
                        margin: "0 0 32px 0",
                        textShadow: "0 2px 20px rgba(0,0,0,0.8)",
                        letterSpacing: "0.01em",
                    }}
                >
                    {text}
                </p>

                {/* Referência do versículo */}
                <p
                    style={{
                        fontFamily: 'Montserrat',
                        fontSize: 28,
                        fontStyle: "italic",
                        color: "#5eb8bc",
                        margin: 0,
                        letterSpacing: "0.06em",
                        opacity: 0.85,
                    }}
                >
                    {verseRef}
                </p>

                {/* Separador decorativo base */}
                <div style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 16,
                    marginTop: 40,
                }}>
                    <div style={{ height: 1, width: 80, background: "linear-gradient(to right, transparent, #5eb8bc88)" }} />
                    <span style={{ fontSize: 22, color: "#5eb8bc88" }}>✦</span>
                    <div style={{ height: 1, width: 80, background: "linear-gradient(to left, transparent, #5eb8bc88)" }} />
                </div>
            </div>
        </AbsoluteFill>
    );
};
