import React from 'react';
import { AbsoluteFill } from 'remotion';

interface LetterboxProps {
    type: 'horizontal' | 'vertical';
    size: number; // Porcentagem (ex: 10 para 10%)
}

export const Letterbox: React.FC<LetterboxProps> = ({ type, size }) => {
    const barStyle: React.CSSProperties = {
        position: 'absolute',
        backgroundColor: 'black',
        zIndex: 100,
    };

    if (type === 'horizontal') {
        return (
            <AbsoluteFill style={{ pointerEvents: 'none' }}>
                <div style={{ ...barStyle, top: 0, left: 0, right: 0, height: `${size}%` }} />
                <div style={{ ...barStyle, bottom: 0, left: 0, right: 0, height: `${size}%` }} />
            </AbsoluteFill>
        );
    }

    return (
        <AbsoluteFill style={{ pointerEvents: 'none' }}>
            <div style={{ ...barStyle, top: 0, bottom: 0, left: 0, width: `${size}%` }} />
            <div style={{ ...barStyle, top: 0, bottom: 0, right: 0, width: `${size}%` }} />
        </AbsoluteFill>
    );
};
