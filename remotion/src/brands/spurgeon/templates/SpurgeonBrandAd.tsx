import React from "react";
import { AbsoluteFill, Img, staticFile, spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";

export const SpurgeonBrandAd: React.FC = () => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	// Animações
	const entrySpring = spring({ frame, fps, config: { damping: 14 } });
	
	const contentOpacity = interpolate(entrySpring, [0, 1], [0, 1]);
	const scale = interpolate(entrySpring, [0, 1], [1.1, 1]);

	return (
		<AbsoluteFill style={{ backgroundColor: "#000" }}>
			{/* Fundo com movimento suave */}
			<AbsoluteFill>
				<Img
					src={staticFile("images/cathedral_bg_cf_1.png")}
					style={{
						width: "100%",
						height: "100%",
						objectFit: "cover",
						opacity: 0.4,
						transform: `scale(${scale})`,
						filter: "sepia(0.8) hue-rotate(-15deg) contrast(1.2)",
					}}
				/>
				<div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.6)" }} />
			</AbsoluteFill>

			<div
				style={{
					position: "absolute",
					inset: 0,
					display: "flex",
					flexDirection: "row",
					alignItems: "center",
					justifyContent: "center",
					opacity: contentOpacity,
					gap: 80,
				}}
			>
				{/* Lado Esquerdo: Mensagem Institucional */}
				<div style={{ display: "flex", flexDirection: "column", gap: 30, maxWidth: 600 }}>
					<h1 style={{ 
						fontFamily: "Georgia, serif", 
						fontSize: 64, 
						color: "#C9A961", 
						margin: 0,
						fontWeight: "normal",
						lineHeight: 1.1 
					}}>
						Deepen Your Faith<br />
						<span style={{ fontSize: 48, color: "#FFF", fontStyle: "italic" }}>
							With our exclusive library
						</span>
					</h1>
					
					<p style={{ 
						fontFamily: "'Inter', sans-serif", 
						fontSize: 24, 
						color: "rgba(255,255,255,0.8)", 
						lineHeight: 1.5,
						margin: 0 
					}}>
						Scan the QR code to access premium Devotionals, Sermon Books, and Theological Studies from the Prince of Preachers.
					</p>

					<div style={{ 
						padding: "16px 32px", 
						background: "#C9A961", 
						color: "#000", 
						fontFamily: "'Inter', sans-serif", 
						fontWeight: "bold", 
						fontSize: 20, 
						borderRadius: 8,
						alignSelf: "flex-start",
						marginTop: 20,
						textTransform: "uppercase",
						letterSpacing: 1
					}}>
						Listen to the Legacy
					</div>
				</div>

				{/* Lado Direito: The Product / QR Code */}
				<div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
					<div style={{ 
						width: 300, 
						height: 300, 
						background: "#FFF", 
						padding: 20, 
						borderRadius: 24,
						boxShadow: "0 20px 50px rgba(0,0,0,0.5), 0 0 0 4px rgba(201,169,97,0.3)" 
					}}>
						<Img 
							src={staticFile("images/sample_qr.png")} 
							style={{ width: "100%", height: "100%" }} 
						/>
					</div>
					<span style={{ 
						fontFamily: "'Inter', sans-serif", 
						fontSize: 20, 
						color: "rgba(201,169,97,0.8)", 
						fontWeight: 500,
						letterSpacing: 2
					}}>
						@CHARLES<span style={{color: "white"}}>SPURGEON</span>TREASURES
					</span>
				</div>
			</div>
		</AbsoluteFill>
	);
};
