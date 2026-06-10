import { AbsoluteFill } from "remotion";

interface ChannelBrandingProps {
    channel: { name: string; subtitle: string };
    reference: { book: string; chapter: number; translation: string };
}

export const ChannelBranding: React.FC<ChannelBrandingProps> = ({ channel, reference }) => {
    return (
        <AbsoluteFill style={{ pointerEvents: "none" }}>
            {/* Canto superior direito: nome do canal */}
            <div
                style={{
                    position: "absolute",
                    top: 40,
                    right: 60,
                    textAlign: "right",
                }}
            >
                <p style={{
                    fontFamily: 'Cinzel',
                    fontSize: 22,
                    color: "#5eb8bc",
                    margin: 0,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    opacity: 0.8,
                }}>
                    {channel.name}
                </p>
                <p style={{
                    fontFamily: 'Montserrat',
                    fontSize: 16,
                    fontStyle: "italic",
                    color: "#f0ede888",
                    margin: "4px 0 0 0",
                    letterSpacing: "0.08em",
                }}>
                    {channel.subtitle}
                </p>
            </div>

            {/* Canto inferior esquerdo: referência bíblica */}
            <div
                style={{
                    position: "absolute",
                    bottom: 40,
                    left: 60,
                }}
            >
                <p style={{
                    fontFamily: 'Cinzel',
                    fontStyle: "italic",
                    fontSize: 24,
                    color: "#c8a96e",
                    margin: 0,
                    opacity: 0.75,
                    letterSpacing: "0.04em",
                }}>
                    {reference.book} {reference.chapter} · {reference.translation}
                </p>
            </div>

            {/* Barra decorativa inferior */}
            <div
                style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 3,
                    background: "linear-gradient(to right, transparent, #3a8a8e66, transparent)",
                }}
            />
        </AbsoluteFill>
    );
};
