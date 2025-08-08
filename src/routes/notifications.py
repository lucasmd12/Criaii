from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from .user import get_current_user_id
from ..models.notification_models import notification_service

# --- Router do FastAPI ---
notifications_router = APIRouter()

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
# ROTAS DE NOTIFICAÇÕES
# =================================================================

@notifications_router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Retorna as notificações do usuário.
    """
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        return notifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar notificações: {str(e)}"
        )

@notifications_router.get("/unread-count")
async def get_unread_count(user_id: str = Depends(get_current_user_id)):
    """
    Retorna a quantidade de notificações não lidas.
    """
    try:
        count = await notification_service.get_unread_count(user_id)
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao contar notificações: {str(e)}"
        )

@notifications_router.post("/mark-read")
async def mark_notifications_as_read(
    user_id: str = Depends(get_current_user_id),
    notification_ids: Optional[List[str]] = None
):
    """
    Marca notificações como lidas.
    Se notification_ids não for fornecido, marca todas como lidas.
    """
    try:
        if notification_ids:
            await notification_service.mark_notifications_read(user_id, notification_ids)
        else:
            await notification_service.mark_all_notifications_read(user_id)
        
        return {"message": "Notificações marcadas como lidas"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao marcar notificações: {str(e)}"
        )

@notifications_router.get("/process-history", response_model=List[ProcessHistoryResponse])
async def get_process_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0)
):
    """
    Retorna o histórico de processos de geração de música.
    """
    try:
        history = await notification_service.get_process_history(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )

@notifications_router.get("/dashboard")
async def get_dashboard_data(user_id: str = Depends(get_current_user_id)):
    """
    Retorna dados consolidados para o dashboard.
    """
    try:
        data = await notification_service.get_dashboard_data(user_id)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados do dashboard: {str(e)}"
        )

