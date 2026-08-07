import httpx
import boto3
from botocore.client import Config
from os import getenv

# Load Cloudflare R2 Credentials
R2_ACCESS_KEY_ID = getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = getenv("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT = getenv("R2_ENDPOINT", "")
R2_PUBLIC_URL = getenv("R2_PUBLIC_URL", "")

# Load Cloudflare Global API Credentials
CLOUDFLARE_ACCOUNT_ID = getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = getenv("CLOUDFLARE_API_TOKEN", "")

def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4")
    )

def register_tools(mcp):

    @mcp.tool()
    async def cloudflare_r2_list(bucket: str = "channels", limit: int = 100) -> list:
        """
        Lista objetos/arquivos dentro de um bucket do Cloudflare R2.
        """
        if not R2_ACCESS_KEY_ID:
            return ["Cloudflare R2 credentials not configured in environment."]
        try:
            s3 = _get_r2_client()
            res = s3.list_objects_v2(Bucket=bucket, MaxKeys=limit)
            contents = res.get("Contents", [])
            return [
                {
                    "key": item["Key"],
                    "size_mb": round(item["Size"] / (1024 * 1024), 2),
                    "last_modified": item["LastModified"].isoformat()
                }
                for item in contents
            ]
        except Exception as e:
            return [f"Error listing R2 bucket: {str(e)}"]

    @mcp.tool()
    async def cloudflare_r2_presigned_url(bucket: str, key: str, method: str = "get_object", expires_in: int = 3600) -> str:
        """
        Gera uma URL pré-assinada (presigned URL) para download (method='get_object')
        ou upload (method='put_object') de arquivos no Cloudflare R2.
        """
        if not R2_ACCESS_KEY_ID:
            return "Cloudflare R2 credentials not configured."
        try:
            s3 = _get_r2_client()
            url = s3.generate_presigned_url(
                ClientMethod=method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            return f"Error generating presigned URL: {str(e)}"

    @mcp.tool()
    async def cloudflare_ai_run(model: str, prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.6) -> str:
        """
        Executa um modelo de Inteligência Artificial usando o Cloudflare Workers AI.
        Modelos comuns:
         - Llama 3 (Text): '@cf/meta/llama-3-8b-instruct'
         - Stable Diffusion (Image): '@cf/stabilityai/stable-diffusion-xl-base-1.0'
         - Whisper (Audio): '@cf/openai/whisper-large-v3'
        """
        if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
            return "Cloudflare global credentials not configured."
            
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        
        # Adjust payload if model is an image generator (no messages format)
        if "diffusion" in model or "image" in model:
            payload = {"prompt": prompt}
            
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code != 200:
                return f"Error calling Cloudflare AI: {r.status_code} - {r.text}"
            
            # If model generates image bytes, we return response content-type or size
            if "image" in r.headers.get("content-type", ""):
                return f"Image successfully generated! Response size: {len(r.content)} bytes. (Content-Type: {r.headers.get('content-type')})"
                
            data = r.json()
            return data.get("result", {}).get("response", "No response text returned.")

    @mcp.tool()
    async def cloudflare_dns_create(zone_id: str, subdomain_name: str, ip_address: str, record_type: str = "A", proxied: bool = False) -> dict:
        """
        Cria um novo registro de DNS em uma zona do Cloudflare.
        """
        if not CLOUDFLARE_API_TOKEN:
            return {"error": "Cloudflare global credentials not configured."}
            
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "type": record_type,
            "name": subdomain_name,
            "content": ip_address,
            "ttl": 1, # Automatic
            "proxied": proxied
        }
        
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code not in (200, 201):
                return {"error": f"Failed to create DNS record: {r.status_code} - {r.text}"}
            return r.json().get("result", {})

    return mcp
