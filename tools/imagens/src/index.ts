// factorio-imagens — gera assets de canal com Workers AI e grava no R2.
//
// Por que um Worker em vez de chamar a API REST: o token do .env tem D1 e
// Workers, mas NÃO tem Workers AI. O binding funciona em runtime sem token.
//
// Uso:
//   POST /gerar  { chave, prompt, modelo? }  -> gera e grava no R2
//   GET  /ping                                -> saúde
export default {
  async fetch(req: Request, env: any): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === '/ping') return new Response('ok');
    if (url.pathname !== '/gerar' || req.method !== 'POST') {
      return new Response('not found', { status: 404 });
    }
    const segredo = req.headers.get('x-segredo');
    if (!env.SEGREDO || segredo !== env.SEGREDO) {
      return new Response('unauthorized', { status: 401 });
    }
    const { chave, prompt, modelo, imagem_b64, forca } = (await req.json()) as any;
    if (!chave || !prompt) return new Response('faltou chave ou prompt', { status: 400 });

    const m = modelo || '@cf/black-forest-labs/flux-1-schnell';
    try {
      // Com `imagem_b64` vira EDIÇÃO (image-to-image): o modelo parte de uma
      // foto real em vez de inventar. É o que resolve semelhança de personagem
      // histórico — o texto sozinho não sabe a cara de ninguém.
      let r: any;
      if (imagem_b64 && m.includes('flux-2')) {
        // MINA: o flux-2-klein NÃO aceita JSON com a imagem em base64.
        // Ele exige multipart/form-data (o erro é "required properties at '/'
        // are 'multipart'"). É a única família aqui que foge do padrão.
        const bin = atob(imagem_b64);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        const fd = new FormData();
        fd.append('prompt', prompt);
        fd.append('image', new Blob([arr], { type: 'image/png' }), 'entrada.png');
        r = await env.AI.run(m, fd as any);
      } else {
        const entrada: any = { prompt };
        if (imagem_b64) {
          const bin = atob(imagem_b64);
          const arr = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
          entrada.image = [...arr];
          if (forca != null) entrada.strength = forca;
        } else if (m.includes('flux-1')) {
          entrada.steps = 4;
        }
        r = await env.AI.run(m, entrada);
      }
      // flux devolve { image: base64 }; sdxl devolve stream binário
      let bytes: Uint8Array;
      if (r?.image) {
        const bin = atob(r.image);
        bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      } else {
        bytes = new Uint8Array(await new Response(r).arrayBuffer());
      }
      await env.ASSETS.put(chave, bytes, {
        httpMetadata: { contentType: 'image/png' },
      });
      return Response.json({ ok: true, chave, bytes: bytes.length, modelo: m });
    } catch (e: any) {
      return Response.json({ ok: false, erro: String(e?.message ?? e) }, { status: 500 });
    }
  },
};
