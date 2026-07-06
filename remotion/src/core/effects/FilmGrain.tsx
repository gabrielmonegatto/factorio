import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { noise2D } from '@remotion/noise';

interface FilmGrainProps {
    opacity?: number;
    seed?: number;
}

export const FilmGrain: React.FC<FilmGrainProps> = ({ opacity = 0.05, seed = 1 }) => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();

    // Criamos uma pequena textura de ruído e escalamos para cobrir a tela
    // Isso é mais performático do que gerar ruído para cada pixel individualmente
    const grainSize = 2; // Tamanho do grão em pixels
    const cols = Math.ceil(width / grainSize);
    const rows = Math.ceil(height / grainSize);

    return (
        <AbsoluteFill style={{ pointerEvents: 'none', opacity }}>
            <canvas
                ref={(canvas) => {
                    if (!canvas) return;
                    const ctx = canvas.getContext('2d');
                    if (!ctx) return;

                    ctx.clearRect(0, 0, width, height);

                    // Usamos o frame como parte do seed para o ruído mudar a cada quadro
                    for (let x = 0; x < cols; x++) {
                        for (let y = 0; y < rows; y++) {
                            // Gerar valor de ruído entre 0 e 1
                            const n = noise2D(seed, x + frame * 10, y + frame * 10);
                            const val = Math.floor((n + 1) * 127.5);
                            ctx.fillStyle = `rgb(${val}, ${val}, ${val})`;
                            ctx.fillRect(x * grainSize, y * grainSize, grainSize, grainSize);
                        }
                    }
                }}
                width={width}
                height={height}
                style={{ width: '100%', height: '100%', mixBlendMode: 'overlay' }}
            />
        </AbsoluteFill>
    );
};
