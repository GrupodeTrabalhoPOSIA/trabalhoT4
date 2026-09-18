@echo off
setlocal EnableExtensions

set "AURORA_ROOT=%~dp0"
set "AURORA_BACKEND_DIR=%AURORA_ROOT%BACKEND"
set "AURORA_FRONTEND_DIR=%AURORA_ROOT%FRONTEND"
set "AURORA_PYTHON=%AURORA_BACKEND_DIR%\.venv\Scripts\python.exe"
set "AURORA_BACKEND_ENV=%AURORA_BACKEND_DIR%\.env"
set "AURORA_FRONTEND_ENV=%AURORA_FRONTEND_DIR%\.env"

echo.
echo ========================================
echo       Aurora Tech Chatbot - Local
echo ========================================
echo.

if not exist "%AURORA_PYTHON%" (
    echo [ERRO] O ambiente virtual do backend nao foi encontrado.
    echo Execute os comandos de instalacao do BACKEND descritos no README.md.
    exit /b 1
)

where npm.cmd >nul 2>&1
if errorlevel 1 (
    echo [ERRO] O npm nao foi encontrado no PATH.
    echo Instale o Node.js e abra este arquivo novamente.
    exit /b 1
)

if not exist "%AURORA_FRONTEND_DIR%\node_modules" (
    echo [ERRO] As dependencias do frontend nao foram instaladas.
    echo Execute: cd FRONTEND ^&^& npm ci
    exit /b 1
)

if /I "%~1"=="--check" (
    echo [OK] Python, ambiente virtual, Node.js e dependencias encontrados.
    exit /b 0
)

if not exist "%AURORA_BACKEND_ENV%" (
    copy /Y "%AURORA_BACKEND_DIR%\.env.example" "%AURORA_BACKEND_ENV%" >nul
    echo [INFO] BACKEND\.env criado a partir de .env.example.
)

if not exist "%AURORA_FRONTEND_ENV%" (
    copy /Y "%AURORA_FRONTEND_DIR%\.env.example" "%AURORA_FRONTEND_ENV%" >nul
    echo [INFO] FRONTEND\.env criado a partir de .env.example.
)

findstr /R /C:"^OPENROUTER_API_KEY=." "%AURORA_BACKEND_ENV%" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] OPENROUTER_API_KEY ainda nao foi preenchida em BACKEND\.env.
    echo         Documentos funcionarao, mas o modelo nao podera responder.
    echo.
)

set "AURORA_SUPABASE_MISSING="
findstr /R /C:"^SUPABASE_DB_URL=." "%AURORA_BACKEND_ENV%" >nul 2>&1
if errorlevel 1 set "AURORA_SUPABASE_MISSING=1"

if defined AURORA_SUPABASE_MISSING (
    echo [AVISO] SUPABASE_DB_URL ainda nao foi preenchida.
    echo         Copie a URI do Session Pooler, na porta 5432, no painel Supabase.
    echo         Configure BACKEND\.env antes de usar documentos e chat.
    echo.
)

echo [INFO] Iniciando backend em http://127.0.0.1:8000 ...
start "Aurora Tech - Backend" /D "%AURORA_BACKEND_DIR%" cmd /k ""%AURORA_PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [INFO] Iniciando frontend em http://localhost:5173 ...
start "Aurora Tech - Frontend" /D "%AURORA_FRONTEND_DIR%" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"

echo [INFO] Aguardando os servidores iniciarem ...
timeout /t 4 /nobreak >nul

echo [OK] Abrindo o Aurora Tech Chatbot no navegador.
start "" "http://localhost:5173"

echo.
echo Para encerrar o sistema, feche os terminais Backend e Frontend.
endlocal
