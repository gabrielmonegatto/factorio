#!/usr/bin/env python3
"""
docker_nomeado.py — roda container com NOME e garante que ele morre junto.

## O vazamento que isto tapa

`docker run` é CLIENTE. Matar o cliente não mata o container: o daemon segue
rodando aquilo. Então toda vez que a fábrica encerrava um passo por fora do
caminho feliz, ficava um container zumbi comendo CPU pra sempre.

Medido em 25/08, e não em teoria:

  - `pkill` num run de narração deixou um `factorio-tts` a 786% de CPU.
  - `systemctl restart factory-producer@moody` deixou um `factorio-render` a
    401%, e o produtor novo subiu OUTRO por cima.

Os dois com nome aleatório do Docker (`epic_dubinsky`, `confident_margulis`),
o que torna impossível saber, olhando, o que é trabalho e o que é lixo. Pior:
o semáforo de CPU (`vaga_cpu.py`) fica cego, porque zumbi não pede vaga. A
máquina fica cheia e o painel diz que está livre.

## O que isto faz

1. **Nome determinístico** (`factorio_<etapa>_<canal>_<id>`): dá pra olhar
   `docker ps` e saber de quem é cada container.
2. **Varre o homônimo antes de subir**: sobra de uma execução morta é removida
   em vez de conviver com a nova.
3. **Mata no `finally`**, inclusive em KeyboardInterrupt, SIGTERM e exceção.
   `--rm` sozinho NÃO basta: ele limpa depois que o container para, e o
   problema é justamente o container que não para.

## Uso

    from docker_nomeado import rodar
    rodar("tts", "spurgeon", "0042",
          ["--memory=8g", f"--cpus={CPUS}", "-v", f"{d}:/data"],
          "factorio-tts", ["--input", "/data/s.txt"])
"""
import re
import signal
import subprocess

PREFIXO = "factorio"


def nome_de(etapa, canal, ident):
    """Nome previsível e válido pro Docker ([a-zA-Z0-9][a-zA-Z0-9_.-]*)."""
    bruto = f"{PREFIXO}_{etapa}_{canal}_{ident}"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", bruto)[:100]


def _derrubar(nome, quieto=True):
    subprocess.run(["docker", "rm", "-f", nome],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL if quieto else None)


def rodar(etapa, canal, ident, opcoes, imagem, argumentos, check=True):
    """docker run que não deixa órfão. Devolve o CompletedProcess."""
    nome = nome_de(etapa, canal, ident)
    # Sobra de execução anterior: derrubar é mais seguro que conviver, porque o
    # homônimo velho estaria escrevendo no MESMO volume de trabalho.
    _derrubar(nome)

    cmd = ["docker", "run", "--rm", "--name", nome] + list(opcoes) + [imagem] + list(argumentos)

    # SIGTERM é como o systemd encerra o serviço no `restart`. Sem isto, o
    # produtor reinicia e o container antigo continua vivo — foi exatamente o
    # `confident_margulis` a 401%.
    anteriores = {}
    def _ao_receber(sig, _frame):
        _derrubar(nome)
        h = anteriores.get(sig)
        if callable(h):
            h(sig, _frame)
        raise KeyboardInterrupt(f"sinal {sig} recebido; {nome} derrubado")

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            anteriores[sig] = signal.signal(sig, _ao_receber)
        except (ValueError, OSError):
            pass       # sem handler fora da thread principal; o finally ainda vale

    try:
        return subprocess.run(cmd, check=check)
    finally:
        _derrubar(nome)
        for sig, h in anteriores.items():
            try:
                signal.signal(sig, h)
            except (ValueError, OSError):
                pass


def varrer(etapa, canal):
    """Derruba sobras DESTE canal e DESTA etapa antes de começar.

    O `rodar()` já mata o homônimo, mas só o homônimo: produtor que reinicia e
    segue pro sermão seguinte deixaria o container do anterior vivo pra sempre.
    Escopo estreito de propósito (etapa + canal): varrer tudo quebraria o
    isolamento entre canais, matando o render de um vizinho que está trabalhando.
    """
    alvo = f"{PREFIXO}_{etapa}_{canal}_"
    mortos = [n for n in zumbis() if n.startswith(alvo)]
    for n in mortos:
        _derrubar(n)
        print(f"🧹 container órfão removido: {n}", flush=True)
    return mortos


def zumbis():
    """Containers de JOB da fábrica vivos agora (diagnóstico e varredura).

    ⚠️ Exige as 4 partes do nome (`factorio_etapa_canal_id`). Um `startswith`
    solto em "factorio_" também casava `factorio_proxy`, que é o Caddy de
    PRODUÇÃO rodando há 4 semanas. Filtro frouxo perto de um serviço de produção
    é acidente esperando uma varredura distraída.
    """
    r = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                       capture_output=True, text=True)
    return [n for n in r.stdout.split()
            if n.startswith(PREFIXO + "_") and n.count("_") >= 3]


if __name__ == "__main__":
    vivos = zumbis()
    print("containers da fábrica vivos:", ", ".join(vivos) if vivos else "(nenhum)")
