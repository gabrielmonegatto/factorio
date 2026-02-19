# Bible 365 Prompt Specification

## Objetivo
Gerar conteúdo diário para a jornada "Bíblia 365 Dias" do App Mananciall. O conteúdo deve ser teologicamente rico, inspirador e prático.

## Estrutura do Output (JSON)
O output deve ser um objeto JSON com a seguinte estrutura:

```json
{
  "day_number": 1,
  "title": "O Verbo Eterno",
  "bible_passage": "João 1:1-14",
  "intro_text": "Markdown string...",
  "explanation_text": "Markdown string...",
  "devotional_text": "Markdown string...",
  "prayer_text": "Markdown string...",
  "application_points": ["Ponto 1", "Ponto 2", "Ponto 3"]
}
```

## Diretrizes de Conteúdo

### 1. Introdução (`intro_text`)
- **Tom:** Acolhedor e convidativo.
- **Objetivo:** Preparar o coração do leitor para o tema do dia.
- **Tamanho:** Curto (2-3 parágrafos).

### 2. Explicação Teológica (`explanation_text`)
- **Tom:** Educativo e profundo, mas acessível.
- **Objetivo:** Explicar o contexto bíblico, significado das palavras originais (se relevante) e a doutrina central.
- **Formatação:** Use **negrito** para conceitos chave.

### 3. Devocional (`devotional_text`)
- **Tom:** Pessoal, inspirador e reflexivo.
- **Objetivo:** Conectar a teologia com a vida diária.
- **Foco:** Como essa verdade muda minha vida hoje?

### 4. Oração (`prayer_text`)
- Uma oração curta e potente baseada no tema.

### 5. Aplicação Prática (`application_points`)
- 3 ações concretas que o leitor pode tomar.

## Exemplo de Estilo
Evite "teologês" excessivo sem explicação. Use metáforas do dia a dia. Foco na graça e na transformação.
