import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

interface OutroProps {
    channel: { name: string; subtitle: string };
}

export const Outro: React.FC<OutroProps> = ({ channel }) => {
    const frame = useCurrentFrame();

    const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });

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
            {/* Ícone de sino */}
            <p style={{ fontSize: 64, margin: "0 0 24px 0" }}>🔔</p>

            {/* CTA principal */}
            <p style={{
                fontFamily: '"Georgia", serif',
                fontSize: 48,
                fontWeight: 700,
                color: "#f0ede8",
                margin: "0 0 16px 0",
                textAlign: "center",
                letterSpacing: "0.03em",
                textShadow: "0 2px 20px rgba(0,0,0,0.8)",
            }}>
                Inscreva-se no canal
            </p>

            <p style={{
                fontFamily: '"Georgia", serif',
                fontStyle: "italic",
                fontSize: 28,
                color: "#5eb8bc",
                margin: "0 0 40px 0",
                textAlign: "center",
                letterSpacing: "0.06em",
            }}>
                e receba diariamente o alimento espiritual
            </p>

            {/* Separador */}
            <div style={{
                width: 160, height: 1,
                background: "linear-gradient(to right, transparent, #c8a96e, transparent)",
                margin: "0 0 32px 0",
            }} />

            {/* Nome do canal */}
            <p style={{
                fontFamily: '"Georgia", serif',
                fontSize: 22,
                color: "#c8a96e",
                margin: 0,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                opacity: 0.8,
            }}>
                {channel.name} · {channel.subtitle}
            </p>
        </AbsoluteFill>
    );
};
