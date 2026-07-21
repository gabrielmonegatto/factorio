# Acervo de criativos no Teable

Espelha o acervo (D1 `br4nds.creatives` + performance do Meta) na tabela
**`br4nds_criativos`** da base Br4nds, para navegar como banco relacional —
galeria, filtro, ordenação — do mesmo jeito que `players_criativos` já faz
com os anúncios de concorrente. O schema é espelhado de propósito: os dois
lados ficam comparáveis na mesma régua.

```bash
python setup_criativos.py            # 1x — cria o schema (idempotente)
python sync_criativos.py --dry-run   # confere
python sync_criativos.py             # dados
python sync_criativos.py --media     # miniaturas (só as que faltam)
```

## A regra que não pode ser quebrada

O sync é **mão única (D1 → Teable) e só nas colunas de máquina**:

| Máquina escreve (sobrescreve) | Humano escreve (nunca tocado) |
|---|---|
| ID · Marca · Produto · Formato · Proporção · Etapa do Funil · Nº do Ad · Mídia · Arquivo (R2) · Produzido em | Gancho · Avatar · Gatilho Emocional · Gatilhos Mentais · CTA · Headline · Copy Principal · Oferta · Notas |
| Investido · Compras · Receita · ROAS · CTR % · Nº de Anúncios · Última veiculação · Sincronizado em | |

A curadoria é o trabalho que não dá para automatizar. Se um dia alguém
adicionar uma coluna de máquina, ela entra em `machine_fields()` — qualquer
coisa fora dessa função é território do humano.

## Miniaturas, não originais

Os 2505 PNGs somam 6,7 GB. Subir isso para o storage da VPS seria
desperdício: a galeria só precisa de preview. Então o script gera webp de
500px (~15 KB cada, ~38 MB no total) e sobe só isso como attachment; o
full-res continua no R2, linkado na coluna `Arquivo (R2)`.

Quando os vídeos entrarem, o mesmo desenho serve: thumb do frame de capa
como attachment + link do vídeo no R2.

## Gotchas

- **Content-type explícito no upload.** Sem ele o Teable grava como
  `text/plain` e a galeria não renderiza. Pior: o registro do Windows não
  conhece `.webp`, então `mimetypes.guess_type` devolve `None` — daí o
  `add_type` no topo de `_teable.py`.
- **API, nunca SQL bruto** no Postgres do container (regra do `docs/STACK.md`).
- Tabela nova no Teable nasce com 3 linhas em branco do template; elas não
  têm `ID` e são ignoradas pelo sync.
- Os dados de performance vêm da atribuição em `../meta/` — leia o README de
  lá, principalmente o aviso sobre o pixel que virou evento custom em 30/04.
