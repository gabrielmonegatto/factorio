import React from "react";
import { useCurrentFrame, random, useVideoConfig, spring, interpolate } from "remotion";

// REFERÊNCIA de Animação de Texto extraída de remotion-bits.
// Mostra a lógica de split de caracteres e animação individual com stagger.

export const AnimatedText: React.FC<{
    children: string;
    splitStagger?: number;
}> = ({
    children,
    splitStagger = 0.1,
}) => {
        const frame = useCurrentFrame();
        const { fps } = useVideoConfig();

        const units = children.split("");

        const renderUnit = (unit: string, index: number) => {
            const delay = index * splitStagger * fps;
            const progress = spring({
                frame: frame - delay,
                fps,
                config: { damping: 10 }
            });

            const opacity = interpolate(progress, [0, 1], [0, 1]);
            const translateY = interpolate(progress, [0, 1], [20, 0]);

            return (
                <span key={index} style={{
                    display: "inline-block",
                    whiteSpace: "pre",
                    opacity,
                    transform: `translateY(${translateY}px)`
                }}>
                    {unit}
                </span>
            );
        };

        return (
            <div style={{ display: "inline-block" }}>
                {units.map(renderUnit)}
            </div>
        );
    };
