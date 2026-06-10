import { AbsoluteFill, useCurrentFrame, interpolate, staticFile, Video, Img, useVideoConfig } from "remotion";

interface BackgroundProps {
    frame: number;
    totalFrames: number;
    bgAsset?: string;
}

const COLORS = {
    bgDeep: "#020507",
    bgMid: "#081018",
    teal: "#2a6a70",
    tealLight: "#5eb8bc",
};

// 160 estrelas estáticas — posições e tamanhos fixos
const STARS = Array.from({ length: 160 }, (_, i) => {
    const s1 = Math.sin(i * 127.1) * 43758.5453;
    const s2 = Math.sin(i * 311.7) * 43758.5453;
    const s3 = Math.sin(i * 74.9) * 43758.5453;
    const s4 = Math.sin(i * 213.3) * 43758.5453;
    const frac = (n: number) => n - Math.floor(n);
    return {
        x: frac(s1) * 1920,
        y: frac(s2) * 750,          // estrelas só na parte superior (75%)
        baseR: 0.6 + frac(s3) * 1.8,
        baseOpacity: 0.25 + frac(s4) * 0.65,
        period: 150 + Math.abs(Math.sin(i * 89.3)) * 200,
        phase: frac(s3) * 360,
    };
});

const CLOUDS = [
    { xBase: 290, y: 130, rx: 320, ry: 55, opacity: 0.055, speed: 0.012 },
    { xBase: 1150, y: 90, rx: 260, ry: 45, opacity: 0.04, speed: 0.008 },
    { xBase: 1490, y: 185, rx: 300, ry: 55, opacity: 0.045, speed: 0.01 },
    { xBase: 580, y: 250, rx: 180, ry: 38, opacity: 0.03, speed: 0.015 },
];

