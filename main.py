# Arquivo: src/main.py (VERSÃO HÍBRIDA FINAL)
# Função: O Maître D' do Restaurante - Orquestra a abertura, o fechamento e a operação de todos os serviços.

import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import socketio
from redis import asyncio as aioredis

# Carregar variáveis de ambiente no início de tudo
load_dotenv()

# =================================================================
# IMPORTAÇÕES DOS MÓDULOS DO PROJETO
# =================================================================
# Rotas (os caminhos dos clientes)
from routes.user import user_router
from routes.music import music_router
from routes.music_list import music_list_router
from routes.notifications import notifications_router

# Serviços (os funcionários do restaurante)
from services.firebase_service import FirebaseService
from services.cloudinary_service import CloudinaryService
from services.websocket_service import websocket_service
from services.keep_alive_service import keep_alive_service
from services.music_generation_service import music_generation_service
from services.notification_service import notification_service

# Novos Serviços (a nova infraestrutura e funcionários)
from services.redis_service import RedisService
from services.presence_service import PresenceService
from services.sync_service import SyncService
from services.cache_service import CacheService

# Banco de Dados (o cofre e o livro de receitas)
from database.database import db_manager

# =================================================================
# GERENCIADOR DE CICLO DE VIDA (LIFESPAN)
# =================================================================
# O 'lifespan' é a forma moderna de lidar com eventos de startup e shutdown no FastAPI.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- ABERTURA DO RESTAURANTE (STARTUP) ---
    print("☀️  Bom dia! O Maître D' está abrindo o restaurante...")

    # 1. Conectar ao Cofre e ao Livro de Receitas (MongoDB)
    await db_manager.connect()

    # 2. Ligar a Central Elétrica (Redis)
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("❌ ERRO CRÍTICO: REDIS_URL não configurada. O restaurante não pode abrir sem energia.")
    
    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    
    # 3. Contratar e apresentar os funcionários (Injeção de Dependência)
    print("🤝  Maître D' está apresentando a equipe...")
    
    # Serviços base
    redis_service = RedisService(redis_client)
    presence_service = PresenceService(redis_service)
    cache_service = CacheService(redis_service)
    
    # Serviços que dependem de outros
    websocket_service.set_presence_service(presence_service)
    sync_service = SyncService(redis_service, presence_service, websocket_service)
    notification_service.set_sync_service(sync_service)
    keep_alive_service.set_redis_service(redis_service)
    
    # Serviços de negócio
    CloudinaryService.initialize()
    FirebaseService.initialize() # Mantido, mesmo que desabilitado
    music_generation_service.set_dependencies(sync_service, notification_service, CloudinaryService())

    # 4. Iniciar tarefas de fundo (Zelador e Sistema de Comandas)
    print("🚀  Maître D' está ligando os sistemas de fundo...")
    keep_alive_service.start()
    asyncio.create_task(sync_service.listen_for_events())
    
    print("✅ Restaurante aberto e totalmente operacional!")
    
    yield # A aplicação roda aqui

    # --- FECHAMENTO DO RESTAURANTE (SHUTDOWN) ---
    print("🌙  Boa noite! O Maître D' está encerrando os serviços...")
    keep_alive_service.stop()
    await redis_client.close()
    await db_manager.disconnect()
    print("✅  Restaurante fechado com segurança.")

# =================================================================
# INÍCIO DA APLICAÇÃO FASTAPI
# =================================================================
app = FastAPI(
    title="Alquimista Musical API",
    description="API para o projeto Alquimista Musical - Estúdio Virtual Completo com Feedback em Tempo Real",
    version="2.1.0-Robust", # Nova versão para refletir a arquitetura
    lifespan=lifespan # Usando o novo gerenciador de ciclo de vida
)

# --- Inclusão das Rotas da API (sem mudanças) ---
app.include_router(user_router, prefix="/api", tags=["Recepcionista (Usuários)"])
app.include_router(music_router, prefix="/api/music", tags=["Garçom (Geração de Música)"])
app.include_router(music_list_router, prefix="/api/music", tags=["Maître (Playlists)"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Painel de Avisos"])

# --- LÓGICA PARA SERVIR O FRONTEND (sem mudanças) ---
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "static", "dist")
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

# =================================================================
# PONTO DE ENTRADA FINAL DA APLICAÇÃO (ASGI)
# =================================================================
# Unifica o FastAPI (HTTP) com o Socket.IO (WebSocket)
application = socketio.ASGIApp(
    socketio_server=websocket_service.sio,
    other_asgi_app=app
)
