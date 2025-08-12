# Arquivo: src/main.py (VERSÃO FINAL, COM A LINHA DO ERRO REMOVIDA)

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

load_dotenv()

# Suas importações de rotas e serviços
from routes.user import user_router
from routes.music import music_router
from routes.music_list import music_list_router
from routes.notifications import notifications_router
from routes.websocket import websocket_router
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
from database.database import db_manager

# --- CONFIGURAÇÃO DE CORS ---
# Esta parte está correta e é necessária para o HTTP
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://alquimistamusical.onrender.com"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("☀️  Bom dia! O Maître D' está abrindo o restaurante...")
    await db_manager.connect()
    app.state.db_manager = db_manager
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("❌ ERRO CRÍTICO: REDIS_URL não configurada.")
    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    print("🤝  Maître D' está organizando o quadro de chaves dos serviços...")
    app.state.redis_service = RedisService(redis_client)
    app.state.presence_service = PresenceService(app.state.redis_service)
    app.state.cache_service = CacheService(app.state.redis_service)
    
    websocket_service.set_presence_service(app.state.presence_service)
    app.state.websocket_service = websocket_service
    
    app.state.sync_service = SyncService(app.state.redis_service, app.state.presence_service, app.state.websocket_service)
    notification_service.set_sync_service(app.state.sync_service)
    app.state.notification_service = notification_service
    keep_alive_service.set_redis_service(app.state.redis_service)
    CloudinaryService.initialize()
    app.state.cloudinary_service = CloudinaryService()
    FirebaseService.initialize()
    app.state.firebase_service = FirebaseService()
    music_generation_service.set_dependencies(app.state.sync_service, app.state.notification_service, app.state.cloudinary_service)
    app.state.music_generation_service = music_generation_service
    print("🚀  Maître D' está ligando os sistemas de fundo...")
    keep_alive_service.start()
    asyncio.create_task(app.state.sync_service.listen_for_events())
    print("✅ Restaurante aberto e totalmente operacional!")
    yield
    print("🌙  Boa noite! O Maître D' está encerrando os serviços...")
    keep_alive_service.stop()
    await redis_client.close()
    await db_manager.disconnect()
    print("✅  Restaurante fechado com segurança.")

app = FastAPI(
    title="Alquimista Musical API",
    description="API para o projeto Alquimista Musical - Estúdio Virtual Completo com Feedback em Tempo Real",
    version="3.0.5-Final-Fix",
    lifespan=lifespan
)

# Adiciona o middleware de CORS para HTTP
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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "dist")

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
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# <<< INÍCIO DA CORREÇÃO >>>
# Ponto de Entrada ASGI sem o argumento que causa o erro.
sio = websocket_service.sio
application = socketio.ASGIApp(
    sio, 
    other_asgi_app=app
)
# <<< FIM DA CORREÇÃO >>>
