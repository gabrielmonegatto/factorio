// utils/teable.ts — cliente REST do Teable em TS PURO.
//
// Por que existe: a versão antiga da fábrica falava com o banco por SQL bruto em
// `localhost` e spawnava Python. Isso funcionava em `trigger dev` (máquina do Gabriel),
// mas MORRE no deploy pra nuvem (`spawn python ENOENT`) — foi o que matou a esteira
// por 24 dias em silêncio. Aqui: só HTTPS + REST, roda em qualquer lugar.
//
// Regra da constituição: dentro dos schemas `bse*` do Teable é SÓ API.
// (DDL por SQL corrompe a camada de metadata; foi o que criou os fantasmas
//  `mcp` e `content_chunks` e as colunas invisíveis.)

const TASKS_TABLE = "tblVzN1Eo8tfk7GX2CJ";

export type Status = "Pendente" | "Em Processamento" | "Concluído" | "Erro";

export interface Task {
  id: string;
  titulo: string;
  esteira: string;      // campo `area` — channels | produto | video | artigo | copy...
  etapa: string;        // campo `task`  — narrate-audio | render-video | ...
  status: Status;
  brand: string;
  projeto: string;      // Project_Slug
  lang: string;         // en | es | pt
  instruction: string;
  logs: string;
  progresso: string;
  /** ID legado criado por SQL (não casa com o padrão do Teable) → a API não escreve nele. */
  somenteLeitura: boolean;
  modificadoEm?: string;
}

/** IDs válidos do Teable são `rec` + ~16 chars. Os legados (`task_xxx_recYYY`) a API recusa. */
const ID_VALIDO = /^rec[A-Za-z0-9]{10,}$/;

function env(nome: string): string {
  const v = process.env[nome];
  if (!v) throw new Error(`Falta a variável de ambiente ${nome} (configure no Trigger.dev)`);
  return v.replace(/\r/g, "").trim();
}

async function req(method: string, path: string, body?: unknown): Promise<any> {
  const url = env("TEABLE_URL").replace(/\/$/, "") + path;
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${env("TEABLE_TOKEN")}`,
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const texto = await res.text();
  if (!res.ok) {
    throw new Error(`Teable ${method} ${path} -> ${res.status}: ${texto.slice(0, 300)}`);
  }
  return texto ? JSON.parse(texto) : {};
}

function paraTask(rec: any): Task {
  const f = rec.fields ?? {};
  return {
    id: rec.id,
    titulo: f["Task ID"] ?? "",
    esteira: f["area"] ?? "",
    etapa: f["task"] ?? "",
    status: (f["Status"] ?? "Pendente") as Status,
    brand: f["Brand"] ?? "mananciall",
    projeto: f["Project_Slug"] ?? "",
    lang: f["lang"] ?? "",
    instruction: f["Instruction"] ?? "",
    logs: f["Logs"] ?? "",
    progresso: f["Progresso"] ?? "",
    somenteLeitura: !ID_VALIDO.test(rec.id ?? ""),
    modificadoEm: rec.lastModifiedTime,
  };
}

/** Lê TODAS as tasks (pagina sozinho). A leitura funciona inclusive nos registros legados. */
export async function listarTasks(): Promise<Task[]> {
  const out: Task[] = [];
  let skip = 0;
  for (;;) {
    const r = await req("GET", `/api/table/${TASKS_TABLE}/record?take=1000&skip=${skip}&fieldKeyType=name`);
    const page: any[] = r.records ?? [];
    out.push(...page.map(paraTask));
    if (page.length < 1000) break;
    skip += 1000;
  }
  return out;
}

/** Identificador canônico da fábrica: brand/area/project/task (validado por validateTaskNames.ts). */
export function idCanonico(t: Task): string {
  return `${t.brand}/${t.esteira}/${t.projeto}/${t.etapa}`;
}

/** Atualiza campos. Lança se o registro for legado (a API recusa o ID inventado). */
export async function atualizarTask(id: string, campos: Record<string, unknown>): Promise<void> {
  if (!ID_VALIDO.test(id)) {
    throw new Error(`Registro legado ${id}: a API do Teable não escreve nele (ID fora do padrão). Quem grava é o operário da VPS.`);
  }
  await req("PATCH", `/api/table/${TASKS_TABLE}/record/${id}`, {
    fieldKeyType: "name",
    record: { fields: campos },
  });
}

/** Cria uma ordem de trabalho nova. Nasce com ID válido → escrevível de qualquer lugar. */
export async function criarTask(campos: Record<string, unknown>): Promise<string> {
  const r = await req("POST", `/api/table/${TASKS_TABLE}/record`, {
    fieldKeyType: "name",
    records: [{ fields: campos }],
  });
  return r.records?.[0]?.id ?? "";
}

/** Anexa uma linha ao log da task (mantém histórico, igual fazia o auto_cure antigo). */
export async function logar(t: Task, msg: string): Promise<void> {
  const carimbo = new Date().toISOString();
  const novo = `${t.logs ?? ""}\n[${carimbo}] ${msg}`.trim().slice(-8000);
  await atualizarTask(t.id, { Logs: novo });
}
