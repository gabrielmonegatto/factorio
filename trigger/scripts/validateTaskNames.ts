// scripts/validateTaskNames.ts
import * as fs from "fs";
import * as path from "path";

const TRIGGER_DIR = path.resolve(__dirname, '..');
const ID_REGEX = /id:\s*["'`]([^"'`]+)["'`]/g;
const CANONICAL_REGEX = /^[a-z0-9_-]+\/[a-z0-9_-]+\/[a-z0-9_-]+\/[a-z0-9_-]+$/;

function walkDir(dir: string): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat && stat.isDirectory()) {
      results = results.concat(walkDir(filePath));
    } else if (filePath.endsWith(".ts")) {
      results.push(filePath);
    }
  }
  return results;
}

function validate() {
  console.log("🔍 [VALIDATE] Iniciando verificação de nomes de tasks...");
  const files = walkDir(TRIGGER_DIR);
  let hasErrors = false;
  let taskCount = 0;

  for (const file of files) {
    // Pula o próprio script de validação
    if (file.endsWith("validateTaskNames.ts")) continue;

    const content = fs.readFileSync(file, "utf-8");
    let match;
    
    // Reset regex index
    ID_REGEX.lastIndex = 0;

    while ((match = ID_REGEX.exec(content)) !== null) {
      const taskId = match[1];
      taskCount++;
      const relativePath = path.relative(TRIGGER_DIR, file);

      if (!CANONICAL_REGEX.test(taskId)) {
        console.error(`❌ [VALIDATE] ID de tarefa inválido em "${relativePath}": "${taskId}"`);
        console.error(`             -> Deve possuir exatamente 4 níveis (brand/area/project/task) em minúsculas.`);
        hasErrors = true;
      } else {
        console.log(`✅ [VALIDATE] ID válido em "${relativePath}": "${taskId}"`);
      }
    }
  }

  console.log(`\n📊 [VALIDATE] Total de tarefas analisadas: ${taskCount}`);
  if (hasErrors) {
    console.error("❌ [VALIDATE] Falha na validação de nomes de tarefas.");
    process.exit(1);
  } else {
    console.log("✨ [VALIDATE] Sucesso! Todas as tarefas seguem o padrão canônico.");
    process.exit(0);
  }
}

if (typeof process !== "undefined" && process.argv[1] && (process.argv[1].endsWith("validateTaskNames.ts") || process.argv[1].endsWith("validateTaskNames.js"))) {
  validate();
}
