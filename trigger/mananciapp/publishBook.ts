/**
 * publishBook.ts — Esteira de Produtização do Mananciapp
 *
 * Responsabilidade: Pegar conteúdo pronto no banco (mineration_content)
 * e publicar como arquivo Markdown no portal Mananciapp (Astro).
 *
 * Fluxo:
 *   1. Busca registros prontos no banco (pipeline_state.published_en = null)
 *   2. Gera o arquivo .md na estrutura src/content/livros/en/{bookSlug}/
 *   3. Atualiza pipeline_state no banco → published_en: 'done'
 *   4. Se todos os capítulos do livro estiverem publicados → dispara deploy
 */

import { task } from "@trigger.dev/sdk/v3";
import { Client } from "pg";
import * as fs from "fs";
import * as path from "path";

const DB_URL = process.env.DATABASE_URL || "postgresql://teable:teable_secret_password@localhost:42345/teable";
const SCHEMA    = "bseWeczeNfCSaMlu2EC";
const TBL_CONTENT = `"${SCHEMA}"."tblFyPPXJTiynzBKFH2"`;
const TBL_INDEX   = `"${SCHEMA}"."tblD7Kxoc7gFTgEWoWo"`;

const SCHEMA_WORKFLOW = "bseWeczeNfCSaMlu2EC";
const TBL_TASKS = `"${SCHEMA_WORKFLOW}"."tblVzN1Eo8tfk7GX2CJ"`;

const MANANCIAPP_CONTENT_DIR = path.resolve(__dirname, "../../../apps/mananciapp/src/content/livros");

// ── Helpers ─────────────────────────────────────────────────────────────────

