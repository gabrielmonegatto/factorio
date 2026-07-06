import React from "react";
import {
	Img,
	staticFile,
	spring,
	useCurrentFrame,
	useVideoConfig,
	interpolate,
	interpolateColors,
} from "remotion";

interface SubscribeUpperThirdProps {
	channelName?: string;
	/** Frame when the animation starts (default: 5s in) */
	showAtFrame?: number;
	/** Duration in frames to stay visible (default: 8s) */
	visibleDuration?: number;
	/** Repeat interval in frames (default: every 90s). Set 0 to show only once. */
	repeatInterval?: number;
}

export const SubscribeUpperThird: React.FC<SubscribeUpperThirdProps> = ({
	channelName = "Charles Spurgeon Treasures",
	showAtFrame,
	visibleDuration,
	repeatInterval,
}) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	const _showAt = showAtFrame ?? 5 * fps;
	const _visible = visibleDuration ?? 8 * fps;
	const _repeat = repeatInterval ?? 90 * fps;

	// Determine local frame within the cycle
	let localFrame: number;
	if (_repeat === 0) {
		localFrame = frame; // show once
	} else {
		localFrame = frame % _repeat;
	}

	const isInWindow = localFrame >= _showAt && localFrame < _showAt + _visible + fps * 2; // extra 2s for exit anim

	if (!isInWindow) return null;

	const windowFrame = localFrame - _showAt;

	// Entry: slide down from above
	const enterProgress = spring({
		frame: windowFrame,
		fps,
		config: { stiffness: 120, damping: 18 },
	});

	// Exit: slide back up
	const exitProgress = spring({
		frame: windowFrame - _visible,
		fps,
		config: { stiffness: 100, damping: 20 },
	});

	const translateY = interpolate(
		enterProgress - exitProgress,
		[0, 1],
		[-120, 0]
	);

	const opacity = interpolate(
		enterProgress - exitProgress,
		[0, 0.3, 1],
		[0, 1, 1],
		{ extrapolateLeft: "clamp", extrapolateRight: "clamp" }
	);

	// Click animation at 3 seconds in
	const clickFrame = 3 * fps;
	const isClicked = windowFrame >= clickFrame;

	const clickSpring = spring({
		frame: windowFrame - clickFrame,
		fps,
		config: { stiffness: 300, damping: 15 },
	});

	// Cor mais "morta" de fundo, tipo um botão desativado/esperando clique
	const bgColor = interpolateColors(
		clickSpring,
		[0, 1],
		["rgba(255, 255, 255, 0.15)", "rgba(204, 0, 0, 1)"]
	);

	// Texto levemente apagado que "acende" no branco puro
	const textColor = interpolateColors(
		clickSpring,
		[0, 1],
		["rgba(255, 255, 255, 0.6)", "rgba(255, 255, 255, 1)"]
	);

	// Pulse only before click
	const pulse = windowFrame < clickFrame 
		? interpolate(Math.sin(windowFrame * 0.08), [-1, 1], [1, 1.05])
		: 1;

	// Scale down on click, then back to 1
	const buttonScale = windowFrame < clickFrame
		? pulse
		: interpolate(clickSpring, [0, 0.3, 1], [pulse, 0.9, 1], { extrapolateRight: "clamp" });

	const shadowOpacity = interpolate(clickSpring, [0, 1], [0, 0.4]);

	return (
		<div
			style={{
				position: "absolute",
				top: 50,
				left: 0,
				right: 0,
				display: "flex",
				justifyContent: "center",
				transform: `translateY(${translateY}px)`,
				opacity,
				pointerEvents: "none",
				zIndex: 100,
			}}
		>
			<div
				style={{
					display: "flex",
					alignItems: "center",
					gap: 16,
					background: "rgba(0, 0, 0, 0.75)",
					backdropFilter: "blur(20px)",
					borderRadius: 60,
					padding: "10px 24px 10px 10px",
					boxShadow: "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.08)",
				}}
			>
				{/* Channel Avatar */}
				<div
					style={{
						width: 52,
						height: 52,
						borderRadius: "50%",
						overflow: "hidden",
						flexShrink: 0,
						border: "2px solid rgba(201, 169, 97, 0.6)",
						boxShadow: "0 0 12px rgba(201, 169, 97, 0.3)",
					}}
				>
					<Img
						src={staticFile("images/spurgeon_avatar.png")}
						style={{
							width: "100%",
							height: "100%",
							objectFit: "cover",
						}}
					/>
				</div>

				{/* Channel Name */}
				<span
					style={{
						fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
						fontSize: 18,
						fontWeight: 500,
						color: "rgba(255,255,255,0.95)",
						letterSpacing: 0.5,
						whiteSpace: "nowrap",
					}}
				>
					{channelName}
				</span>

				{/* Subscribe Button */}
				<div
					style={{
						background: bgColor,
						borderRadius: 20,
						padding: "8px 20px",
						display: "flex",
						alignItems: "center",
						gap: 6,
						transform: `scale(${buttonScale})`,
						boxShadow: `0 4px 12px rgba(204,0,0,${shadowOpacity})`,
						transition: "width 0.3s ease",
						overflow: "hidden",
					}}
				>
					{/* Icon */}
					<div style={{ position: "relative", width: 14, height: 14 }}>
						{/* Plus Icon (fade out) */}
						<svg
							width="14"
							height="14"
							viewBox="0 0 24 24"
							fill={textColor}
							style={{
								position: "absolute",
								opacity: interpolate(clickSpring, [0, 1], [1, 0]),
								transform: `rotate(${interpolate(clickSpring, [0, 1], [0, 90])}deg)`
							}}
						>
							<path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
						</svg>
						{/* Checkmark Icon (fade in) */}
						<svg
							width="14"
							height="14"
							viewBox="0 0 24 24"
							fill={textColor}
							style={{
								position: "absolute",
								opacity: interpolate(clickSpring, [0, 1], [0, 1]),
								transform: `scale(${interpolate(clickSpring, [0.5, 1], [0, 1])})`
							}}
						>
							<path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
						</svg>
					</div>

					<span
						style={{
							fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
							fontSize: 14,
							fontWeight: 600,
							color: textColor,
							textTransform: "uppercase",
							letterSpacing: 1,
						}}
					>
						{isClicked ? "Subscribed!" : "Subscribe"}
					</span>
				</div>
			</div>
		</div>
	);
};
