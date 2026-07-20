import React from "react";
import {
	AbsoluteFill,
	Audio as RemotionAudio,
	Img,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
	interpolate,
	spring,
} from "remotion";
import { resolveAsset } from "../../../core/library/resolveAsset";

// Label humano-legível (limpo) exibido sob o QR. O QR em si codifica a URL de
// redirect com UTM (mananciall.org/go?s=yt&v=NNNN) — ver props qrCodeUrl.
const CLEAN_LINK_LABEL = "mananciall.org/en/treasures-spurgeon";

/**
 * SPURGEON CTA SCREEN — 2 Cenas
 * ─────────────────────────────
 * Cena 1 (0–7s):   Tela de Inscrição "Charles Spurgeon Treasures"
 * Cena 2 (7–14s):  Tela de QR Code "Devocionais & Citações"
 *
 * Total: 420 frames @ 30fps = 14 segundos
 */

// ─── CENA 1: Inscrição ──────────────────────────────────────────────────────
const SceneSubscribe: React.FC<{ frame: number }> = ({ frame }) => {
	const { fps } = useVideoConfig();

	const PORTRAIT_IN = 10;
	const LABEL_IN    = 20;
	const TITLE_IN    = 35;
	const CTA_IN      = 65;

	const portraitX = spring({
		frame: frame - PORTRAIT_IN,
		fps,
		config: { stiffness: 60, damping: 15, mass: 1.2 },
		from: 300,
		to: 0,
	});

	const makeTextAnim = (startFrame: number) => ({
		opacity: interpolate(frame, [startFrame, startFrame + 20], [0, 1], {
			extrapolateLeft: "clamp",
			extrapolateRight: "clamp",
		}),
		transform: `translateY(${interpolate(frame, [startFrame, startFrame + 20], [20, 0], {
			extrapolateLeft: "clamp",
			extrapolateRight: "clamp",
		})}px)`,
	});

	const barWidth = interpolate(frame, [TITLE_IN + 20, TITLE_IN + 50], [0, 100], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});

	const btnScale = spring({
		frame: frame - CTA_IN,
		fps,
		config: { stiffness: 200, damping: 12 },
		from: 0.7,
		to: 1,
	});
	const btnOpacity = interpolate(frame, [CTA_IN, CTA_IN + 15], [0, 1], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});

	const particles = Array.from({ length: 8 }, (_, i) => {
		const seed = i * 137.5;
		const x = seed % 100;
		const speed = 0.3 + (i % 3) * 0.15;
		const yOffset = (frame * speed + seed) % 100;
		const pOpacity = Math.sin((frame / fps) * 0.8 + i) * 0.3 + 0.2;
		return { x, yOffset, pOpacity, size: 3 + (i % 3) * 2 };
	});

	return (
		<>
			{/* Spurgeon */}
			<div style={{
				position: "absolute",
				right: 0,
				bottom: 0,
				transform: `translateX(${portraitX}px)`,
				height: "100%", // Preenche toda a tela verticalmente
				display: "flex",
				alignItems: "flex-end",
			}}>
				<Img
					src={staticFile("images/spurgeon_base.png")}
					style={{
						height: "100%",
						objectFit: "contain",
						objectPosition: "bottom right",
						// Filtro potente para garantir que o fundo suma
						filter: "contrast(1.5) brightness(1.1) saturate(0)",
						mixBlendMode: "screen",
						// Suavização lateral para não ter corte no braço
						WebkitMaskImage: "linear-gradient(to left, black 70%, transparent 100%)",
					}}
				/>
				<div style={{
					position: "absolute",
					bottom: 0,
					left: 0,
					right: 0,
					height: "30%",
					background: "linear-gradient(to top, rgba(5,3,2,1) 0%, transparent 100%)",
				}} />
			</div>

			{/* Partículas */}
			{particles.map((p, i) => (
				<div key={i} style={{
					position: "absolute",
					left: `${p.x}%`,
					bottom: `${p.yOffset}%`,
					width: p.size,
					height: p.size,
					borderRadius: "50%",
					backgroundColor: "#c9a961",
					opacity: p.pOpacity,
					boxShadow: `0 0 ${p.size * 3}px #c9a961`,
				}} />
			))}

			{/* Conteúdo esquerdo */}
			<div style={{
				position: "absolute",
				left: 80,
				top: "50%",
				transform: "translateY(-50%)",
				maxWidth: 700,
				display: "flex",
				flexDirection: "column",
				gap: 20,
			}}>
				<div style={{ ...makeTextAnim(LABEL_IN) }}>
					<span style={{
						fontFamily: "Georgia, serif",
						fontSize: 16,
						color: "#c9a961",
						textTransform: "uppercase",
						letterSpacing: 5,
					}}>
						Subscribe to our channel
					</span>
				</div>

				<div style={{ ...makeTextAnim(TITLE_IN) }}>
					<h1 style={{
						margin: 0,
						fontFamily: "Georgia, serif",
						fontSize: 68,
						fontWeight: "bold",
						color: "#ffffff",
						lineHeight: 1.1,
						textShadow: "0 4px 40px rgba(0,0,0,0.8)",
					}}>
						Charles Spurgeon<br />Treasures
					</h1>
				</div>

				<div style={{
					width: `${barWidth}%`,
					height: 3,
					maxWidth: 400,
					background: "linear-gradient(90deg, #c9a961, #f0d080)",
					borderRadius: 2,
				}} />

				<div style={{ ...makeTextAnim(TITLE_IN + 15) }}>
					<p style={{
						margin: 0,
						fontFamily: "Georgia, serif",
						fontSize: 22,
						color: "rgba(255,255,255,0.65)",
						lineHeight: 1.6,
						maxWidth: 480,
					}}>
						Sermons that transformed the world.
						<br />
						<em>New video every day.</em>
					</p>
				</div>

				<div style={{
					opacity: btnOpacity,
					transform: `scale(${btnScale})`,
					transformOrigin: "left center",
					display: "flex",
					gap: 16,
					alignItems: "center",
					marginTop: 10,
				}}>
					<div style={{
						background: "linear-gradient(135deg, #c9a961 0%, #f0d080 50%, #c9a961 100%)",
						padding: "16px 36px",
						borderRadius: 6,
						boxShadow: "0 8px 30px rgba(201,169,97,0.4)",
					}}>
						<span style={{
							fontFamily: "Georgia, serif",
							fontSize: 20,
							fontWeight: "bold",
							color: "#1a0f00",
							textTransform: "uppercase",
							letterSpacing: 2,
						}}>
							▶ Subscribe
						</span>
					</div>

					<div style={{
						border: "2px solid rgba(255,255,255,0.3)",
						padding: "14px 28px",
						borderRadius: 6,
					}}>
						<span style={{
							fontFamily: "Georgia, serif",
							fontSize: 18,
							color: "rgba(255,255,255,0.8)",
						}}>
							🔔 Turn on alerts
						</span>
					</div>
				</div>
			</div>
		</>
	);
};

