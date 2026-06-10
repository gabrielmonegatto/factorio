import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { SubscribeUpperThird } from "../components/SubscribeUpperThird";

/**
 * Composição isolada para visualizar o UpperThird de Subscribe.
 * Mostra sobre o fundo da catedral para contexto fiel ao vídeo final.
 */
export const SubscribePreview: React.FC = () => {
	return (
		<AbsoluteFill>
			{/* Background contextual */}
			<AbsoluteFill>
				<Img
					src={staticFile("images/cathedral_bg_cf_1.png")}
					style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.85 }}
				/>
				<AbsoluteFill
					style={{
						background: "linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.2) 100%)",
					}}
				/>
			</AbsoluteFill>

			{/* UpperThird Subscribe — showAtFrame=15 para ver rápido no preview */}
			<SubscribeUpperThird
				channelName="Charles Spurgeon Treasures"
				showAtFrame={15}
				visibleDuration={240}
				repeatInterval={0}
			/>
		</AbsoluteFill>
	);
};
