import React from "react";
import {
	AbsoluteFill,
	Img,
	staticFile,
	useCurrentFrame,
	interpolate,
	spring,
	useVideoConfig,
} from "remotion";

/**
 * Composição isolada para design/teste do QR Code Widget.
 * Aparece sobre o fundo real da catedral para contexto fiel.
 */
export const QRCodePreview: React.FC = () => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	// Fade-in suave na entrada (primeiros 0.5s)
	const opacity = interpolate(frame, [0, 15], [0, 1], {
		extrapolateRight: "clamp",
	});

	// Leve bounce de entrada no Y
	const translateY = spring({
		frame,
		fps,
		config: { stiffness: 180, damping: 20 },
		from: -20,
		to: 0,
	});

	return (
		<AbsoluteFill>
			{/* Background contextual */}
			<AbsoluteFill>
				<Img
					src={staticFile("images/cathedral_bg_cf_1.png")}
					style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.85 }}
				/>
				<AbsoluteFill style={{
					background: "linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.2) 100%)"
				}} />
			</AbsoluteFill>

			{/* QR CODE WIDGET */}
			<div style={{
				position: "absolute",
				top: 40,
				left: 40,
				opacity,
				transform: `translateY(${translateY}px)`,
				display: "flex",
				flexDirection: "column",
				alignItems: "center",
				gap: 10,
			}}>
				{/* Card branco com sombra */}
				<div style={{
					background: "white",
					borderRadius: 12,
					padding: 10,
					boxShadow: "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.1)",
					display: "flex",
					flexDirection: "column",
					alignItems: "center",
					gap: 8,
				}}>
					{/* QR Code gerado com serviço público (substitua pela imagem real) */}
					<img
						src="https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=https://youtube.com/@charlesspurgeontreasures"
						width={140}
						height={140}
						style={{ display: "block", borderRadius: 4 }}
					/>
					{/* Linha separadora dourada */}
					<div style={{
						width: "100%",
						height: 2,
						background: "linear-gradient(90deg, transparent, #c9a961, transparent)",
					}} />
					{/* Texto abaixo */}
					<span style={{
						fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
						fontSize: 12,
						fontWeight: 300,
						color: "#555",
						textTransform: "uppercase",
						letterSpacing: 2,
					}}>
						Books & Devotionals
					</span>
				</div>
			</div>

		</AbsoluteFill>
	);
};
