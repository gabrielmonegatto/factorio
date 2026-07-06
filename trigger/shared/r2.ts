/**
 * r2.ts — Utilitário central de acesso ao Cloudflare R2
 * Usado por todas as tasks do Factorio para upload/download de assets.
 *
 * Estrutura de paths no bucket 'mananciall':
 *   mananciapp/audio/{lang}/{bookSlug}/{unitSlug}/audio.mp3
 *   mananciapp/covers/{bookSlug}/cover.jpg
 *   channels/youtube/{bookSlug}/{unitSlug}/render.mp4
 */

import { S3Client, PutObjectCommand, GetObjectCommand, HeadObjectCommand } from "@aws-sdk/client-s3";
import * as fs from "fs";
import * as path from "path";

const R2_ENDPOINT          = process.env.R2_ENDPOINT!;
const R2_ACCESS_KEY_ID     = process.env.R2_ACCESS_KEY_ID!;
const R2_SECRET_ACCESS_KEY = process.env.R2_SECRET_ACCESS_KEY!;
const BUCKET_NAME          = "mananciall";

// URL pública do bucket (via r2.dev ou custom domain configurado no dash)
// Por ora usamos a URL S3-compatible que é acessível via presigned URLs
const R2_PUBLIC_BASE = process.env.R2_PUBLIC_URL ?? null;

export const r2Client = new S3Client({
  endpoint: R2_ENDPOINT,
  credentials: {
    accessKeyId:     R2_ACCESS_KEY_ID,
    secretAccessKey: R2_SECRET_ACCESS_KEY,
  },
  region: "auto",
  forcePathStyle: false,
});

/**
 * Faz upload de um arquivo local para o R2.
 * @returns A chave (path) do arquivo no bucket
 */
export async function uploadToR2(params: {
  localPath:   string;   // Caminho local do arquivo
  r2Key:       string;   // Destino no bucket, ex: "mananciapp/audio/en/spurgeon/fc-005/audio.mp3"
  contentType: string;   // "audio/mpeg", "image/jpeg", "application/json", etc.
}): Promise<string> {
  const { localPath, r2Key, contentType } = params;

  if (!fs.existsSync(localPath)) {
    throw new Error(`[R2] Arquivo não encontrado: ${localPath}`);
  }

  const fileBuffer = fs.readFileSync(localPath);

  await r2Client.send(new PutObjectCommand({
    Bucket:      BUCKET_NAME,
    Key:         r2Key,
    Body:        fileBuffer,
    ContentType: contentType,
  }));

  console.log(`✅ [R2] Upload concluído: ${r2Key} (${(fileBuffer.length / 1024).toFixed(1)} KB)`);
  return r2Key;
}

/**
 * Retorna a URL pública de um objeto no R2.
 * Requer que o bucket tenha acesso público habilitado no Cloudflare Dashboard.
 */
export function getR2PublicUrl(r2Key: string): string | null {
  if (!R2_PUBLIC_BASE) return null;
  return `${R2_PUBLIC_BASE.replace(/\/$/, "")}/${r2Key}`;
}

/**
 * Verifica se um objeto já existe no R2 (útil para idempotência).
 */
export async function existsInR2(r2Key: string): Promise<boolean> {
  try {
    await r2Client.send(new HeadObjectCommand({ Bucket: BUCKET_NAME, Key: r2Key }));
    return true;
  } catch {
    return false;
  }
}

// ── Helpers de nomenclatura padronizada ────────────────────────────────────

export function audioKey(lang: string, bookSlug: string, unitSlug: string): string {
  return `mananciapp/audio/${lang}/${bookSlug}/${unitSlug}/audio.mp3`;
}

export function transcriptKey(lang: string, bookSlug: string, unitSlug: string): string {
  return `mananciapp/transcripts/${lang}/${bookSlug}/${unitSlug}/transcript.json`;
}

export function coverKey(bookSlug: string): string {
  return `mananciapp/covers/${bookSlug}/cover.jpg`;
}

export function youtubeRenderKey(bookSlug: string, unitSlug: string): string {
  return `channels/youtube/${bookSlug}/${unitSlug}/render.mp4`;
}
