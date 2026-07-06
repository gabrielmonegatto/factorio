# 📚 Biblioteca de Referência (Néctar)

Esta pasta contém o "néctar" extraído de bibliotecas e templates profissionais do Remotion. 
Os arquivos aqui são **REFERÊNCIAS** para lógica e não devem ser usados diretamente como componentes (pois dependem de utilitários externos).

## 🗃️ O que temos aqui:

1. **`Spectrum_Ref.tsx`** (Audiogram):
   - Lógica de visualização de áudio usando `@remotion/media-utils`.
   - Como transformar frequências de áudio em barras visuais.

2. **`SkiaNeon_Ref.tsx`** (Skia):
   - Como usar o motor `Skia` para efeitos de neon, borrão (blur) e gradientes complexos.
   - Ideal para o look "premium/etéreo" de canais de meditação.

3. **`AnimatedText_Ref.tsx`** (Remotion Bits):
   - Lógica de animação de texto dividida por caracteres (staggered animation).
   - Uso de `spring` e `interpolate` para movimentos orgânicos.

---

**Uso sugerido:**
Quando precisarmos de um novo efeito, basta eu ler esses arquivos e adaptar a lógica para os nossos componentes oficiais em `src/core/effects`.
