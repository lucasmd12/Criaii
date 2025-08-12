# src/dependencies.py
# Função: Central de Requisições do Restaurante - Como os funcionários pedem acesso aos recursos

from fastapi import Depends, HTTPException
from services.redis_service import RedisService
from services.presence_service import PresenceService
from services.sync_service import SyncService
from services.cache_service import CacheService
from services.cloudinary_service import CloudinaryService
from services.firebase_service import FirebaseService
from services.notification_service import NotificationService
from services.music_generation_service import MusicGenerationService
from database.database import get_database

def get_redis_service():
    """Maître D' fornece acesso à Central Elétrica (Redis)"""
    from main import app
    if not hasattr(app.state, 'redis_service'):
        raise HTTPException(status_code=500, detail="❌ Central Elétrica (Redis) não está funcionando!")
    print("⚡️ Funcionário solicitou acesso à Central Elétrica (Redis)")
    return app.state.redis_service

def get_presence_service():
    """Maître D' fornece acesso ao Gerente de Salão (Presence)"""
    from main import app
    if not hasattr(app.state, 'presence_service'):
        raise HTTPException(status_code=500, detail="❌ Gerente de Salão (Presence) não está disponível!")
    print("👥 Funcionário solicitou acesso ao Gerente de Salão (Presence)")
    return app.state.presence_service

def get_cache_service():
    """Maître D' fornece acesso ao Gerente do Buffet (Cache)"""
    from main import app
    if not hasattr(app.state, 'cache_service'):
        raise HTTPException(status_code=500, detail="❌ Gerente do Buffet (Cache) não está disponível!")
    print("🍽️ Funcionário solicitou acesso ao Gerente do Buffet (Cache)")
    return app.state.cache_service

def get_sync_service():
    """Maître D' fornece acesso ao Sistema de Comandas (Sync)"""
    from main import app
    if not hasattr(app.state, 'sync_service'):
        raise HTTPException(status_code=500, detail="❌ Sistema de Comandas (Sync) não está funcionando!")
    print("📋 Funcionário solicitou acesso ao Sistema de Comandas (Sync)")
    return app.state.sync_service

def get_cloudinary_service():
    """Maître D' fornece acesso ao Fotógrafo (Cloudinary)"""
    from main import app
    if not hasattr(app.state, 'cloudinary_service'):
        raise HTTPException(status_code=500, detail="❌ Fotógrafo (Cloudinary) não está disponível!")
    print("📸 Funcionário solicitou acesso ao Fotógrafo (Cloudinary)")
    return app.state.cloudinary_service

def get_notification_service():
    """Maître D' fornece acesso ao Painel de Avisos (Notification)"""
    from main import app
    if not hasattr(app.state, 'notification_service'):
        raise HTTPException(status_code=500, detail="❌ Painel de Avisos (Notification) não está funcionando!")
    print("📢 Funcionário solicitou acesso ao Painel de Avisos (Notification)")
    return app.state.notification_service

def get_music_generation_service():
    """Maître D' fornece acesso à Cozinha (Music Generation)"""
    from main import app
    if not hasattr(app.state, 'music_generation_service'):
        raise HTTPException(status_code=500, detail="❌ Cozinha (Music Generation) não está funcionando!")
    print("🍳 Funcionário solicitou acesso à Cozinha (Music Generation)")
    return app.state.music_generation_service
