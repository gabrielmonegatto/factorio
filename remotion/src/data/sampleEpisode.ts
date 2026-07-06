// Gerado automaticamente via pipeline/generate_episode_data.py
export const sampleBibleEpisode = {
    durationInFrames: 1674,
    channel: {
        name: "Maná Diário",
        subtitle: "Bíblia Narrada",
    },
    reference: {
        book: "Salmos",
        chapter: 23,
        translation: "ACF",
    },
    sections: [
        {
            id: "v1",
            startFrame: 103,
            text: "O SENHOR é o meu pastor, nada me faltará.",
            verseRef: "v. 1",
        },
        {
            id: "v2",
            startFrame: 241,
            text: "Deitar-me faz em verdes pastos, guia-me mansamente a águas tranqüilas.",
            verseRef: "v. 2",
        },
        {
            id: "v3",
            startFrame: 471,
            text: "Refrigera a minha alma; guia-me pelas veredas da justiça, por amor do seu nome.",
            verseRef: "v. 3",
        },
        {
            id: "v4",
            startFrame: 676,
            text: "Ainda que eu andasse pelo vale da sombra da morte, não temeria mal algum, porque tu estás comigo; a tua vara e o teu cajado me consolam.",
            verseRef: "v. 4",
        },
        {
            id: "v5",
            startFrame: 1011,
            text: "Preparas uma mesa perante mirn na presença dos meus inimigos, unges a minha cabeça com óleo, o meu cálice transborda.",
            verseRef: "v. 5",
        },
        {
            id: "v6",
            startFrame: 1292,
            text: "Certamente que a bondade e a misericórdia me seguirão todos os dias da minha vida; e habitarei na casa do Senhor por longos dias.",
            verseRef: "v. 6",
        }
    ],
    audioSrc: "/audio/sl-023-acf.wav",
    bgAsset: "" as string | undefined,
    ambientSrc: "/audio/ambient_night.mp3" as string | undefined,
    bgMusicSrc: "/audio/bg_music_piano.mp3" as string | undefined,
};

export type EpisodeProps = typeof sampleBibleEpisode;
