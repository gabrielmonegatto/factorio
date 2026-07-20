import { staticFile } from "remotion";

/**
 * resolveAsset — resolve um caminho de asset para uma URL utilizável no render.
 *
 * Regra única da fábrica:
 *   - URL remota (http/https) ou data-URI  → usa direto (assets por-sermão vêm do R2)
 *   - caminho local ("images/x.png", "/images/x.png") → staticFile() (assets FIXOS empacotados no public/)
 *
 * Isso permite que o MESMO componente rode:
 *   - localmente (assets locais em public/)
 *   - no RunPods (assets por-sermão via URL do R2, assets fixos empacotados na imagem)
 */
export const resolveAsset = (path?: string | null): string => {
  if (!path) return "";
  if (/^https?:\/\//i.test(path) || path.startsWith("data:") || path.startsWith("blob:")) {
    return path;
  }
  return staticFile(path.startsWith("/") ? path.slice(1) : path);
};
