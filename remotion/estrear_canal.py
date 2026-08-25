#!/usr/bin/env python3
"""
estrear_canal.py — muda a DATA DE ESTREIA de um canal e arrasta o calendário junto.

## Por que existe

O `schedule_channel.py` grava `channel_start` na primeira vez que roda e nunca
mais mexe nisso (de propósito: recalcular a base sozinho já produziu dois vídeos
no mesmo dia e dias vazios, a mina de 10/08). Só que a primeira vez que ele
rodou pro Moody foi por cron, e ele escolheu "amanhã" — o canal ficou pronto
hoje e estreando depois.

Antecipar na mão seria editar JSON no R2 e mexer em vídeo por vídeo no Studio.
Isto aqui faz a operação inteira, e serve pra qualquer canal futuro: é a mesma
coisa que vai acontecer toda vez que um canal ficar pronto antes da data que o
cron chutou.

## O que faz

  1. Recalcula todo o calendário a partir da data nova (respeitando warmup e
     `videos_por_dia` do canal, pela MESMA função que o agendador usa).
  2. Reaponta o `publishAt` de cada vídeo já agendado.
  3. Slot que já passou vira publicação AGORA (é o caso do vídeo de estreia
     quando se antecipa pro próprio dia).
  4. Persiste o `channel_start` novo, senão o próximo run do cron desfaz tudo.

## Uso

    python estrear_canal.py --canal moody --data hoje
    python estrear_canal.py --canal moody --data 2026-08-25 --aplicar

⚠️ GATE HUMANO: tornar vídeo público é irreversível (o mundo vê, e desfazer não
   apaga quem já viu). Sem `--aplicar` isto é só prévia.
"""
import argparse
import datetime as dt
import json
import urllib.request

import canais
import schedule_channel as S


def publicar_agora(env, video_id, token):
    """Tira o vídeo do privado AGORA. Remove o publishAt: a API recusa os dois juntos."""
    body = json.dumps({"id": video_id,
                       "status": {"privacyStatus": "public",
                                  "selfDeclaredMadeForKids": False}}).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/videos?part=status",
        data=body, method="PUT",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=40).read()


def main():
    ap = argparse.ArgumentParser()
    canais.add_arg_canal(ap)
    ap.add_argument("--data", required=True,
                    help="'hoje' ou AAAA-MM-DD: o dia do PRIMEIRO vídeo")
    ap.add_argument("--aplicar", action="store_true",
                    help="sem isto, só mostra o calendário novo")
    args = ap.parse_args()

    C = S.aplicar_canal(args.canal)
    env = S.load_env()
    agora = dt.datetime.now(dt.timezone.utc)
    nova = (agora.date() if args.data == "hoje"
            else dt.date.fromisoformat(args.data))

    s3 = S.s3c(env)
    estado = json.loads(s3.get_object(Bucket=S.BUCKET, Key=S.STATE_KEY)["Body"].read())
    antiga = estado.get("channel_start")
    agendados = estado.get("scheduled", {})
    if not agendados:
        raise SystemExit("nada agendado ainda: rode o schedule_channel.py primeiro.")

    print(f"🏷️  {C['slug']} ({C['nome']})")
    print(f"📅 estreia {antiga} → {nova}  ·  cadência {C['videos_por_dia']}/dia "
          f"· warmup {S.WARMUP_DAYS}d · {len(agendados)} vídeos já agendados\n")

    # A ordem do calendário é a ordem dos sermões prontos, a MESMA que o
    # agendador usa. Recalcular por conta própria aqui abriria a porta pro
    # calendário deste script discordar do calendário do cron.
    prontos = S.list_ready_sermons(s3)
    plano = []
    for i, nnnn in enumerate(prontos):
        if nnnn not in agendados:
            continue
        quando = S.slot_datetime(i, nova)
        plano.append((nnnn, agendados[nnnn]["videoId"],
                      agendados[nnnn].get("publishAt"), quando))

    for nnnn, vid, antes, quando in plano:
        passou = quando <= agora
        alvo = "AGORA (público)" if passou else quando.strftime("%Y-%m-%d %H:%MZ")
        print(f"  {nnnn}  {(antes or '?')[:16]}  →  {alvo}   https://youtu.be/{vid}")

    if not args.aplicar:
        print("\n(prévia — rode de novo com --aplicar)")
        return

    token = S.yt_token(env)          # confere o canal antes de mexer em qualquer vídeo
    mexidos = 0
    for nnnn, vid, _antes, quando in plano:
        try:
            if quando <= agora:
                publicar_agora(env, vid, token)
                estado["scheduled"][nnnn]["publishAt"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
                estado["scheduled"][nnnn]["publicado"] = True
                print(f"  🔴 {nnnn} NO AR: https://youtu.be/{vid}")
            else:
                pa = quando.strftime("%Y-%m-%dT%H:%M:%SZ")
                S.schedule_existing(env, vid, pa, token)
                estado["scheduled"][nnnn]["publishAt"] = pa
                print(f"  🗓️  {nnnn} → {pa}")
            mexidos += 1
        except Exception as e:
            print(f"  ❌ {nnnn}: {str(e)[:200]}")

    # Persistir por último e SEMPRE: se o channel_start velho ficar no R2, o
    # próximo run do cron recalcula da base antiga e desmancha isto tudo.
    estado["channel_start"] = nova.isoformat()
    s3.put_object(Bucket=S.BUCKET, Key=S.STATE_KEY,
                  Body=json.dumps(estado, indent=2).encode(),
                  ContentType="application/json")
    print(f"\n🏁 {mexidos}/{len(plano)} reapontados · channel_start={nova} salvo no R2")


if __name__ == "__main__":
    main()
