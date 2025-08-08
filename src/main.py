import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import socketio

# Carregar variáveis de ambiente
load_dotenv()

# =================================================================
# CORREÇÃO APLICADA AQUI: Importações relativas
# Adicionado "." para que o Python encontre os módulos dentro do pacote 'src'.
# =================================================================
from .routes.user import user_router
from .routes.music import music_router
from .routes.music_list import music_list_router
from .routes.notifications import notifications_router

from .services.firebase_service import FirebaseService
from .services.cloudinary_service import CloudinaryService
from .services.websocket_service import websocket_service
from .services.keep_alive_service import keep_alive_service

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

# --- Integração do WebSocket ---
# Cria uma aplicação ASGI que combina FastAPI com Socket.IO
socket_app = socketio.ASGIApp(websocket_service.sio, app)

# --- Evento de Startup ---
@app.on_event("startup")
async def on_startup():
    print("🎵 Iniciando Alquimista Musical Backend...")
    print("🔧 Inicializando serviços externos...")
    
    # Inicializa serviços principais
    FirebaseService.initialize()
    CloudinaryService.initialize()
    
    # Inicia o keep-alive para manter a cozinha (Hugging Face) sempre ativa
    keep_alive_service.start()
    
    print("🍃 Serviços externos inicializados.")
    print("🔌 WebSocket configurado para comunicação em tempo real.")
    print("🔄 Keep-alive ativo para manter a cozinha sempre pronta.")
    print("🚀 Servidor FastAPI pronto.")

# --- Evento de Shutdown ---
@app.on_event("shutdown")
async def on_shutdown():
    print("🛑 Parando serviços...")
    keep_alive_service.stop()
    print("✅ Serviços parados com segurança.")

# --- Inclusão das Rotas da API ---
app.include_router(user_router, prefix="/api", tags=["Usuários"])
app.include_router(music_router, prefix="/api/music", tags=["Músicas"])
app.include_router(music_list_router, prefix="/api/music", tags=["Playlists"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notificações"])

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

# 1. Define o caminho para a pasta de build do frontend.
# Tornando o caminho mais robusto usando a localização do arquivo atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "static", "dist")

# 2. Verifica se o diretório de build existe
if not os.path.exists(FRONTEND_BUILD_DIR):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!! AVISO: Diretório de build do frontend não encontrado.")
    print(f"!! Caminho esperado: {FRONTEND_BUILD_DIR}")
    print(f"!! Execute 'npm run build' no diretório src/static para gerar o build.")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
else:
    # 3. Monta o diretório de arquivos estáticos
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static")
    print(f"✅ Frontend servido de: {FRONTEND_BUILD_DIR}")

# Exporta a aplicação ASGI que inclui WebSocket
application = socket_app


