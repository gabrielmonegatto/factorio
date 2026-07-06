# 🛡️ Boas Práticas e Travas de Crédito — API Foreplay

Este documento serve como guia de referência técnica para evitar o desperdício de créditos e estouros de cota ao utilizar a API pública do Foreplay no ecossistema **EternalL**.

---

## 🔑 1. Como a API do Foreplay Cobra Créditos
*   **Regra Geral:** A API do Foreplay cobra **1 crédito para cada anúncio retornado** no endpoint de listagem de anúncios da marca (`GET /api/brand/getAdsByBrandId`).
*   **O Risco:** Marcas grandes (ex: *Mars Men*, *Hims*) podem ter milhares de anúncios ativos cadastrados. Chamar a API paginando através de todos os `cursor` sem uma trava rígida consumirá milhares de créditos de uma única vez.

---

## 🧱 2. As 4 Travas Obrigatórias de Desenvolvimento

Qualquer agente, automação ou script que faça chamadas para buscar anúncios da API do Foreplay **deve** implementar as seguintes travas e padrões:

### 1. Limite Rígido (Capped Pull)
O loop de paginação deve ser interrompido imediatamente assim que atingir o limite estipulado pelo usuário. O padrão recomendado é:
*   Máximo **100 imagens**
*   Máximo **100 vídeos**
*   *Gasto máximo por marca concorrente: 200 créditos.*

### 2. Parâmetro `limit` Dinâmico no Loop
Para evitar que a última página da paginação extrapole a trava (ex: puxar 50 anúncios quando só faltavam 10 para bater a meta de 100), calcule o `limit` de cada requisição dinamicamente:
```python
limit_needed = min(50, max_limit - len(ads_fetched))
```

### 3. Ordenação por Performance (`longest_running`)
Ao limitar a busca a 100 criativos, precisamos garantir que estamos trazendo os anúncios com melhor desempenho. Passe sempre o parâmetro de ordenação por duração ativa na requisição:
```python
"order": "longest_running"
```
Isso garante que os criativos que estão no ar há mais tempo (prováveis campeões) venham no topo da lista.

### 4. Cache Local Obrigatório (`foreplay_media_cache.json`)
Antes de fazer qualquer requisição de download de mídia, análise ou transcrição, consulte o cache local em `scratch/foreplay_media_cache.json`.
*   A listagem inicial salva todos os metadados dos anúncios no cache.
*   Consultas subsequentes para detalhes de mídias devem ler o cache local, custando **0 créditos** adicionais da API.

---

## 💻 3. Exemplo de Implementação Padrão (Python)

Utilize este modelo de código ao construir novas tasks de extração:

```python
def fetch_ads_by_format(brand_id, display_format, max_limit=100):
    ads_fetched = []
    cursor = None
    
    while len(ads_fetched) < max_limit:
        # 1. Calcula o limite dinâmico necessário para não estourar a trava
        limit_needed = min(50, max_limit - len(ads_fetched))
        
        params = {
            "brand_ids": brand_id,
            "live": "true",
            "display_format": display_format,
            "order": "longest_running",  # Puxa os campeões primeiro
            "limit": limit_needed
        }
        if cursor:
            params["cursor"] = cursor
            
        r = requests.get(f"{foreplay_base_url}/brand/getAdsByBrandId", headers=headers, params=params)
        if r.status_code != 200:
            break
            
        res = r.json()
        data = res.get("data", [])
        ads_fetched.extend(data)
        
        # Paginação via cursor
        cursor = res.get("metadata", {}).get("cursor")
        if not cursor or len(data) == 0:
            break
            
    return ads_fetched
```
