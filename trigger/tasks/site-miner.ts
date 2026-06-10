import { task, schedules } from "@trigger.dev/sdk/v3";
import { exec } from "child_process";
import { promisify } from "util";
import * as path from "path";

const execAsync = promisify(exec);

const SCRIPTS_DIR = path.resolve(
  "C:/Users/Monegatto/Desktop/EternalL/_factorio/workflows/site_miner"
);

interface DiscoverPayload {
  targetUrl: string;
  siteName?: string;
  limit?: number;
  searchFilter?: string;
}

interface ScrapeBatchPayload {
  siteName?: string;
  crawlId?: string;
  batchSize?: number;
  delayMs?: number;
}

/**
 * DISCOVER: Firecrawl Map → knowledge_index
 */
export const discoverSite = task({
  id: "discover-site",
  run: async (payload: DiscoverPayload) => {
    const { targetUrl, siteName, limit = 500, searchFilter } = payload;

    const args = [
      `"${SCRIPTS_DIR}\\discover_site.py"`,
      `"${targetUrl}"`,
    ];

    if (siteName) args.push(`--site "${siteName}"`);
    if (limit) args.push(`--limit ${limit}`);
    if (searchFilter) args.push(`--search "${searchFilter}"`);

    const cmd = `python ${args.join(" ")}`;
    console.log(`🔍 Running: ${cmd}`);

    const { stdout, stderr } = await execAsync(cmd);
    console.log(stdout);
    if (stderr) console.error(stderr);

    return { status: "completed", targetUrl, siteName };
  },
});

/**
 * SCRAPE BATCH: knowledge_index (mapped) → Firecrawl → knowledge_content
 */
export const scrapeSiteBatch = task({
  id: "scrape-site-batch",
  run: async (payload: ScrapeBatchPayload) => {
    const { siteName, crawlId, batchSize = 10, delayMs = 500 } = payload;

    const args = [`"${SCRIPTS_DIR}\\scrape_site.py"`];
    if (siteName) args.push(`--site "${siteName}"`);
    if (crawlId) args.push(`--crawl "${crawlId}"`);
    if (batchSize) args.push(`--batch ${batchSize}`);
    if (delayMs) args.push(`--delay ${delayMs}`);

    const cmd = `python ${args.join(" ")}`;
    console.log(`🕷️ Running: ${cmd}`);

    const { stdout, stderr } = await execAsync(cmd);
    console.log(stdout);
    if (stderr) console.error(stderr);

    return { status: "completed", batchSize };
  },
});

/**
 * SCRAPE ALL: loops batches until all mapped pages are scraped
 */
export const scrapeAllSite = task({
  id: "scrape-all-site",
  run: async (payload: { siteName?: string; crawlId?: string; batchSize?: number }) => {
    const { siteName, crawlId, batchSize = 10 } = payload;
    let totalScraped = 0;
    let keepGoing = true;

    while (keepGoing) {
      // For now just one batch at a time via the Python scrape
      const result = await scrapeSiteBatch.triggerAndWait({
        siteName,
        crawlId,
        batchSize,
        delayMs: 500,
      });

      const scraped = result?.output?.scraped ?? result?.output?.output?.scraped ?? 0;
      totalScraped += scraped;

      console.log(`📊 Progresso: ${totalScraped} páginas raspadas`);

      if (scraped < batchSize) {
        keepGoing = false;
      }
    }

    return { status: "completed", totalScraped };
  },
});

/**
 * Scheduled: every 6 hours, scrape pending pages
 */
export const scheduledScrape = schedules.task({
  id: "scheduled-site-scrape",
  cron: "0 */6 * * *",
  run: async () => {
    console.log("🕐 Scraping schedule triggered — processing pending pages...");

    const result = await scrapeAllSite.triggerAndWait({
      batchSize: 10,
    });

    console.log(`✅ Scheduled scrape completed: ${result?.output?.totalScraped ?? 0} pages`);
    return result?.output;
  },
});