import { EpisodeProps } from "./sampleEpisode";

export const salmo1PortraitData: EpisodeProps = {
    durationInFrames: 1650,
    channel: {
        name: "Maná Diário",
        subtitle: "Bíblia Narrada",
    },
    reference: {
        book: "Salmos",
        chapter: 1,
        translation: "ACF",
    },
    sections: [
        {
            id: "v1",
            startFrame: 90,
            text: "Bem-aventurado o homem que não anda segundo o conselho dos ímpios, nem se detém no caminho dos pecadores, nem se assenta na roda dos escarnecedores.",
            verseRef: "v. 1",
        },
        {
            id: "v2",
            startFrame: 350,
            text: "Antes tem o seu prazer na lei do Senhor, e na sua lei medita de dia e de noite.",
            verseRef: "v. 2",
        },
        {
            id: "v3",
            startFrame: 580,
            text: "Pois será como a árvore plantada junto a ribeiros de águas, a qual dá o seu fruto no seu tempo; as suas folhas não cairão, e tudo quanto fizer prosperará.",
            verseRef: "v. 3",
        },
        {
            id: "v4",
            startFrame: 920,
            text: "Não são assim os ímpios; mas são como a moinha que o vento espalha.",
            verseRef: "v. 4",
        },
        {
            id: "v5",
            startFrame: 1150,
            text: "Por isso os ímpios não subsistirão no juízo, nem os pecadores na congregação dos justos.",
            verseRef: "v. 5",
        },
        {
            id: "v6",
            startFrame: 1380,
            text: "Porque o Senhor conhece o caminho dos justos; porém o caminho dos ímpios perecerá.",
            verseRef: "v. 6",
        }
    ],
    audioSrc: "/bible/pt-br/chirp3_algieba/salmos/salmos_001.wav",
    bgAsset: "/visuals/sky/videos/portrait/pexels_vid_30560393.mp4",
    ambientSrc: "/visuals/sky/audio/ambient_wind_loop.wav",
    bgMusicSrc: "/assets/audio/frequencies/peaceful_freesound_524853.wav",
};

export const salmo1LandscapeData: EpisodeProps = {
    ...salmo1PortraitData,
    bgAsset: "/visuals/sky/videos/landscape/pexels_vid_30560632.mp4",
};
