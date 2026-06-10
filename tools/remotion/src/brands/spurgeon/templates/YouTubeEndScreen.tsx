import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

export const YouTubeEndScreen: React.FC = () => {
	return (
		<AbsoluteFill style={{ backgroundColor: "#050505", overflow: "hidden" }}>
			{/* Background Image with heavy dimming */}
			<AbsoluteFill>
				<Img
					src={staticFile("images/cathedral_bg_cf_1.png")}
					style={{
						width: "100%",
						height: "100%",
						objectFit: "cover",
						opacity: 0.3,
						filter: "grayscale(50%) blur(4px)",
					}}
				/>
				{/* Dark Vignette to focus attention on the elements */}
				<div
					style={{
						position: "absolute",
						inset: 0,
						background: "radial-gradient(circle at center, transparent 20%, rgba(0,0,0,0.9) 100%)",
					}}
				/>
			</AbsoluteFill>

			{/* 
				YouTube Native Outline Guides 
				These guides correspond to the standard locations where YouTube 
				places the clickable End Screen elements.
			*/}

			<div style={{ position: "absolute", width: "100%", height: "100%", top: 0, left: 0 }}>
				{/* LEFT COLUMN: 2 Stacked Rectangles (Video & Playlist) */}
				
				{/* Top Rectangle: Next Video */}
				<div 
					style={{
						position: "absolute",
						left: "5%",
						top: "15%",
						width: "35%",
						height: "30%",
						border: "2px dashed rgba(201, 169, 97, 0.4)",
						borderRadius: 12,
						background: "rgba(0,0,0,0.4)",
						display: "flex",
						justifyContent: "center",
						alignItems: "center",
						flexDirection: "column",
					}}
				>
					<span style={{ color: "rgba(255,255,255,0.7)", fontFamily: "Georgia, serif", fontSize: 24, fontStyle: "italic" }}>
						Continue the Legacy
					</span>
				</div>

				{/* Bottom Rectangle: Playlist */}
				<div 
					style={{
						position: "absolute",
						left: "5%",
						top: "50%",
						width: "35%",
						height: "30%",
						border: "2px dashed rgba(201, 169, 97, 0.4)",
						borderRadius: 12,
						background: "rgba(0,0,0,0.4)",
						display: "flex",
						justifyContent: "center",
						alignItems: "center",
						flexDirection: "column",
					}}
				>
					<span style={{ color: "rgba(255,255,255,0.7)", fontFamily: "Georgia, serif", fontSize: 24, fontStyle: "italic" }}>
						Sermon Library
					</span>
				</div>

				{/* RIGHT COLUMN: Subscribe Circle */}
				<div
					style={{
						position: "absolute",
						right: "15%",
						top: "50%",
						transform: "translateY(-50%)", // Center vertically
						width: "250px",
						height: "250px",
						borderRadius: "50%",
						border: "2px dashed rgba(201, 169, 97, 0.4)",
						background: "rgba(0,0,0,0.4)",
						display: "flex",
						flexDirection: "column",
						justifyContent: "center",
						alignItems: "center",
					}}
				>
					{/* Text Below Circle Guide */}
					<span style={{ 
						position: "absolute", 
						bottom: -50,
						color: "#C9A961", 
						fontFamily: "'Inter', sans-serif", 
						fontSize: 22, 
						fontWeight: 500,
						letterSpacing: 2,
						textTransform: "uppercase",
						whiteSpace: "nowrap"
					}}>
						Subscribe Now
					</span>
				</div>
			</div>

			{/* Decorative Branding Elements */}
			<div style={{ position: "absolute", bottom: 40, width: "100%", display: "flex", justifyContent: "center", alignItems: "center", gap: 20 }}>
				<div style={{ width: 100, height: 1, background: "linear-gradient(to right, transparent, rgba(201,169,97,0.5))" }} />
				<span style={{ color: "rgba(255,255,255,0.4)", fontFamily: "Georgia", fontStyle: "italic", fontSize: 18 }}>
					"He who has God and everything else has no more than he who has God only."
				</span>
				<div style={{ width: 100, height: 1, background: "linear-gradient(to left, transparent, rgba(201,169,97,0.5))" }} />
			</div>
		</AbsoluteFill>
	);
};
