import subprocess
import sys

# Script para rodar o check_backlog.py e capturar a saída
script_path = r"C:\Users\Monegatto\Desktop\EternalL\_brain\projectz\mananciall\squad\agente_minerador\workers\check_backlog.py"

try:
    print(f"Executando: {script_path}")
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    print("SAÍDA:")
    print(result.stdout)
    
    if result.stderr:
        print("ERROS:")
        print(result.stderr)
        
except Exception as e:
    print(f"Erro na execução: {e}")

