# src/main.py (O Maître D' do Restaurante - VERSÃO FINAL COM CORS COMPLETO)

import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from redis import asyncio as aioredis
import socketio
from fastapi.middleware.cors import CORSMiddleware

# Carregar variáveis de ambiente no início de tudo
load_dotenv()

# --- ROTAS ---
from routes.user import user_router
from routes.music import music_router
from routes.music_list import music_list_router
from routes.notifications import notifications_router
from routes.websocket import websocket_router

# --- SERVIÇOS ---
from services.firebase_service import FirebaseService
from services.cloudinary_service import CloudinaryService
from services.websocket_service import websocket_service
from services.keep_alive_service import keep_alive_service
from services.music_generation_service import music_generation_service
from services.notification_service import notification_service
from services.redis_service import RedisService
from services.presence_service import PresenceService
from services.sync_service import SyncService
from services.cache_service import CacheService
from services.voice_processing_service import voice_processing_service

# --- BANCO DE DADOS ---
from database.database import db_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    O ciclo de vida do restaurante: abertura (startup) e fechamento (shutdown).
    """
    print("☀️  Bom dia! O Maître D' está abrindo o restaurante...")

    # 1. Conectar ao Cofre (MongoDB)
    await db_manager.connect()
    app.state.db_manager = db_manager

    # 2. Ligar a Central Elétrica (Redis)
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("❌ ERRO CRÍTICO: REDIS_URL não configurada.")
    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    
    # 3. Contratar e apresentar a equipe, guardando as chaves no app.state
    print("🤝  Maître D' está organizando o quadro de chaves dos serviços...")
    
    app.state.redis_service = RedisService(redis_client)
    app.state.cache_service = CacheService(app.state.redis_service)
    app.state.presence_service = PresenceService(app.state.redis_service)
    
    CloudinaryService.initialize()
    app.state.cloudinary_service = CloudinaryService()
    
    FirebaseService.initialize()
    app.state.firebase_service = FirebaseService()
    
    voice_processing_service.set_cloudinary_service(app.state.cloudinary_service)
    app.state.voice_processing_service = voice_processing_service
    
    websocket_service.set_presence_service(app.state.presence_service)
    app.state.websocket_service = websocket_service
    
    app.state.sync_service = SyncService(app.state.redis_service, app.state.presence_service, app.state.websocket_service)
    
    notification_service.set_sync_service(app.state.sync_service)
    app.state.notification_service = notification_service
    
    music_generation_service.set_dependencies(
        sync_service=app.state.sync_service, 
        notification_service=app.state.notification_service, 
        cloudinary_service=app.state.cloudinary_service
    )
    app.state.music_generation_service = music_generation_service
    
    keep_alive_service.set_redis_service(app.state.redis_service)

    # 4. Iniciar tarefas de fundo
    print("🚀  Maître D' está ligando os sistemas de fundo...")
    keep_alive_service.start()
    asyncio.create_task(app.state.sync_service.listen_for_events())
    
    print("✅ Restaurante aberto e totalmente operacional!")
    
    yield

    # --- LÓGICA DE ENCERRAMENTO ---
    print("🌙  Boa noite! O Maître D' está encerrando os serviços...")
    keep_alive_service.stop()
    await redis_client.close()
    await db_manager.disconnect()
    print("✅  Restaurante fechado com segurança.")

# --- CONFIGURAÇÃO DO APP FASTAPI ---
app = FastAPI(
    title="Alquimista Musical API",
    description="API para o projeto Alquimista Musical - Estúdio Virtual Completo com Feedback em Tempo Real",
    version="4.1.3-Final-CORS",
    lifespan=lifespan
)

# --- CONFIGURAÇÃO DE CORS ---
origins = [
    "http://localhost:5173",  # Para teste local do frontend
    "http://localhost:3000",  # Outra porta comum para teste local
    "https://alquimistamusical.onrender.com" # URL de produção, já que o frontend é servido daqui
]

# Middleware para CORS de requisições HTTP
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão das Rotas
app.include_router(user_router, prefix="/api", tags=["Recepcionista (Usuários)"])
app.include_router(music_router, prefix="/api/music", tags=["Garçom (Geração de Música)"])
app.include_router(music_list_router, prefix="/api/music", tags=["Maître (Playlists)"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Painel de Avisos"])
app.include_router(websocket_router, tags=["Comunicação em Tempo Real (WebSocket)"])

# Lógica para servir o Frontend
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
FRONTEND_BUILD_DIR = os.path.join(STATIC_DIR, "dist")

if os.path.exists(FRONTEND_BUILD_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD_DIR, "assets")), name="assets")
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
        if not os.path.exists(index_path):
            raise HTTPException(status_code=404, detail="index.html not found")
        return FileResponse(index_path)
    print(f"✅ Fachada do Restaurante (Frontend) configurada para ser servida de: {FRONTEND_BUILD_DIR}")
else:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!! AVISO: Fachada do Restaurante (Frontend) não encontrada em: {FRONTEND_BUILD_DIR}")
    print(f"!! Verificando em: {STATIC_DIR}")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# Ponto de Entrada ASGI com CORS para WebSocket
sio = websocket_service.sio
application = socketio.ASGIApp(
    sio, 
    other_asgi_app=app,
    cors_allowed_origins=origins
)
