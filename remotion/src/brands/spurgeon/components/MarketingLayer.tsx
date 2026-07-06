import React from "react";
import { 
	AbsoluteFill, 
	Img, 
	staticFile, 
	useCurrentFrame, 
	interpolate
} from "remotion";

interface MarketingLayerProps {
	qrCodeUrl?: string;
}

export const MarketingLayer: React.FC<MarketingLayerProps> = ({ qrCodeUrl }) => {
	const frame = useCurrentFrame();

	// Animação do QR Code (Fade-in sutil no início)
	const qrOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });

	return (
		<AbsoluteFill style={{ pointerEvents: "none" }}>
			
			{/* QR CODE - TOPO ESQUERDO */}
			{qrCodeUrl && qrCodeUrl.length > 0 && (
				<div style={{
					position: "absolute",
					top: 40,
					left: 40,
					opacity: qrOpacity,
					display: "flex",
					flexDirection: "column",
					alignItems: "center",
					gap: 8
				}}>
					<div style={{
						padding: 8,
						backgroundColor: "white",
						borderRadius: 8,
						boxShadow: "0 4px 15px rgba(0,0,0,0.5)"
					}}>
						<Img 
							src={staticFile(qrCodeUrl)} 
							style={{ width: 120, height: 120 }} 
						/>
					</div>
					<span style={{
						color: "rgba(255,255,255,0.85)",
						fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
						fontSize: 12,
						fontWeight: 300,
						letterSpacing: 2,
						textTransform: "uppercase",
						textShadow: "0 2px 4px rgba(0,0,0,0.8)"
					}}>
						Books & Devotionals
					</span>
				</div>
			)}
		</AbsoluteFill>
	);
};
