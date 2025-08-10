# src/main.py

# =================================================================
# PASSO 1: CONFIGURAÇÃO DO AMBIENTE (A CURA DEFINITIVA)
# =================================================================
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# =================================================================
# PASSO 2: IMPORTS PADRÃO E VARIÁVEIS DE AMBIENTE
# =================================================================
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException # Adicionado HTTPException para a nova rota
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

# --- Configuração do CORS ---
origins = [
    "https://alquimistamusical.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "*"  # Para desenvolvimento
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Evento de Startup ---
@app.on_event("startup")
async def on_startup():
    """O Gerente Geral abre o restaurante para o dia."""
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

# --- Evento de Shutdown ---
@app.on_event("shutdown")
async def on_shutdown():
    """O Gerente Geral fecha o restaurante no final do dia."""
    print("🌙  Boa noite! Encerrando os serviços...")
    keep_alive_service.stop()
    await db_manager.disconnect()
    print("✅  Restaurante fechado com segurança.")

# --- Inclusão das Rotas da API ---
app.include_router(user_router, prefix="/api", tags=["Recepcionista (Usuários)"])
app.include_router(music_router, prefix="/api/music", tags=["Garçom (Geração de Música)"])
app.include_router(music_list_router, prefix="/api/music", tags=["Maître (Playlists)"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Painel de Avisos"])

# --- Rota de Health Check ---
@app.get("/health")
async def health_check():
    keep_alive_status = keep_alive_service.get_status()
    return {
        "status": "healthy",
        "service": "Alquimista Musical",
        "version": "2.0.0",
        "websocket": "enabled",
        "keep_alive": keep_alive_status,
        "features": [
            "Geração de música com IA",
            "Feedback em tempo real via WebSocket", 
            "Painel de notificações persistentes",
            "Keep-alive automático do Hugging Face",
            "Estúdio virtual completo"
        ]
    }

# --- Rota para informações do WebSocket ---
@app.get("/api/websocket-info")
async def websocket_info():
    return {
        "endpoint": "/socket.io/",
        "events": {
            "client_to_server": [
                "connect",
                "join_user_room"
            ],
            "server_to_client": [
                "connection_status",
                "joined_room", 
                "music_progress",
                "music_completed",
                "music_error"
            ]
        },
        "usage": "Conecte-se e envie 'join_user_room' com {userId: 'seu_id'} para receber atualizações"
    }

# =================================================================
# LÓGICA PARA SERVIR O FRONTEND (React/Vite)
# =================================================================

# ππidcloned: Início do Bloco Antigo (Comentado)
# Este método usa app.mount e causa conflito com WebSockets.
# -----------------------------------------------------------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "static", "dist")
# 
# if not os.path.exists(FRONTEND_BUILD_DIR):
#     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#     print(f"!! AVISO: Diretório de build do frontend não encontrado.")
#     print(f"!! Caminho esperado: {FRONTEND_BUILD_DIR}")
#     print(f"!! Execute 'npm run build' no diretório src/static para gerar o build.")
#     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
# else:
#     app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static")
#     print(f"✅ Frontend servido de: {FRONTEND_BUILD_DIR}")
# -----------------------------------------------------------------
# ππidcloned: Fim do Bloco Antigo

# fulano: Início do Bloco Novo (Ativo)
# Este método usa uma rota curinga para servir o frontend,
# resolvendo o conflito com WebSockets.
# -----------------------------------------------------------------
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "static", "dist")

# Verifica se a pasta de build existe para dar um aviso claro no log
if os.path.exists(FRONTEND_BUILD_DIR):
    # Monta a pasta de assets (JS, CSS, etc.) de forma específica
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "assets")), name="assets")

    # Rota curinga que serve o index.html para qualquer outro caminho
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
        return FileResponse(index_path)
    
    print(f"✅ Frontend configurado para ser servido de: {FRONTEND_BUILD_DIR}")
else:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!! AVISO: Diretório de build do frontend não encontrado.")
    print(f"!! Caminho esperado: {FRONTEND_BUILD_DIR}")
    print(f"!! O app irá rodar, mas o frontend não será servido.")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
# -----------------------------------------------------------------
# fulano: Fim do Bloco Novo

# Exporta a aplicação ASGI que inclui WebSocket
# application = socketio.ASGIApp(websocket_service.sio, app)

# ADICIONE ESTA LINHA NO LUGAR
app.mount("/", websocket_service.sio)

