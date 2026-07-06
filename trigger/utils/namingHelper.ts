// utils/namingHelper.ts
/**
 * Helper to build canonical task identifiers.
 * Format: `${brand}/${area}/${project}/${task}`
 */
export function buildTaskId(params: {
  brand: string;
  area: string;
  project: string;
  task: string;
}): string {
  const { brand, area, project, task } = params;
  return `${brand}/${area}/${project}/${task}`;
}
