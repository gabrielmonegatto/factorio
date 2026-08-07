import time
import shutil
import socket
import json
from os import getenv

START_TIME = time.time()

def _query_docker_socket(path: str) -> str:
    """
    Faz uma requisição HTTP crua ao Unix Socket do Docker (/var/run/docker.sock).
    Retorna o payload de resposta decodificado.
    """
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect("/var/run/docker.sock")
        
        request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode("utf-8"))
        
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()
        
        # Split headers and body
        parts = response.split(b"\r\n\r\n", 1)
        if len(parts) < 2:
            return ""
            
        body = parts[1]
        
        # Check if transfer encoding is chunked
        headers = parts[0].decode("utf-8", errors="ignore")
        if "Transfer-Encoding: chunked" in headers:
            # Simple chunked decoding
            decoded_body = b""
            position = 0
            while position < len(body):
                line_end = body.find(b"\r\n", position)
                if line_end == -1:
                    break
                chunk_size_str = body[position:line_end].strip()
                if not chunk_size_str:
                    break
                try:
                    chunk_size = int(chunk_size_str, 16)
                except ValueError:
                    break
                if chunk_size == 0:
                    break
                position = line_end + 2
                decoded_body += body[position:position+chunk_size]
                position += chunk_size + 2
            return decoded_body.decode("utf-8", errors="replace")
            
        return body.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Docker Socket Error: {str(e)}"

def register_tools(mcp):

    @mcp.tool()
    async def system_health() -> dict:
        """
        Retorna o status geral de funcionamento do MCP Hub Universal.
        """
        uptime = time.time() - START_TIME
        return {
            "status": "online",
            "servico": "MCP Universal",
            "versao": "1.0.0",
            "uptime_segundos": round(uptime),
            "teable_conectado": bool(getenv("TEABLE_TOKEN")),
            "agentmemory_conectado": bool(getenv("AGENTMEMORY_SECRET"))
        }

    @mcp.tool()
    async def system_disk_space() -> dict:
        """
        Checa o uso de espaço em disco físico na VPS.
        """
        total, used, free = shutil.disk_usage("/")
        return {
            "total_gb": round(total / (2**30), 2),
            "used_gb": round(used / (2**30), 2),
            "free_gb": round(free / (2**30), 2),
            "percent_used": round((used / total) * 100, 2)
        }

    @mcp.tool()
    async def system_docker_ps() -> list:
        """
        Lista todos os containers ativos no Docker da VPS.
        Requer que o volume /var/run/docker.sock esteja montado no container.
        """
        res = _query_docker_socket("/containers/json")
        if "Docker Socket Error" in res:
            return [{"error": "Docker socket not accessible or not mounted in container."}]
        try:
            containers = json.loads(res)
            return [
                {
                    "names": c.get("Names", []),
                    "state": c.get("State", ""),
                    "status": c.get("Status", ""),
                    "id": c.get("Id", "")[:12]
                }
                for c in containers
            ]
        except Exception as e:
            return [{"error": f"Failed to parse Docker response: {str(e)}"}]

    @mcp.tool()
    async def system_docker_logs(container_name: str, tail: int = 50) -> str:
        """
        Lê as últimas linhas de log de um container Docker específico na VPS.
        """
        # Clean container name (docker returns logs with raw headers, we strip them)
        path = f"/containers/{container_name}/logs?stdout=1&stderr=1&tail={tail}"
        res = _query_docker_socket(path)
        
        if "Docker Socket Error" in res:
            return "Docker socket not accessible."
            
        # Strip Docker multiplexed stream headers if present
        # Docker logs header format: [stream_type (1 byte), 3 bytes empty, size (4 bytes)]
        lines = []
        i = 0
        while i < len(res):
            # If it looks like a docker multiplex header (first byte 1 or 2, followed by nulls)
            if i + 8 <= len(res) and (res[i] == 1 or res[i] == 2) and res[i+1] == 0 and res[i+2] == 0:
                try:
                    size = int.from_bytes(res[i+4:i+8].encode('utf-8', errors='ignore') if isinstance(res[i+4:i+8], str) else res[i+4:i+8], byteorder='big')
                    line = res[i+8:i+8+size]
                    lines.append(line)
                    i += 8 + size
                except:
                    lines.append(res[i:])
                    break
            else:
                lines.append(res[i:])
                break
                
        return "".join(lines).strip()

    return mcp
