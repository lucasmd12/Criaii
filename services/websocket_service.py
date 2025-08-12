# Arquivo: services/websocket_service.py (VERSÃO FINAL E CORRETA)
# Função: O Garçom do Restaurante - Gerencia a comunicação em tempo real com os clientes.

import socketio
from typing import Optional, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

# Importamos a CLASSE do serviço com o qual ele vai interagir
from services.presence_service import PresenceService

class WebSocketService:
    """
    Serviço de WebSocket que colabora com o PresenceService para um controle de estado robusto.
    """
    def __init__(self):
        # <<< INÍCIO DA CORREÇÃO DEFINITIVA >>>
        # A configuração de CORS é passada AQUI, na criação do servidor principal.
        # O "*" permite todas as origens, o que é seguro para começar.
        # Mais tarde, podemos substituir por uma lista específica se necessário.
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*" 
        )
        # <<< FIM DA CORREÇÃO DEFINITIVA >>>
        
        self.presence_service: Optional[PresenceService] = None
        self.register_events() # Adicionando a chamada que estava faltando
        print("✔️  Rádio do Garçom (WebSocket) pronto para receber conexões.")

    def set_presence_service(self, presence_service: PresenceService):
        """
        Método chamado pelo main.py no startup para entregar o "rádio"
        de comunicação com o Gerente de Salão.
        """
        self.presence_service = presence_service
        print("✔️  Garçom (WebSocket) recebeu o rádio para falar com o Gerente de Salão (PresenceService).")

    def register_events(self):
        """Registra os manipuladores de eventos do Socket.IO."""
        @self.sio.event
        async def connect(sid, environ):
            # Sua lógica de conexão aqui
            user_id = environ.get('HTTP_X_USER_ID')
            if not user_id:
                print(f"🔌 Conexão anônima rejeitada: {sid}")
                return False
            
            await self.sio.save_session(sid, {'user_id': user_id})
            if self.presence_service:
                await self.presence_service.user_connected(user_id, sid)
            print(f"🔌 Cliente conectado: {sid}, Usuário: {user_id}")

        @self.sio.event
        async def disconnect(sid):
            # Sua lógica de desconexão aqui
            session = await self.sio.get_session(sid)
            user_id = session.get('user_id')
            if user_id and self.presence_service:
                await self.presence_service.user_disconnected(user_id, sid)
            print(f"🔌 Cliente desconectado: {sid}, Usuário: {user_id}")

    async def send_personal_message(self, user_id: str, event: str, data: Dict[str, Any]):
        """Envia uma mensagem para um usuário específico."""
        # Encontra o SID do usuário para enviar a mensagem
        user_sids = self.presence_service.get_user_sids(user_id)
        if user_sids:
            for sid in user_sids:
                await self.sio.emit(event, data, to=sid)
        else:
            print(f"🤫 Tentativa de enviar mensagem '{event}' para o cliente {user_id}, mas ele não está na mesa.")

# Instância global do serviço WebSocket
websocket_service = WebSocketService()
