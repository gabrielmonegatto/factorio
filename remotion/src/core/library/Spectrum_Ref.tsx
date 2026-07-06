import { useWindowedAudioData, visualizeAudio } from "@remotion/media-utils";
import { useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

// Nota: AudioVizContainer e constants são dependências locais do template-audiogram original.
// Este arquivo serve como REFERÊNCIA de lógica para usar getWindowedAudioData e visualizeAudio.

const BASE_SIZE = 20;

const AudioVizContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        {children}
    </div>
);

const Bar: React.FC<{ height: number; color: string }> = ({
    height,
    color,
}) => {
    const barStyle: React.CSSProperties = {
        borderRadius: `${BASE_SIZE * 0.25}px`,
        width: `${BASE_SIZE * 0.5}px`,
        height: `${height}px`,
        backgroundColor: color,
    };

    return <div style={barStyle} />;
};

export const Spectrum: React.FC<{
    readonly barColor: string;
    readonly numberOfSamples: number;
    readonly freqRangeStartIndex: number;
    readonly waveLinesToDisplay: number;
    readonly mirrorWave: boolean;
    readonly audioSrc: string;
}> = ({
    barColor,
    numberOfSamples,
    freqRangeStartIndex,
    waveLinesToDisplay,
    mirrorWave,
    audioSrc,
}) => {
        const frame = useCurrentFrame();
        const { fps } = useVideoConfig();

        const { audioData, dataOffsetInSeconds } = useWindowedAudioData({
            src: audioSrc,
            fps,
            frame,
            windowInSeconds: 10,
        });

        if (!audioData) {
            return <AudioVizContainer children={null} />;
        }

        const frequencyData = visualizeAudio({
            fps,
            frame,
            audioData,
            numberOfSamples,
            optimizeFor: "speed",
            dataOffsetInSeconds,
        });

        const frequencyDataSubset = frequencyData.slice(
            freqRangeStartIndex,
            freqRangeStartIndex +
            (mirrorWave ? Math.round(waveLinesToDisplay / 2) : waveLinesToDisplay),
        );

        const frequenciesToDisplay = mirrorWave
            ? [...frequencyDataSubset.slice(1).reverse(), ...frequencyDataSubset]
            : frequencyDataSubset;

        return (
            <AudioVizContainer>
                {frequenciesToDisplay.map((v, i) => {
                    return <Bar key={i} height={300 * Math.sqrt(v)} color={barColor} />;
                })}
            </AudioVizContainer>
        );
    };
