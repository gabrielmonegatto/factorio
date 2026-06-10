import React from 'react';
import {
    useCurrentFrame,
    useVideoConfig,
    staticFile,
} from 'remotion';
import { useAudioData, visualizeAudio } from '@remotion/media-utils';

interface AudioVisualizerProps {
    audioSrc: string;
    numberOfSamples?: number;
    color?: string;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
    audioSrc,
    numberOfSamples = 64,
    color = "#ffd700"
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const audioData = useAudioData(staticFile(audioSrc));

    if (!audioData) {
        return null;
    }

    const visualization = visualizeAudio({
        fps,
        frame,
        audioData,
        numberOfSamples, // Deve ser potência de 2
    });

    // Filtramos apenas as frequências médias/baixas para um visual mais limpo (as primeiras 32)
    const displayFrequencies = visualization.slice(0, 32);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
            width: '100%',
            height: '100px',
        }}>
            {displayFrequencies.map((amplitude, i) => {
                // Efeito de espelhamento (centro para fora)
                const height = Math.max(4, amplitude * 100);
                
                return (
                    <div
                        key={i}
                        style={{
                            width: '4px',
                            height: `${height}px`,
                            backgroundColor: color,
                            borderRadius: '2px',
                            opacity: 0.6 + (amplitude * 0.4),
                            boxShadow: `0 0 10px ${color}44`,
                        }}
                    />
                );
            })}
        </div>
    );
};
