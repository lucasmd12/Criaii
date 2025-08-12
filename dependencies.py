# src/dependencies.py
# Função: Central de Requisições do Restaurante - Como os funcionários pedem acesso aos recursos

from fastapi import Depends, HTTPException, Request
from typing import TYPE_CHECKING

# Usamos TYPE_CHECKING para evitar importações circulares em tempo de execução,
# mas ainda ter o autocompletar e a verificação de tipos no editor.
if TYPE_CHECKING:
    from services.redis_service import RedisService
    from services.presence_service import PresenceService
    from services.sync_service import SyncService
    from services.cache_service import CacheService
    from services.cloudinary_service import CloudinaryService
    from services.firebase_service import FirebaseService
    from services.notification_service import NotificationService
    from services.music_generation_service import MusicGenerationService
    from database.database import DatabaseConnection

# =================================================================
# FUNÇÕES DE DEPENDÊNCIA PARA OS SERVIÇOS
# =================================================================

def get_db_manager(request: Request) -> "DatabaseConnection":
    """Maître D' fornece acesso ao Gerente do Cofre (MongoDB)"""
    if not hasattr(request.app.state, 'db_manager'):
        raise HTTPException(status_code=500, detail="❌ Gerente do Cofre (DB) não está disponível!")
    return request.app.state.db_manager

def get_cache_service(request: Request) -> "CacheService":
    """Maître D' fornece acesso ao Gerente do Buffet (Cache)"""
    if not hasattr(request.app.state, 'cache_service'):
        raise HTTPException(status_code=500, detail="❌ Gerente do Buffet (Cache) não está disponível!")
    print("🍽️ Funcionário solicitou acesso ao Gerente do Buffet (Cache)")
    return request.app.state.cache_service

def get_sync_service(request: Request) -> "SyncService":
    """Maître D' fornece acesso ao Sistema de Comandas (Sync)"""
    if not hasattr(request.app.state, 'sync_service'):
        raise HTTPException(status_code=500, detail="❌ Sistema de Comandas (Sync) não está funcionando!")
    print("📋 Funcionário solicitou acesso ao Sistema de Comandas (Sync)")
    return request.app.state.sync_service

def get_music_generation_service(request: Request) -> "MusicGenerationService":
    """Maître D' fornece acesso à Cozinha (Music Generation)"""
    if not hasattr(request.app.state, 'music_generation_service'):
        raise HTTPException(status_code=500, detail="❌ Cozinha (Music Generation) não está funcionando!")
    print("🍳 Funcionário solicitou acesso à Cozinha (Music Generation)")
    return request.app.state.music_generation_service

def get_notification_service(request: Request) -> "NotificationService":
    """Maître D' fornece acesso ao Painel de Avisos (Notification)"""
    if not hasattr(request.app.state, 'notification_service'):
        raise HTTPException(status_code=500, detail="❌ Painel de Avisos (Notification) não está funcionando!")
    print("📢 Funcionário solicitou acesso ao Painel de Avisos (Notification)")
    return request.app.state.notification_service

# Adicione aqui outras funções 'get' para os serviços que suas rotas precisam,
# como get_cloudinary_service, se necessário.
