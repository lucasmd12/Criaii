# Arquivo: services/websocket_service.py (VERSÃO CORRIGIDA PARA FASTAPI ROUTER)
# Função: O Garçom do Restaurante - Gerencia a comunicação em tempo real com os clientes.

import socketio
import asyncio
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

# Importamos a CLASSE do serviço com o qual ele vai interagir
from services.presence_service import PresenceService

class WebSocketService:
    """
    Serviço de WebSocket que colabora com o PresenceService para um controle de estado robusto.
    Agora projetado para ser usado com um APIRouter do FastAPI.
    """
    def __init__(self):
        # A inicialização do servidor Socket.IO é mantida para compatibilidade com ASGI
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*",
            transports=['polling', 'websocket']
        )
        
        # O Garçom agora tem um canal direto para falar com o Gerente.
        self.presence_service: Optional[PresenceService] = None
        
        # O mapa de conexões ativas agora é a fonte da verdade para envio de mensagens.
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Os eventos agora são gerenciados pelo endpoint, não registrados aqui.

    def set_presence_service(self, presence_service: PresenceService):
        """
        Método chamado pelo main.py no startup para entregar o "rádio"
        de comunicação com o Gerente de Salão.
        """
        self.presence_service = presence_service
        print("✔️  Garçom (WebSocket) recebeu o rádio para falar com o Gerente de Salão (PresenceService).")

    async def handle_connection(self, websocket: WebSocket, user_id: str):
        """
        Ponto de entrada único para uma conexão WebSocket.
        Gerencia o ciclo de vida completo da conexão de um cliente.
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        if self.presence_service:
            await self.presence_service.set_user_online(user_id)
            print(f"👍 Usuário {user_id} sentou-se à mesa e foi registrado pelo Gerente de Salão.")
        else:
            print(f"⚠️ Usuário {user_id} conectou, mas o Gerente de Salão não está disponível.")

        try:
            # Loop para manter a conexão viva.
            # No nosso caso, a comunicação é principalmente do servidor para o cliente,
            # então não precisamos processar muitas mensagens de entrada.
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            print(f"👋 Cliente {user_id} foi embora.")
            # A desconexão é tratada no bloco 'finally'.
        except Exception as e:
            print(f"🚨 Erro inesperado na conexão do cliente {user_id}: {e}")
        finally:
            # Garante que a limpeza seja feita em qualquer caso de desconexão.
            self.active_connections.pop(user_id, None)
            if self.presence_service:
                await self.presence_service.set_user_offline(user_id)
                print(f"👍 Gerente de Salão foi notificado que o cliente {user_id} saiu.")

    async def send_personal_message(self, user_id: str, event: str, data: Dict[str, Any]):
        """
        Envia uma mensagem para um usuário específico.
        Agora usa o dicionário de conexões ativas do FastAPI.
        """
        if user_id in self.active_connections:
            # O formato padrão para o cliente é um objeto com 'type' e 'payload'
            message_to_send = {"type": event, "payload": data}
            await self.active_connections[user_id].send_json(message_to_send)
        else:
            # Este log é útil para debug, mostrando que tentamos enviar uma mensagem
            # para um cliente que já havia desconectado.
            print(f"🤫 Tentativa de enviar mensagem '{event}' para o cliente {user_id}, mas ele já não está na mesa.")

    # Seus métodos de compatibilidade permanecem, agora usando a nova base mais eficiente.
    # Nenhuma outra parte do código que chama esses métodos precisa ser alterada.
    async def send_progress_update(self, user_id: str, progress_data: Dict[str, Any]):
        await self.send_personal_message(user_id, 'music_progress', progress_data)
    
    async def send_completion_notification(self, user_id: str, music_data: Dict[str, Any]):
        await self.send_personal_message(user_id, 'music_completed', music_data)
        print(f"✅ Prato finalizado! Notificação de conclusão enviada para {user_id}.")
    
    async def send_error_notification(self, user_id: str, error_data: Dict[str, Any]):
        await self.send_personal_message(user_id, 'music_error', error_data)
        print(f"❌ Ops! Algo deu errado na cozinha. Notificação de erro enviada para {user_id}.")
    
    async def emit_error(self, user_id: str, error_message: str):
        await self.send_error_notification(user_id, {'error': error_message})
    
    async def emit_progress(self, user_id: str, **kwargs):
        await self.send_progress_update(user_id, kwargs)
    
    async def emit_completion(self, user_id: str, **kwargs):
        await self.send_completion_notification(user_id, kwargs)

# Instância global do serviço WebSocket (mantemos seu padrão original)
websocket_service = WebSocketService()