// ─── SCENE 2: QR Code — Devotionals ──────────────────────────────────────────
const SceneQRCode: React.FC<{ frame: number; qrCodeUrl?: string; linkLabel?: string }> = ({ frame, qrCodeUrl, linkLabel }) => {
	const { fps } = useVideoConfig();

	// Everything enters together, with small staggered delays
	const CONTENT_IN = 10;

	const qrScale = spring({
		frame: frame - CONTENT_IN,
		fps,
		config: { stiffness: 100, damping: 14 },
		from: 0.5,
		to: 1,
	});

	const makeTextAnim = (startFrame: number) => ({
		opacity: interpolate(frame, [startFrame, startFrame + 25], [0, 1], {
			extrapolateLeft: "clamp",
			extrapolateRight: "clamp",
		}),
		transform: `translateY(${interpolate(frame, [startFrame, startFrame + 25], [16, 0], {
			extrapolateLeft: "clamp",
			extrapolateRight: "clamp",
		})}px)`,
	});

	// Pulsing glow around the QR
	const glowOpacity = 0.4 + Math.sin((frame / fps) * 1.5) * 0.3;

	return (
		<div style={{
			position: "absolute",
			inset: 0,
			display: "flex",
			flexDirection: "column",
			alignItems: "center",
			justifyContent: "center",
			gap: 40,
		}}>
			{/* Top Label */}
			<div style={{ ...makeTextAnim(CONTENT_IN), textAlign: "center" }}>
				<span style={{
					fontFamily: "Georgia, serif",
					fontSize: 16,
					color: "#c9a961",
					textTransform: "uppercase",
					letterSpacing: 6,
				}}>
					Discover the collection
				</span>
			</div>

			{/* Title */}
			<div style={{ ...makeTextAnim(CONTENT_IN + 10), textAlign: "center" }}>
				<h2 style={{
					margin: 0,
					fontFamily: "Georgia, serif",
					fontSize: 58,
					fontWeight: "bold",
					color: "#ffffff",
					lineHeight: 1.2,
					textShadow: "0 4px 40px rgba(0,0,0,0.9)",
					textAlign: "center",
				}}>
					The Best of Charles Spurgeon<br />
					<span style={{ color: "#c9a961" }}>Books &amp; Devotionals</span>
				</h2>
			</div>

			{/* Large QR Code + glow */}
			<div style={{
				opacity: interpolate(frame, [CONTENT_IN + 20, CONTENT_IN + 40], [0, 1], {
					extrapolateLeft: "clamp",
					extrapolateRight: "clamp",
				}),
				transform: `scale(${qrScale})`,
				position: "relative",
				display: "flex",
				flexDirection: "column",
				alignItems: "center",
				gap: 16,
			}}>
				{/* Pulsing golden halo */}
				<div style={{
					position: "absolute",
					inset: -30,
					borderRadius: 24,
					boxShadow: `0 0 80px rgba(201,169,97,${glowOpacity})`,
					pointerEvents: "none",
				}} />

				{/* QR Card */}
				<div style={{
					background: "white",
					borderRadius: 16,
					padding: 20,
					boxShadow: "0 20px 60px rgba(0,0,0,0.8)",
				}}>
					<Img
						src={resolveAsset(qrCodeUrl)}
						width={280}
						height={280}
						style={{ display: "block", borderRadius: 4 }}
					/>
				</div>

				{/* Channel/Link Label */}
				<span style={{
					fontFamily: "Georgia, serif",
					fontSize: 20,
					color: "rgba(255,255,255,0.7)",
					fontStyle: "italic",
				}}>
					{linkLabel || CLEAN_LINK_LABEL}
				</span>
			</div>

			{/* Subtitle */}
			<div style={{ ...makeTextAnim(CONTENT_IN + 30), textAlign: "center" }}>
				<p style={{
					margin: 0,
					fontFamily: "Georgia, serif",
					fontSize: 20,
					color: "rgba(255,255,255,0.5)",
					letterSpacing: 1,
				}}>
					Scan the QR Code or click the link in the comments
				</p>
			</div>
		</div>
	);
};

