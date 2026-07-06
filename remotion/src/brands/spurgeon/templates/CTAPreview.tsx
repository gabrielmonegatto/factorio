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
 * Composição isolada para design/teste da animação de CTA.
 * Loop de 5s: banner entra da esquerda, fica 3s, sai pela esquerda.
 */
export const CTAPreview: React.FC = () => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	const enterDuration = 20;  // 0.66s entrada
	const holdDuration = 90;   // 3s visível
	const exitStart = enterDuration + holdDuration;
	const exitDuration = 20;   // 0.66s saída

	// Slide de entrada (spring)
	const enterProgress = spring({
		frame,
		fps,
		config: { stiffness: 120, damping: 16 },
		durationInFrames: enterDuration,
	});

	// Slide de saída (interpolação linear)
	const exitProgress = interpolate(frame, [exitStart, exitStart + exitDuration], [0, 1], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});

	// translateX: começa em -500px, entra até 40px, depois volta para -500px
	const translateX = interpolate(enterProgress - exitProgress, [0, 1], [-500, 40]);

	// Linha de progresso dentro do banner (mostra quanto tempo ficará)
	const progressWidth = interpolate(
		frame,
		[enterDuration, exitStart],
		[100, 0],
		{ extrapolateLeft: "clamp", extrapolateRight: "clamp" }
	);

	return (
		<AbsoluteFill>
			{/* Background contextual */}
			<AbsoluteFill>
				<Img
					src={staticFile("images/cathedral_bg_cf_1.png")}
					style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.7 }}
				/>
				<AbsoluteFill style={{
					background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0) 100%)"
				}} />
			</AbsoluteFill>

			{/* CTA BANNER */}
			<div style={{
				position: "absolute",
				bottom: 140,
				left: 0,
				transform: `translateX(${translateX}px)`,
			}}>
				{/* Container do banner */}
				<div style={{
					display: "flex",
					flexDirection: "column",
					overflow: "hidden",
					borderRadius: "0 10px 10px 0",
					boxShadow: "4px 4px 30px rgba(0,0,0,0.7)",
				}}>
					{/* Topo dourado com label */}
					<div style={{
						background: "linear-gradient(90deg, #7a5c1e 0%, #c9a961 60%, #f0d080 100%)",
						padding: "6px 24px 4px 20px",
					}}>
						<span style={{
							fontFamily: "Georgia, serif",
							fontSize: 13,
							fontWeight: "bold",
							color: "rgba(0,0,0,0.75)",
							textTransform: "uppercase",
							letterSpacing: 2,
						}}>
							📚 Recurso Recomendado
						</span>
					</div>

					{/* Corpo escuro com título */}
					<div style={{
						background: "rgba(10,8,4,0.95)",
						padding: "14px 24px 16px 20px",
						borderTop: "none",
					}}>
						<p style={{
							margin: 0,
							fontFamily: "Georgia, serif",
							fontSize: 26,
							fontWeight: "bold",
							color: "#fff",
							letterSpacing: 0.5,
							lineHeight: 1.2,
							maxWidth: 340,
						}}>
							The Eternal Preacher
						</p>
						<p style={{
							margin: "4px 0 0 0",
							fontFamily: "Georgia, serif",
							fontSize: 14,
							color: "rgba(255,255,255,0.5)",
						}}>
							C.H. Spurgeon — Obras Completas
						</p>
					</div>

					{/* Barra de progresso dourada na base */}
					<div style={{
						height: 3,
						background: "rgba(255,255,255,0.1)",
					}}>
						<div style={{
							width: `${progressWidth}%`,
							height: "100%",
							background: "linear-gradient(90deg, #c9a961, #f0d080)",
							transition: "width 0.1s linear",
						}} />
					</div>
				</div>
			</div>
		</AbsoluteFill>
	);
};
