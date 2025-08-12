# src/routes/websocket.py
# Função: O Sistema de Comunicação em Tempo Real do Restaurante

from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect

# --- Injeção de Dependências ---
from dependencies import get_presence_service

# --- Importações de CLASSE para Type Hinting ---
from services.websocket_service import websocket_service
from services.presence_service import PresenceService

# --- Router do FastAPI ---
websocket_router = APIRouter()

@websocket_router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    presence_service: PresenceService = Depends(get_presence_service)
):
    """Canal de Comunicação Direta Restaurante ↔ Cliente"""
    print(f"🔄 NOVA CONEXÃO: Cliente '{user_id}' solicitando canal de comunicação direta...")
    
    # O 'websocket_service' agora é apenas um manipulador de lógica, não um endpoint.
    # A rota do FastAPI é o verdadeiro ponto de entrada.
    manager = websocket_service
    
    await manager.connect(websocket, user_id)
    
    try:
        # Loop para manter a conexão viva e escutar por mensagens (se necessário no futuro)
        while True:
            # O receive_text() aguarda por mensagens do cliente.
            # Se o cliente desconectar, ele levantará uma exceção.
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"👋 Cliente '{user_id}' desconectou do canal.")
    finally:
        # A lógica de desconexão agora é chamada aqui, no final da vida da conexão.
        await manager.disconnect(user_id, presence_service)
        print(f"🔚 Canal de comunicação para cliente '{user_id}' foi fechado.")
