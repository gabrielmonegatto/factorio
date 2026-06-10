import { AbsoluteFill } from "remotion";
import { Background } from "../../../core/components/Background";
import { Letterbox } from "../../../core/effects/Letterbox";

export const LetterboxDemo: React.FC<{ type: 'horizontal' | 'vertical' }> = ({ type }) => {
    return (
        <AbsoluteFill style={{ backgroundColor: '#111' }}>
            <Background frame={0} totalFrames={300} />
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                color: 'white',
                fontSize: 40,
                fontFamily: 'Cinzel',
                textAlign: 'center',
                padding: 100
            }}>
                Exemplo de Letterbox<br />
                Tipo: {type}<br />
                100% via Código
            </div>
            <Letterbox type={type} size={10} />
        </AbsoluteFill>
    );
};
