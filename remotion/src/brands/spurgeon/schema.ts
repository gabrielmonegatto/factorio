import { z } from "zod";

export const sermonMasterSchema = z.object({
  // Audio
  narrationUrl: z.string(),
  bgmUrl: z.string().default("/audio/bg_music_piano.mp3"),
  bgmVolume: z.number().min(0).max(0.15).default(0.08),

  // Visual
  backgroundImageUrl: z.string(),
  preacherImageUrl: z.string(),
  kenBurnsIntensity: z.enum(["subtle", "normal", "dynamic"]).default("subtle"),

  // Subtitles
  transcriptSlug: z.string(), // Slug para puxar o JSON
  subtitleStyle: z.enum(["classic", "modern", "minimal"]).default("modern"),

  // Marketing
  qrCodeUrl: z.string(),
  ctaBookUrl: z.string().optional(),
  ctaBookTitle: z.string().optional(),

  // MARCA — tudo que o espectador LÊ na tela. Estava cravado dentro dos
  // componentes, e por isso o 1º vídeo do Moody exibiu "The Best of Charles
  // Spurgeon" no CTA. Vem do canais.py via build_job. Opcional pra não
  // quebrar props antigos; o componente cai num texto neutro se faltar.
  channelName: z.string().optional(),
  preacherName: z.string().optional(),
  collectionTitle: z.string().optional(),
  linkLabel: z.string().optional(),

  // Meta
  sermonTitle: z.string(),
  sermonNumber: z.string(),

  // V2 Timeline Elements (Hook, Brand, End Screen)
  hookAudioUrl: z.string().optional(),
  hookTranscriptSlug: z.string().optional(),
  hookDurationFrames: z.number().optional(),

  introCtaAudioUrl: z.string().optional(),
  introCtaTranscriptSlug: z.string().optional(),
  introCtaDurationFrames: z.number().optional(),

  outroHookAudioUrl: z.string().optional(),
  outroHookTranscriptSlug: z.string().optional(),
  outroHookDurationFrames: z.number().optional(),

  outroCtaAudioUrl: z.string().optional(),
  outroCtaTranscriptSlug: z.string().optional(),
  outroCtaDurationFrames: z.number().optional(),

  marketingTitle: z.string().optional(),
});

export type SermonMasterProps = z.infer<typeof sermonMasterSchema>;
