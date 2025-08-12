# src/routes/websocket.py
# Função: O Sistema de Comunicação em Tempo Real do Restaurante - Conecta os clientes diretamente com a cozinha

from fastapi import APIRouter, WebSocket, Depends
from services.websocket_service import websocket_service
from services.presence_service import PresenceService

# Criamos um router específico para o WebSocket
websocket_router = APIRouter()

async def get_presence_service():
    """
    Maître D' obtém o Gerente de Salão (PresenceService) para o WebSocket.
    CORREÇÃO CRÍTICA: Removida anotação de tipo de retorno para evitar erro Pydantic.
    """
    if not websocket_service.presence_service:
        print("❌ ERRO: Gerente de Salão (PresenceService) não foi apresentado ao Sistema de Comunicação!")
        print("🔧 SOLUÇÃO: Verifique se websocket_service.set_presence_service() foi chamado no main.py")
        raise RuntimeError(
            "FALHA NA OPERAÇÃO: PresenceService não foi injetado no WebSocketService. "
            "Verifique se websocket_service.set_presence_service(presence_service) foi executado durante o startup."
        )
    
    print("✅ Maître D' conectou com sucesso o Gerente de Salão para comunicação em tempo real")
    return websocket_service.presence_service

@websocket_router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    presence_service: PresenceService = Depends(get_presence_service)
):
    """Canal de Comunicação Direta Restaurante ↔ Cliente"""
    print(f"🔄 NOVA CONEXÃO: Cliente '{user_id}' solicitando canal de comunicação direta...")
    
    try:
        await websocket_service.handle_connection(websocket, user_id, presence_service)
        print(f"✅ Canal estabelecido com sucesso para cliente '{user_id}'")
    except Exception as e:
        print(f"❌ FALHA NA COMUNICAÇÃO com cliente '{user_id}': {str(e)}")
        print("🔧 DIAGNÓSTICO: Verificar Redis, PresenceService e WebSocketService")
        raise
    finally:
        print(f"🔚 Encerrando conexão para cliente '{user_id}'")
