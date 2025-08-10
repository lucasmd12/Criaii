# src/main.py (Versão com Arquitetura Final Simplificada e Corrigida)

# =================================================================
# PASSO 1: CONFIGURAÇÃO DO AMBIENTE
# =================================================================
# A linha 'sys.path.insert' foi removida.
# O comando de start com 'PYTHONPATH=.' torna esta manipulação
# manual do path desnecessária e potencialmente conflituosa.
import sys
import os


# =================================================================
# PASSO 2: IMPORTS PADRÃO E VARIÁVEIS DE AMBIENTE
# =================================================================
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import socketio

# Carregar variáveis de ambiente
load_dotenv()


# =================================================================
# IMPORTAÇÕES DOS MÓDULOS DO PROJETO
# =================================================================
from  routes.user import user_router
from  routes.music import music_router
from  routes.music_list import music_list_router
from  routes.notifications import notifications_router
from  services.firebase_service import FirebaseService
from  services.cloudinary_service import CloudinaryService
from  services.websocket_service import websocket_service
from  services.keep_alive_service import keep_alive_service
from  database.database import db_manager


# =================================================================
# INÍCIO DA APLICAÇÃO FASTAPI
# =================================================================

app = FastAPI(
    title="Alquimista Musical API",
    description="API para o projeto Alquimista Musical - Estúdio Virtual Completo com Feedback em Tempo Real",
    version="2.0.0"
)

# O middleware de CORS do FastAPI foi removido para evitar conflitos.

# --- Eventos de Startup e Shutdown (Permanecem os mesmos) ---
@app.on_event("startup")
async def on_startup():
    print("☀️  Bom dia! Iniciando o Alquimista Musical Backend...")
    await db_manager.connect()
    print("🔧  Inicializando serviços externos (Firebase, Cloudinary)...")
    FirebaseService.initialize()
    CloudinaryService.initialize()
    keep_alive_service.start()
    print("🍃  Serviços externos prontos.")
    print("🔌  WebSocket configurado para comunicação em tempo real.")
    print("🔄  Keep-alive ativo para manter a cozinha sempre pronta.")
    print("🚀  Restaurante aberto! Servidor FastAPI pronto para receber clientes.")

@app.on_event("shutdown")
async def on_shutdown():
    print("🌙  Boa noite! Encerrando os serviços...")
    keep_alive_service.stop()
    await db_manager.disconnect()
    print("✅  Restaurante fechado com segurança.")

# --- Inclusão das Rotas da API (Permanecem as mesmas) ---
app.include_router(user_router, prefix="/api", tags=["Recepcionista (Usuários)"])
app.include_router(music_router, prefix="/api/music", tags=["Garçom (Geração de Música)"])
app.include_router(music_list_router, prefix="/api/music", tags=["Maître (Playlists)"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Painel de Avisos"])

# --- Rotas de Health Check e Info (Permanecem as mesmas) ---
@app.get("/health")
async def health_check():
    keep_alive_status = keep_alive_service.get_status()
    return {"status": "healthy", "service": "Alquimista Musical", "version": "2.0.0", "websocket": "enabled", "keep_alive": keep_alive_status, "features": ["Geração de música com IA", "Feedback em tempo real via WebSocket", "Painel de notificações persistentes", "Keep-alive automático do Hugging Face", "Estúdio virtual completo"]}

@app.get("/api/websocket-info")
async def websocket_info():
    return {"endpoint": "/socket.io/", "events": {"client_to_server": ["connect", "join_user_room"], "server_to_client": ["connection_status", "joined_room", "music_progress", "music_completed", "music_error"]}, "usage": "Conecte-se e envie 'join_user_room' com {userId: 'seu_id'} para receber atualizações"}

# =================================================================
# LÓGICA PARA SERVIR O FRONTEND (React/Vite)
# =================================================================
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "static", "dist")

if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "assets")), name="assets")
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
        if not os.path.exists(index_path):
            raise HTTPException(status_code=404, detail="index.html not found")
        return FileResponse(index_path)
    print(f"✅ Frontend configurado para ser servido de: {FRONTEND_BUILD_DIR}")
else:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!! AVISO: Diretório de build do frontend não encontrado: {FRONTEND_BUILD_DIR}")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# =================================================================
# PONTO DE ENTRADA FINAL DA APLICAÇÃO (ASGI)
# =================================================================
# A configuração de CORS foi movida para o websocket_service.py,
# que é o lugar correto. O ASGIApp agora atua apenas como um unificador
# simples e limpo entre o FastAPI e o Socket.IO.
application = socketio.ASGIApp(
    socketio_server=websocket_service.sio,
    other_asgi_app=app
)
