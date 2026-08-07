import httpx
from os import getenv

RUNPOD_API_KEY = getenv("RUNPOD_API_KEY", "")

def _headers():
    return {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

def register_tools(mcp):

    @mcp.tool()
    async def runpod_list_pods() -> list:
        """
        Lista todos os pods de GPU (ativos ou parados) na conta do Runpod.
        """
        if not RUNPOD_API_KEY:
            return ["Runpod API key not configured in environment."]
            
        url = "https://api.runpod.io/v1/pods"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=_headers(), timeout=15)
            if r.status_code != 200:
                return [f"Failed to list Runpod pods: {r.status_code} - {r.text}"]
            return r.json()

    @mcp.tool()
    async def runpod_pod_control(pod_id: str, action: str) -> str:
        """
        Controla o ciclo de vida de um pod no Runpod.
        Ações válidas: 'start', 'stop', 'terminate'.
        """
        if not RUNPOD_API_KEY:
            return "Runpod API key not configured."
            
        action = action.lower().strip()
        if action not in ("start", "stop", "terminate"):
            return f"Invalid action: {action}. Must be 'start', 'stop', or 'terminate'."
            
        url = f"https://api.runpod.io/v1/pods/{pod_id}/{action}"
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=_headers(), timeout=15)
            if r.status_code not in (200, 201):
                return f"Failed to execute action '{action}' on pod {pod_id}: {r.status_code} - {r.text}"
            return f"Action '{action}' successfully sent to pod {pod_id}."

    @mcp.tool()
    async def runpod_run_serverless_job(endpoint_id: str, input_data: dict) -> dict:
        """
        Dispara um job assíncrono em um Endpoint Serverless do Runpod (ex: Whisper, TTS).
        Retorna o ID do Job para consulta posterior.
        """
        if not RUNPOD_API_KEY:
            return {"error": "Runpod API key not configured."}
            
        url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        payload = {"input": input_data}
        
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=_headers(), json=payload, timeout=20)
            if r.status_code not in (200, 201):
                return {"error": f"Failed to run serverless job: {r.status_code} - {r.text}"}
            return r.json()

    @mcp.tool()
    async def runpod_get_serverless_job_status(endpoint_id: str, job_id: str) -> dict:
        """
        Consulta o status ou resultado de um job Serverless do Runpod usando o ID do job.
        Retorna o status (COMPLETED, IN_QUEUE, RUNNING, FAILED) e o resultado final se completo.
        """
        if not RUNPOD_API_KEY:
            return {"error": "Runpod API key not configured."}
            
        url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=_headers(), timeout=15)
            if r.status_code != 200:
                return {"error": f"Failed to fetch job status: {r.status_code} - {r.text}"}
            return r.json()

    return mcp
