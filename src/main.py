# src/main.py (Versão com Arquitetura Final Unificada)

# =================================================================
# PASSO 1: CONFIGURAÇÃO DO AMBIENTE
# =================================================================
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# =================================================================
# PASSO 2: IMPORTS PADRÃO E VARIÁVEIS DE AMBIENTE
# =================================================================
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# O CORSMiddleware não é mais necessário aqui, pois será gerenciado pelo ASGIApp
# from fastapi.middleware.cors import CORSMiddleware 
import socketio

# Carregar variáveis de ambiente
load_dotenv()


# =================================================================
# IMPORTAÇÕES DOS MÓDULOS DO PROJETO
# =================================================================
from src.routes.user import user_router
from src.routes.music import music_router
from src.routes.music_list import music_list_router
from src.routes.notifications import notifications_router
from src.services.firebase_service import FirebaseService
from src.services.cloudinary_service import CloudinaryService
from src.services.websocket_service import websocket_service
from src.services.keep_alive_service import keep_alive_service
from src.database.database import db_manager


# =================================================================
# INÍCIO DA APLICAÇÃO FASTAPI
# =================================================================

app = FastAPI(
    title="Alquimista Musical API",
    description="API para o projeto Alquimista Musical - Estúdio Virtual Completo com Feedback em Tempo Real",
    version="2.0.0"
)

# ππidcloned: Início do Bloco Antigo (Comentado)
# O middleware de CORS do FastAPI é removido para evitar conflito com o
# gerenciamento de CORS unificado do socketio.ASGIApp.
# -----------------------------------------------------------------
# origins = [
#     "https://alquimistamusical.onrender.com",
#     "http://localhost:5173",
#     "http://localhost:3000",
#     "*"
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# -----------------------------------------------------------------
# ππidcloned: Fim do Bloco Antigo

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
    # ... (código inalterado)
    keep_alive_status = keep_alive_service.get_status()
    return {"status": "healthy", "service": "Alquimista Musical", "version": "2.0.0", "websocket": "enabled", "keep_alive": keep_alive_status, "features": ["Geração de música com IA", "Feedback em tempo real via WebSocket", "Painel de notificações persistentes", "Keep-alive automático do Hugging Face", "Estúdio virtual completo"]}

@app.get("/api/websocket-info")
async def websocket_info():
    # ... (código inalterado)
    return {"endpoint": "/socket.io/", "events": {"client_to_server": ["connect", "join_user_room"], "server_to_client": ["connection_status", "joined_room", "music_progress", "music_completed", "music_error"]}, "usage": "Conecte-se e envie 'join_user_room' com {userId: 'seu_id'} para receber atualizações"}

# =================================================================
# LÓGICA PARA SERVIR O FRONTEND (React/Vite)
# A lógica de servir o frontend permanece a mesma que funcionou,
# usando a rota curinga para evitar conflitos.
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
# fulano: Início do Bloco Novo (Ativo)
# Esta é a arquitetura final e correta. O socketio.ASGIApp se torna o
# ponto de entrada principal. Ele gerencia o CORS para TUDO (HTTP e WebSocket)
# e direciona o tráfego: requisições para '/socket.io' vão para o WebSocket,
# e todas as outras vão para a aplicação FastAPI ('app').
# =================================================================
origins_final = [
    "https://alquimistamusical.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
]

application = socketio.ASGIApp(
    socketio_server=websocket_service.sio,
    other_asgi_app=app,
    cors_allowed_origins=origins_final
)
# =================================================================
# fulano: Fim do Bloco Novo
