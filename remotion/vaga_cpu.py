#!/usr/bin/env python3
"""
vaga_cpu.py — semáforo de CPU da MÁQUINA INTEIRA, compartilhado por todas as esteiras.

## O problema que isto resolve

Cada etapa pesada ganhou um teto de CPU olhando só pra si mesma: a narração
pedia 8, o produtor de render pedia 8 (antes 12). Ninguém somava. Numa VPS de
16 vCPU com DOIS canais ligados, a conta virava:

    narrar spurgeon 8 + narrar moody 8 + render spurgeon 8 + render moody 8 = 32

O sistema não recusa: ele aceita e engasga. Medido em 25/08, com load 20:
um sermão que levava 1.400s passou a levar 9.700s. Seis vezes mais lento.
E como o orçamento de tempo da narração conta minutos de relógio, ele estourou
em 341 min de uma janela de 200.

Teto por processo não é teto de máquina. Isolamento entre canais também não
resolve: cada esteira estava certa sozinha, e erradas juntas.

## Como funciona

Um número fixo de VAGAS, cada uma valendo um punhado de CPUs, somando menos que
a máquina. Trabalho pesado só começa depois de pegar uma vaga, e devolve ao sair
(inclusive se morrer: o lock é do processo, o kernel solta sozinho).

    VAGAS x CPUS_POR_VAGA <= nproc - 1     (1 sobra pro sistema e pro proxy)

Isso PRESERVA o isolamento que o Gabriel pediu: canal travado segura UMA vaga,
não a máquina. E escala pro canal 3 sem reconfigurar nada, porque o que limita é
a máquina, não a contagem de canais.

## Uso

    from vaga_cpu import vaga, CPUS

    with vaga("narrar spurgeon 0042"):
        roda_o_container(cpus=CPUS)

Ajustável por ambiente (a VPS pode crescer): FACTORIO_VAGAS, FACTORIO_CPUS_VAGA.
"""
import contextlib
import os
import time

# fcntl só existe em Unix. Isto roda na VPS, mas o repo é editado no Windows do
# Gabriel: import solto quebraria até um `--help` na máquina dele.
try:
    import fcntl
except ImportError:
    fcntl = None


def _nproc():
    try:
        return len(os.sched_getaffinity(0))     # respeita cgroup/taskset
    except AttributeError:
        return os.cpu_count() or 4


NPROC = _nproc()
VAGAS = int(os.environ.get("FACTORIO_VAGAS", "3"))
CPUS = os.environ.get("FACTORIO_CPUS_VAGA") or str(max(1, (NPROC - 1) // VAGAS))
DIR = os.environ.get("FACTORIO_VAGAS_DIR", "/tmp")


def orcamento_ok():
    """True se as vagas cabem na máquina. Serve pra avisar, não pra bloquear."""
    return VAGAS * int(CPUS) <= NPROC - 1


@contextlib.contextmanager
def vaga(rotulo, espera_max_s=1800, quieto=False):
    """Segura uma vaga de CPU enquanto o bloco roda.

    Espera até `espera_max_s` por uma vaga livre. Estourou a espera, levanta
    TimeoutError: quem chama decide se pula o item ou encerra o run. Esperar
    pra sempre transformaria um render travado em fábrica parada.

    Sem fcntl (Windows), vira no-op: dá pra rodar e testar fora da VPS.
    """
    if fcntl is None:
        yield CPUS
        return

    t0 = time.monotonic()
    avisou = False
    while True:
        for i in range(VAGAS):
            f = open(os.path.join(DIR, f"factorio_vaga_{i}.lock"), "w")
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                f.close()
                continue
            # Deixa rastro de quem está com a vaga: máquina cheia sem saber de
            # quem é a culpa foi exatamente o que custou caro em 25/08.
            f.write(f"{os.getpid()} {rotulo}\n")
            f.flush()
            if not quieto:
                print(f"🎟️  vaga {i}/{VAGAS} ({CPUS} cpus) · {rotulo}", flush=True)
            try:
                yield CPUS
            finally:
                f.close()          # fechar solta o flock
            return
        se = time.monotonic() - t0
        if se > espera_max_s:
            raise TimeoutError(
                f"sem vaga de CPU depois de {se/60:.0f} min ({VAGAS} ocupadas)")
        if not avisou and not quieto:
            print(f"⏸️  as {VAGAS} vagas de CPU estão ocupadas · esperando "
                  f"(até {espera_max_s/60:.0f} min) · {rotulo}", flush=True)
            avisou = True
        time.sleep(20)


def quem_esta_dentro():
    """Lê os rótulos das vagas ocupadas. Só pra diagnóstico."""
    fora = []
    for i in range(VAGAS):
        p = os.path.join(DIR, f"factorio_vaga_{i}.lock")
        try:
            fora.append(f"{i}: {open(p).read().strip() or 'livre'}")
        except OSError:
            fora.append(f"{i}: livre")
    return fora


if __name__ == "__main__":
    print(f"nproc={NPROC} · vagas={VAGAS} x {CPUS} cpus = {VAGAS*int(CPUS)}"
          f" · cabe={'sim' if orcamento_ok() else 'NÃO'}")
    for l in quem_esta_dentro():
        print("  " + l)
