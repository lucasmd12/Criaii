# src/routes/notifications.py (O Painel de Avisos e Gerente do Salão - VERSÃO HÍBRIDA OTIMIZADA)

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

# --- Injeção de Dependências ---
from .user import get_current_user_id
from dependencies import get_db_manager, get_notification_service, get_sync_service

# --- Importações de CLASSE para Type Hinting ---
from services.notification_service import NotificationService
from services.sync_service import SyncService
from database.database import DatabaseConnection

# --- Router do FastAPI ---
notifications_router = APIRouter()

# --- Modelos de Resposta (Pydantic) - Mantidos para clareza da documentação da API ---
class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    timestamp: str
    read: bool
    data: dict = {}

class ProcessHistoryResponse(BaseModel):
    process_id: str
    user_id: str
    music_name: str
    status: str
    progress: int
    message: str
    timestamp: str
    estimated_time: Optional[int] = None
    step: str

# =================================================================
# ROTAS DO PAINEL DE AVISOS
# =================================================================

@notifications_router.get("/")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    notification_service: NotificationService = Depends(get_notification_service),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Gerente buscando os últimos avisos no painel para o cliente."""
    print(f"👨‍💼 Gerente: Cliente {user_id} está checando seu painel de avisos.")
    notifications = await notification_service.get_user_notifications(
        db_manager, user_id=user_id, limit=limit, skip=skip
    )
    unread_count = await notification_service.get_unread_count(db_manager, user_id)
    print(f"✅ Gerente: {len(notifications)} avisos encontrados para o cliente {user_id} ({unread_count} não lidos).")
    return {"notifications": notifications, "unread_count": unread_count}

@notifications_router.get("/unread-count")
async def get_unread_count(
    user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Gerente fazendo uma contagem rápida de novos avisos para o cliente."""
    print(f"👨‍💼 Gerente: Contando rapidamente os avisos não lidos para o cliente {user_id}.")
    count = await notification_service.get_unread_count(db_manager, user_id)
    print(f"✅ Gerente: Cliente {user_id} tem {count} avisos novos.")
    return {"unread_count": count}

@notifications_router.post("/mark-read")
async def mark_notifications_as_read(
    user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    notification_service: NotificationService = Depends(get_notification_service),
    sync_service: SyncService = Depends(get_sync_service),
    notification_ids: Optional[List[str]] = None
):
    """Gerente arquivando avisos antigos do painel do cliente."""
    action = "todos os avisos" if not notification_ids else f"{len(notification_ids)} aviso(s) específico(s)"
    print(f"👨‍💼 Gerente: Cliente {user_id} está arquivando {action} do seu painel.")
    
    await notification_service.mark_notifications_as_read(db_manager, user_id, notification_ids)
    print(f"✅ Gerente: Avisos do cliente {user_id} foram arquivados com sucesso.")
    
    await sync_service.publish_event(
        event_type="notifications_updated",
        user_id=user_id,
        payload={"message": "Suas notificações foram atualizadas."}
    )
    print(f"📡 Gerente enviou uma comanda eletrônica: 'Avisar cliente {user_id} para checar seu painel de avisos.'")

    return {"message": "Avisos arquivados com sucesso!"}

@notifications_router.get("/process-history")
async def get_process_history(
    user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    notification_service: NotificationService = Depends(get_notification_service),
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0)
):
    """Gerente consultando o livro de comandas antigas do cliente."""
    print(f"👨‍💼 Gerente: Cliente {user_id} está revisando seu histórico de pedidos.")
    history = await notification_service.get_process_history(
        db_manager, user_id=user_id, limit=limit, skip=skip
    )
    print(f"✅ Gerente: Histórico de {len(history)} pedidos encontrado para o cliente {user_id}.")
    return {"history": history}

@notifications_router.get("/dashboard")
async def get_dashboard_data(
    user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Gerente preparando um resumo do movimento do restaurante para o cliente."""
    print(f"👨‍💼 Gerente: Compilando dados do painel geral para o cliente {user_id}.")
    data = await notification_service.get_dashboard_data(db_manager, user_id)
    print(f"✅ Gerente: Resumo do dashboard pronto para o cliente {user_id}.")
    return data
