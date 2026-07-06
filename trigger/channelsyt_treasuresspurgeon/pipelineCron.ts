// pipelineCron.ts – delega ao universalCron
import { universalCron } from "../utils/universalCron";

/**
 * Export alias so existing imports keep working.
 */
export const cronSpurgeonPipeline = universalCron;