// ─── COMPOSIÇÃO PRINCIPAL ────────────────────────────────────────────────────
export const SpurgeonCTA: React.FC<{ ctaAudioUrl?: string; qrCodeUrl?: string; linkLabel?: string }> = ({ ctaAudioUrl, qrCodeUrl, linkLabel }) => {
	const frame = useCurrentFrame();

	const { durationInFrames } = useVideoConfig();

	// Timings das cenas (em frames @30fps)
	const SCENE1_START = 0;
	const SCENE1_END   = Math.floor(durationInFrames / 2); // Metade para inscrição
	const CROSSFADE    = 30;  // 1s de crossfade
	const SCENE2_START = SCENE1_END;
	const TOTAL        = durationInFrames;

	// Opacidade de cada cena com crossfade
	const scene1Opacity = interpolate(
		frame,
		[SCENE1_START, SCENE1_START + 15, SCENE1_END - CROSSFADE, SCENE1_END],
		[0, 1, 1, 0],
		{ extrapolateLeft: "clamp", extrapolateRight: "clamp" }
	);

	const scene2Opacity = interpolate(
		frame,
		[SCENE2_START - CROSSFADE, SCENE2_START, TOTAL - 20, TOTAL],
		[0, 1, 1, 0],
		{ extrapolateLeft: "clamp", extrapolateRight: "clamp" }
	);

	// Frame local de cada cena
	const scene1Frame = Math.max(0, frame - SCENE1_START);
	const scene2Frame = Math.max(0, frame - (SCENE2_START - CROSSFADE));

	return (
		<AbsoluteFill style={{ backgroundColor: "#050302" }}>

			{/* ── FUNDO PERSISTENTE ── */}
			<AbsoluteFill>
				<Img
					src={staticFile("images/cathedral_bg_cf_3.png")}
					style={{
						width: "100%",
						height: "100%",
						objectFit: "cover",
						filter: "brightness(0.35) saturate(0.6)",
					}}
				/>
				<AbsoluteFill style={{
					background: "radial-gradient(ellipse at 50% 50%, transparent 20%, rgba(0,0,0,0.75) 80%)",
				}} />
				<AbsoluteFill style={{
					background: "linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 20%, transparent 80%, rgba(0,0,0,0.9) 100%)",
				}} />
			</AbsoluteFill>

			{/* Linha de brilho no topo */}
			<div style={{
				position: "absolute",
				top: 0,
				left: 0,
				right: 0,
				height: 2,
				background: "linear-gradient(90deg, transparent, #c9a961, transparent)",
				opacity: 0.6,
			}} />

			{/* ── NARRATIVE Audio (Kokoro) ── */}
			{ctaAudioUrl && <RemotionAudio src={resolveAsset(ctaAudioUrl)} />}

			{/* ── CENA 1: Inscrição ── */}
			<AbsoluteFill style={{ opacity: scene1Opacity }}>
				<SceneSubscribe frame={scene1Frame} />
			</AbsoluteFill>

			{/* ── CENA 2: QR Code Devocionais ── */}
			<AbsoluteFill style={{ opacity: scene2Opacity }}>
				<SceneQRCode frame={scene2Frame} qrCodeUrl={qrCodeUrl} linkLabel={linkLabel} />
			</AbsoluteFill>

		</AbsoluteFill>
	);
};
