import { AbsoluteFill } from "remotion";
import { Background } from "../../../core/components/Background";
import { FilmGrain } from "../../../core/effects/FilmGrain";

export const FilmGrainDemo: React.FC<{ opacity: number; label: string }> = ({ opacity, label }) => {
    return (
        <AbsoluteFill style={{ backgroundColor: '#111' }}>
            <Background frame={0} totalFrames={300} />
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                color: 'white',
                fontSize: 40,
                fontFamily: 'Cinzel',
                textAlign: 'center',
                padding: 100,
                zIndex: 10
            }}>
                <span style={{ fontSize: 60, color: '#5eb8bc' }}>{label}</span>
                <div style={{ height: 20 }} />
                Exemplo de Film Grain Procedural<br />
                Opacidade: {opacity * 100}%<br />
                100% via Código (Zero Assets)
            </div>
            <FilmGrain opacity={opacity} />
        </AbsoluteFill>
    );
};
