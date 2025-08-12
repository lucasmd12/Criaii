# src/routes/websocket.py

from fastapi import APIRouter, WebSocket, Depends
from services.websocket_service import websocket_service
from services.presence_service import PresenceService

# Criamos um router específico para o WebSocket
websocket_router = APIRouter()

# Esta é a função de dependência que o FastAPI usará
# para obter o PresenceService, sem confundi-lo com um modelo de resposta.
async def get_presence_service() -> PresenceService:
    # Assumindo que o presence_service é inicializado no main.py
    # e está acessível de alguma forma.
    # A melhor abordagem é injetá-lo no websocket_service no startup.
    if not websocket_service.presence_service:
        raise RuntimeError("PresenceService não foi injetado no WebSocketService.")
    return websocket_service.presence_service

@websocket_router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    presence_service: PresenceService = Depends(get_presence_service)
):
    """Endpoint WebSocket para comunicação em tempo real."""
    await websocket_service.handle_connection(websocket, user_id, presence_service)
