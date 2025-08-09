# src/routes/notifications.py (O Painel de Avisos e Gerente do Salão)

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from routes.user import get_current_user_id
from models.notification_models import notification_service

# --- Router do FastAPI ---
notifications_router = APIRouter()

# --- Modelos de Resposta (Pydantic) ---
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
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Gerente buscando os últimos avisos no painel para o cliente."""
    print(f"👨‍💼 Gerente: Cliente {user_id} está checando seu painel de avisos.")
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        unread_count = await notification_service.get_unread_count(user_id)
        print(f"✅ Gerente: {len(notifications)} avisos encontrados para o cliente {user_id} ({unread_count} não lidos).")
        return {"notifications": notifications, "unread_count": unread_count}
    except Exception as e:
        print(f"🚨 Gerente: Erro ao buscar avisos para o cliente {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um problema ao carregar o painel de avisos."
        )

@notifications_router.get("/unread-count")
async def get_unread_count(user_id: str = Depends(get_current_user_id)):
    """Gerente fazendo uma contagem rápida de novos avisos para o cliente."""
    print(f"👨‍💼 Gerente: Contando rapidamente os avisos não lidos para o cliente {user_id}.")
    try:
        count = await notification_service.get_unread_count(user_id)
        print(f"✅ Gerente: Cliente {user_id} tem {count} avisos novos.")
        return {"unread_count": count}
    except Exception as e:
        print(f"🚨 Gerente: Erro ao fazer a contagem de avisos para o cliente {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um problema ao verificar novos avisos."
        )

@notifications_router.post("/mark-read")
async def mark_notifications_as_read(
    user_id: str = Depends(get_current_user_id),
    notification_ids: Optional[List[str]] = None
):
    """Gerente arquivando avisos antigos do painel do cliente."""
    action = "todos os avisos" if not notification_ids else f"{len(notification_ids)} aviso(s) específico(s)"
    print(f"👨‍💼 Gerente: Cliente {user_id} está arquivando {action} do seu painel.")
    try:
        if notification_ids:
            await notification_service.mark_notifications_as_read(user_id, notification_ids)
        else:
            await notification_service.mark_notifications_as_read(user_id)
        
        print(f"✅ Gerente: Avisos do cliente {user_id} foram arquivados com sucesso.")
        return {"message": "Avisos arquivados com sucesso!"}
    except Exception as e:
        print(f"🚨 Gerente: Erro ao arquivar avisos para o cliente {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um problema ao arquivar os avisos."
        )

@notifications_router.get("/process-history")
async def get_process_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0)
):
    """Gerente consultando o livro de comandas antigas do cliente."""
    print(f"👨‍💼 Gerente: Cliente {user_id} está revisando seu histórico de pedidos.")
    try:
        history = await notification_service.get_process_history(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        print(f"✅ Gerente: Histórico de {len(history)} pedidos encontrado para o cliente {user_id}.")
        return {"history": history}
    except Exception as e:
        print(f"🚨 Gerente: Erro ao buscar histórico de pedidos para o cliente {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um problema ao buscar seu histórico de pedidos."
        )

@notifications_router.get("/dashboard")
async def get_dashboard_data(user_id: str = Depends(get_current_user_id)):
    """Gerente preparando um resumo do movimento do restaurante para o cliente."""
    print(f"👨‍💼 Gerente: Compilando dados do painel geral para o cliente {user_id}.")
    try:
        data = await notification_service.get_dashboard_data(user_id)
        print(f"✅ Gerente: Resumo do dashboard pronto para o cliente {user_id}.")
        return data
    except Exception as e:
        print(f"🚨 Gerente: Erro ao compilar os dados do dashboard para o cliente {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um problema ao preparar o resumo do restaurante."
        )
