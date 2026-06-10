@echo off
REM ============================================
REM  EternalL - Antigravity CLI Setup
REM  Configura GEMINI_API_KEY do AI Studio
REM  Pra usar no CMD/PowerShell:
REM    call setup_cli.bat
REM    agy "seu prompt aqui"
REM ============================================

REM As chaves estão no .env do projeto. Não versionar secrets.
REM setx GEMINI_API_KEY "SUA_CHAVE_AQUI" /M
REM setx OPENROUTER_API_KEY "SUA_CHAVE_AQUI" /M

echo.
echo ============================================
echo  Antigravity CLI configurado!
echo  Chaves setadas como variaveis de sistema.
echo  Abra um NOVO terminal e execute:
echo    agy "iniciar ciclo de mineracao"
echo ============================================
echo.
pause