export const Background: React.FC<BackgroundProps> = ({ frame, totalFrames, bgAsset }) => {
    const { width, height } = useVideoConfig();

    // Pulso suave do brilho central (ciclo lento de 12s)
    const centerGlow = interpolate(
        frame % 360,
        [0, 180, 360],
        [0.15, 0.27, 0.15],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    // Pulso do halo da lua (ciclo de 8s)
    const moonHaloOpacity = interpolate(
        frame % 240,
        [0, 120, 240],
        [0.7, 1.0, 0.7],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    // >>> CONFIGURAÇÃO DO MOVIMENTO (KEN BURNS) <<<
    // DICA: Ajuste os números abaixo para mudar a intensidade do zoom e deslize.

    // Zoom: 1.0 é o original. 1.25 significa 25% de aproximação. (Ponto de equilíbrio)
    const kenBurnsScale = interpolate(
        frame,
        [0, totalFrames],
        [1, 1.25],
        { extrapolateRight: "clamp" }
    );

    // Deslize Horizontal (X): Quanto maior o número negativo, mais ele anda para a esquerda.
    const kenBurnsX = interpolate(
        frame,
        [0, totalFrames],
        [0, -70],
        { extrapolateRight: "clamp" }
    );

    // Deslize Vertical (Y): Quanto maior o número negativo, mais ele sobe.
    const kenBurnsY = interpolate(
        frame,
        [0, totalFrames],
        [0, -20],
        { extrapolateRight: "clamp" }
    );
    // >>> FIM DA CONFIGURAÇÃO <<<

    const isVideo = bgAsset?.endsWith(".mp4");

    return (
        <AbsoluteFill>
            {/* Fundo base - Escuro se não houver asset */}
            <AbsoluteFill style={{
                background: bgAsset ? "black" : `radial-gradient(ellipse 130% 110% at 50% -5%, ${COLORS.bgMid} 0%, ${COLORS.bgDeep} 65%)`,
            }} />

            {/* ASSET REAL (PEXELS) */}
            {bgAsset && (
                <AbsoluteFill>
                    <div style={{
                        width: "100%",
                        height: "100%",
                        transform: !isVideo ? `scale(${kenBurnsScale}) translate(${kenBurnsX}px, ${kenBurnsY}px)` : "none",
                        transformOrigin: "center center",
                    }}>
                        {isVideo ? (
                            <Video
                                src={staticFile(bgAsset)}
                                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                muted
                                loop
                            />
                        ) : (
                            <Img
                                src={staticFile(bgAsset)}
                                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                            />
                        )}
                    </div>
                    {/* Overlay escuro para garantir legibilidade dos textos em cima do asset real */}
                    <AbsoluteFill style={{ backgroundColor: "rgba(0,0,0,0.3)" }} />
                </AbsoluteFill>
            )}

            {/* SVG: estrelas + lua + nuvens — tudo animado (overlay sutil sobre o asset real) */}
            <AbsoluteFill style={{ pointerEvents: 'none' }}>
                <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{ position: "absolute" }}>
                    <defs>
                        <filter id="softBlur">
                            <feGaussianBlur stdDeviation="30" />
                        </filter>
                        <filter id="moonGlow">
                            <feGaussianBlur stdDeviation="12" result="blur" />
                            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                        </filter>
                        <radialGradient id="moonHalo" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor="#d0eaec" stopOpacity="0.3" />
                            <stop offset="50%" stopColor="#5eb8bc" stopOpacity="0.1" />
                            <stop offset="100%" stopColor="#5eb8bc" stopOpacity="0" />
                        </radialGradient>
                        <radialGradient id="moonFace" cx="38%" cy="32%" r="60%">
                            <stop offset="0%" stopColor="#eef6f7" />
                            <stop offset="65%" stopColor="#b8dde0" />
                            <stop offset="100%" stopColor="#80c0c4" />
                        </radialGradient>
                    </defs>

                    {STARS.map((star, i) => {
                        const t = ((frame + star.phase) / star.period) * Math.PI * 2;
                        const twinkle = star.baseOpacity * (0.6 + 0.4 * Math.sin(t));
                        const r = star.baseR * (0.85 + 0.15 * Math.sin(t * 0.7 + 1.2));
                        return (
                            <circle key={i} cx={star.x} cy={star.y} r={r} fill="white" opacity={bgAsset ? twinkle * 0.5 : twinkle} />
                        );
                    })}

                    <ellipse
                        cx="1530" cy="145" rx="100" ry="100"
                        fill="url(#moonHalo)"
                        opacity={bgAsset ? moonHaloOpacity * 0.4 : moonHaloOpacity}
                    />
                    <circle cx="1530" cy="145" r="40" fill="url(#moonFace)" opacity={bgAsset ? 0.4 : 0.78} filter="url(#moonGlow)" />
                    <circle cx="1546" cy="145" r="37" fill={COLORS.bgDeep} opacity={bgAsset ? 0.3 : 0.65} />

                    {CLOUDS.map((cloud, i) => {
                        const drift = Math.sin(frame * cloud.speed) * 40;
                        return (
                            <ellipse
                                key={`cloud-${i}`}
                                cx={cloud.xBase + drift}
                                cy={cloud.y}
                                rx={cloud.rx}
                                ry={cloud.ry}
                                fill="white"
                                opacity={bgAsset ? cloud.opacity * 0.5 : cloud.opacity}
                                filter="url(#softBlur)"
                            />
                        );
                    })}
                </svg>
            </AbsoluteFill>

            {/* Brilho teal suave no centro (pulsante) */}
            <AbsoluteFill style={{
                background: `radial-gradient(ellipse 50% 45% at 50% 48%, ${COLORS.teal}45 0%, transparent 70%)`,
                opacity: centerGlow,
            }} />

            {/* Vinheta nas bordas */}
            <AbsoluteFill style={{
                background: `radial-gradient(ellipse 88% 88% at 50% 50%, transparent 42%, ${COLORS.bgDeep}f0 100%)`,
            }} />
        </AbsoluteFill>
    );
};