function slugify(str: string): string {
  return str
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function buildMarkdown(params: {
  title:         string;
  author:        string;
  bookTitle:     string;
  bookId:        string;
  chapterNumber: number;
  description?:  string;
  coverImage?:   string;
  audioUrl?:     string;
  verse?:        string;
  verseRef?:     string;
  content:       string;
}): string {
  const { title, author, bookTitle, bookId, chapterNumber, description, coverImage, audioUrl, verse, verseRef, content } = params;

  const frontmatter: Record<string, any> = {
    title,
    bookId,
    bookTitle,
    author,
    chapterNumber,
    ...(description ? { description } : {}),
    ...(coverImage  ? { coverImage }  : {}),
    ...(audioUrl    ? { audioUrl }    : {}),
    ...(verse       ? { verse }       : {}),
    ...(verseRef    ? { verseRef }    : {}),
  };

  const fm = Object.entries(frontmatter)
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join("\n");

  return `---\n${fm}\n---\n\n${content.trim()}\n`;
}

// ── Task Principal ───────────────────────────────────────────────────────────

interface PublishPayload {
  bookIndexId?: string;   // Se passado, publica apenas este livro. Senão, publica todos prontos.
  limit?: number;
  taskId?: string;        // ID da tarefa universal para atualização
}

export async function runPublishMananciappBooks(payload: PublishPayload) {
    const { bookIndexId, limit = 50, taskId } = payload;
    const db = new Client({ connectionString: DB_URL });
    await db.connect();

    try {
      let bookAutoNumberText = "";
      if (bookIndexId) {
        const bookInfo = await db.query(`SELECT __auto_number::text as auto_num FROM ${TBL_INDEX} WHERE __id = $1`, [bookIndexId]);
        if (bookInfo.rows.length > 0) {
          bookAutoNumberText = bookInfo.rows[0].auto_num ?? "";
        }
      }

      // ── Busca unidades prontas (scraped/concluido) sem published_en ──────
      const whereBook = bookIndexId
        ? `AND (mc.index_id = $2 OR mc.index_id = $3)`
        : "";

      const query = `
        SELECT
          mc.__id,
          mc.title,
          mc.author,
          mc.book_name,
          mc.content,
          mc.metadata,
          mc.pipeline_state,
          mc.index_id,
          ci."Name" as book_index_name
        FROM ${TBL_CONTENT} mc
        LEFT JOIN ${TBL_INDEX} ci ON (ci.__id = mc.index_id OR ci.__auto_number::text = mc.index_id)
        WHERE mc.content IS NOT NULL
          AND mc.content != ''
          AND (
            mc.pipeline_state IS NULL
            OR mc.pipeline_state->'published_en'->>'status' IS NULL
          )
          ${whereBook}
        ORDER BY mc.__id ASC
        LIMIT $1
      `;

      const queryParams: any[] = [limit];
      if (bookIndexId) queryParams.push(bookIndexId, bookAutoNumberText);

      const { rows } = await db.query(query, queryParams);
      console.log(`📚 [mananciapp/publish] ${rows.length} unidades encontradas para publicar.`);

      if (rows.length === 0) {
        if (taskId) {
          console.log(`📝 [mananciapp/publish] Nenhuma unidade para publicar. Concluindo tarefa ${taskId}...`);
          await db.query(`
            UPDATE ${TBL_TASKS}
            SET "Status" = 'Concluído', "resultado" = 'Nenhuma unidade pendente para publicar.', __last_modified_time = NOW()
            WHERE __id = $1
          `, [taskId]);
        }
        return { status: "nothing_to_publish" };
      }

      // ── Agrupa na memória por baseTitle (removendo o sufixo " - Parte X") ──────
      const groups = new Map<string, any[]>();
      for (const unit of rows) {
        const title = unit.title ?? "Untitled";
        const baseTitle = title.replace(/\s*-\s*Parte\s+\d+$/i, "").trim();
        if (!groups.has(baseTitle)) {
          groups.set(baseTitle, []);
        }
        groups.get(baseTitle)!.push(unit);
      }

      const results = { published: 0, failed: 0, errors: [] as string[] };

      for (const [baseTitle, units] of groups.entries()) {
        try {
          // Ordena as unidades do grupo pelo número da parte
          units.sort((a, b) => {
            const matchA = (a.title ?? "").match(/Parte\s+(\d+)$/i);
            const matchB = (b.title ?? "").match(/Parte\s+(\d+)$/i);
            const partA = matchA ? parseInt(matchA[1], 10) : 1;
            const partB = matchB ? parseInt(matchB[1], 10) : 1;
            return partA - partB;
          });

          // Concatena os conteúdos das partes
          const concatenatedContent = units.map(u => u.content ?? "").join("\n\n");

          // Usa a primeira unidade como referência de metadados
          const refUnit = units[0];
          let meta: Record<string, any> = {};
          try { meta = JSON.parse(refUnit.metadata ?? "{}"); } catch {}

          const bookName   = refUnit.book_name ?? refUnit.book_index_name ?? "Unknown Book";
          const bookSlug   = slugify(bookName);
          const unitSlug   = slugify(baseTitle);
          const lang       = "en";

          const state = refUnit.pipeline_state ?? {};
          const audioUrl = state.narration_en?.r2_url || undefined;

          // Monta o markdown unificado
          const md = buildMarkdown({
            title:         baseTitle,
            author:        refUnit.author ?? "Charles H. Spurgeon",
            bookTitle:     bookName,
            bookId:        bookSlug,
            chapterNumber: meta.chapter_number ?? meta.day_number ?? 0,
            description:   meta.description || undefined,
            coverImage:    meta.cover_image || undefined,
            audioUrl,
            verse:         meta.verse_en || undefined,
            verseRef:      meta.verse_reference || undefined,
            content:       concatenatedContent,
          });

          // Garante que o diretório existe
          const dir = path.join(MANANCIAPP_CONTENT_DIR, lang, bookSlug);
          fs.mkdirSync(dir, { recursive: true });

          // Escreve o arquivo unificado
          const filePath = path.join(dir, `${unitSlug}.md`);
          fs.writeFileSync(filePath, md, "utf-8");

          console.log(`✅ [mananciapp/publish] Publicado: ${lang}/${bookSlug}/${unitSlug}.md (Concatenado de ${units.length} partes)`);

          // Atualiza pipeline_state no banco para todas as partes do grupo
          const now = new Date().toISOString();
          for (const u of units) {
            const currentState = u.pipeline_state ?? {};
            const newState = {
              ...currentState,
              published_en: {
                status:     "done",
                path:       `livros/${lang}/${bookSlug}/${unitSlug}`,
                updated_at: now,
              },
            };

            await db.query(`
              UPDATE ${TBL_CONTENT}
              SET pipeline_state = $1::jsonb, __last_modified_time = NOW()
              WHERE __id = $2
            `, [JSON.stringify(newState), u.__id]);

            results.published++;
          }
        } catch (err: any) {
          console.error(`❌ [mananciapp/publish] Erro em ${baseTitle}: ${err.message}`);
          results.failed += units.length;
          results.errors.push(`${baseTitle}: ${err.message}`);
        }
      }

      console.log(`\n📊 Resultado: ${results.published} publicados, ${results.failed} falhos.`);

      // Atualiza o progresso global do livro na index e dispara i18n
      if (bookIndexId) {
        const checkQuery = `
          SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN (pipeline_state->'published_en'->>'status') = 'done' THEN 1 END) as published
          FROM ${TBL_CONTENT}
          WHERE index_id = $1 OR index_id = $2
        `;
        const { rows: stats } = await db.query(checkQuery, [bookIndexId, bookAutoNumberText]);
        if (stats.length > 0) {
          const { total, published } = stats[0];
          const totalNum = Number(total);
          const pubNum = Number(published);
          const pct = totalNum > 0 ? Math.round((pubNum / totalNum) * 100) : 0;

          console.log(`📈 [mananciapp/publish] Progresso global do livro ${bookIndexId}: ${pubNum}/${totalNum} (${pct}%)`);

          const bookRes = await db.query(`SELECT pipeline_state FROM ${TBL_INDEX} WHERE __id = $1`, [bookIndexId]);
          const currentBookState = bookRes.rows[0]?.pipeline_state ?? {};

          const newBookState = {
            ...currentBookState,
            published_en: {
              status: pubNum === totalNum ? "done" : "pending",
              total: totalNum,
              done: pubNum,
              pct
            }
          };

          await db.query(`
            UPDATE ${TBL_INDEX}
            SET pipeline_state = $1::jsonb, __last_modified_time = NOW()
            WHERE __id = $2
          `, [JSON.stringify(newBookState), bookIndexId]);

          // Se a publicação em inglês acabou (100%), dispara i18n
          // COMENTADO: Mantendo as esteiras isoladas conforme feedback do usuário
        }
      }

      // Se um taskId foi fornecido, atualiza a tarefa na tabela universal de tasks
      if (taskId) {
        console.log(`📝 [mananciapp/publish] Atualizando status da task ${taskId} para 'Concluído'...`);
        await db.query(`
          UPDATE ${TBL_TASKS}
          SET "Status" = 'Concluído', "resultado" = $1, __last_modified_time = NOW()
          WHERE __id = $2
        `, [`Publicado: ${results.published} capítulos. Falhados: ${results.failed}.`, taskId]);
      }

      return results;

    } finally {
      await db.end();
    }
}

export const publishMananciappBooks = task({
  id: "mananciall/produto/books/publish",
  maxDuration: 600, // 10 minutos
  queue: {
    name: "mananciapp-publish-queue",
    concurrencyLimit: 1,
  },
  run: runPublishMananciappBooks,
});
