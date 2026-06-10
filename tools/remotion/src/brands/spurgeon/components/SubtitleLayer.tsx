import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

export interface Word {
	text: string;
	start: number;
	end: number;
	confidence: number;
}

// ─── REGRAS DE LEGENDAGEM PROFISSIONAL (TV/CINEMA) ───
// 1. Máximo 2 linhas por bloco
// 2. Máximo ~42 caracteres por linha
// 3. Nunca separar artigo/preposição do seu substantivo
// 4. Preferir quebra em pontuação natural
// 5. Cada bloco = uma unidade lógica de pensamento

const MAX_CHARS_PER_LINE = 42;
const MAX_LINES = 2;

// Palavras que NUNCA devem ficar sozinhas no fim de uma linha
// (artigos, preposições, conjunções curtas)
const GLUE_WORDS = new Set([
	"a", "an", "the", "of", "in", "on", "at", "to", "for",
	"by", "with", "from", "and", "but", "or", "nor", "as",
	"is", "it", "its", "my", "his", "her", "our", "your",
	"their", "this", "that", "no", "not", "so", "if", "be",
]);

// Verifica se uma palavra termina com pontuação forte (fim de frase/cláusula)
function endsWithPunctuation(text: string): boolean {
	return /[.,;:!?…—\-]$/.test(text);
}

// Verifica se é pontuação de FIM de sentença (pausa longa)
function endsWithSentenceEnd(text: string): boolean {
	return /[.!?…]$/.test(text);
}

interface SubtitleCue {
	words: Word[];
	text: string;   // texto formatado (pode ter \n)
	start: number;  // timestamp da primeira palavra (ms)
	end: number;    // timestamp da última palavra (ms)
}

/**
 * Segmenta as palavras em blocos de legenda profissionais.
 * Cada bloco tem no máximo 2 linhas de ~42 caracteres,
 * respeitando limites naturais de frase.
 */
function buildCues(words: Word[]): SubtitleCue[] {
	if (words.length === 0) return [];

	const cues: SubtitleCue[] = [];
	let currentLine = "";
	let lines: string[] = [];
	let cueWords: Word[] = [];

	function flushCue() {
		if (lines.length > 0 || currentLine.length > 0) {
			if (currentLine.length > 0) {
				lines.push(currentLine.trim());
			}
			if (cueWords.length > 0) {
				cues.push({
					words: [...cueWords],
					text: lines.join("\n"),
					start: cueWords[0].start,
					end: cueWords[cueWords.length - 1].end,
				});
			}
			lines = [];
			currentLine = "";
			cueWords = [];
		}
	}

	function flushLine() {
		if (currentLine.length > 0) {
			lines.push(currentLine.trim());
			currentLine = "";
		}
	}

	for (let i = 0; i < words.length; i++) {
		const word = words[i];
		const wordText = word.text;
		const testLine = currentLine.length === 0 
			? wordText 
			: currentLine + " " + wordText;

		// Se adicionar esta palavra estoura a linha
		if (testLine.length > MAX_CHARS_PER_LINE && currentLine.length > 0) {
			// Verifica se a última palavra da linha é uma "glue word"
			// Se for, leva ela junto pra próxima linha
			const lastSpace = currentLine.lastIndexOf(" ");
			if (lastSpace > 0) {
				const lastWord = currentLine.substring(lastSpace + 1).toLowerCase().replace(/[.,;:!?]/g, "");
				if (GLUE_WORDS.has(lastWord)) {
					// Move a glue word para a próxima linha
					const beforeGlue = currentLine.substring(0, lastSpace);
					const glueWord = currentLine.substring(lastSpace + 1);
					currentLine = beforeGlue;
					flushLine();
					currentLine = glueWord + " " + wordText;
					cueWords.push(word);

					// Se já tem 2 linhas, fecha o cue
					if (lines.length >= MAX_LINES) {
						flushCue();
					}
					continue;
				}
			}

			flushLine();

			// Se já tem 2 linhas completas, fecha o cue
			if (lines.length >= MAX_LINES) {
				flushCue();
			}

			currentLine = wordText;
			cueWords.push(word);
		} else {
			currentLine = testLine;
			cueWords.push(word);
		}

		// Se a palavra termina com pontuação forte, é um ponto natural de quebra
		if (endsWithSentenceEnd(wordText)) {
			// Fim de sentença → fecha o cue inteiro
			flushCue();
		} else if (endsWithPunctuation(wordText) && lines.length >= 1) {
			// Pontuação média (vírgula, ponto-vírgula) + já tem uma linha → fecha
			flushCue();
		}
	}

	// Flush qualquer coisa que sobrou
	flushCue();

	return cues;
}

// ─── COMPONENTE ───

interface SubtitleLayerProps {
	words: Word[];
	style?: React.CSSProperties;
}

export const SubtitleLayer: React.FC<SubtitleLayerProps> = ({ words, style }) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();
	const currentTimeMs = (frame / fps) * 1000;

	if (!words || words.length === 0) return null;

	// Segmenta apenas uma vez (React vai cachear entre renders do mesmo frame)
	const cues = buildCues(words);

	// Encontra o cue ativo: o último cue cujo start <= currentTimeMs
	let activeCue: SubtitleCue | null = null;
	for (let i = cues.length - 1; i >= 0; i--) {
		if (currentTimeMs >= cues[i].start) {
			// Só mostra se ainda estamos dentro do tempo do cue
			// (ou até 500ms depois do último end, para não sumir instantaneamente)
			if (currentTimeMs <= cues[i].end + 500) {
				activeCue = cues[i];
			}
			break;
		}
	}

	if (!activeCue) return null;

	return (
		<div
			style={{
				position: "absolute",
				bottom: "6%",
				left: 0,
				width: "100%",
				display: "flex",
				justifyContent: "center",
				...style,
			}}
		>
			<div
				style={{
					color: "white",
					fontSize: 48,
					fontWeight: 700,
					textAlign: "center",
					maxWidth: "80%",
					fontFamily: "Georgia, serif",
					lineHeight: 1.4,
					textShadow: "2px 2px 8px rgba(0,0,0,0.95), 0 0 20px rgba(0,0,0,0.8)",
					textTransform: "uppercase",
					letterSpacing: 1,
					whiteSpace: "pre-line",
				}}
			>
				{activeCue.text}
			</div>
		</div>
	);
};
