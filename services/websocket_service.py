# Arquivo: services/websocket_service.py (VERSÃO CORRIGIDA E COMPATÍVEL)
# Função: O Garçom do Restaurante - Gerencia a comunicação em tempo real com os clientes.

import socketio
from typing import Optional, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect # Importações que você já usa

# Importamos a CLASSE do serviço com o qual ele vai interagir
from services.presence_service import PresenceService

class WebSocketService:
    """
    Serviço de WebSocket que colabora com o PresenceService para um controle de estado robusto.
    """
    def __init__(self):
        # <<< INÍCIO DA CORREÇÃO >>>
        # O servidor agora é criado para ACEITAR a configuração de CORS,
        # que será passada pelo main.py.
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=[] # Inicializa como vazio. O main.py vai preencher.
        )
        # <<< FIM DA CORREÇÃO >>>
        
        self.presence_service: Optional[PresenceService] = None
        self.active_connections: Dict[str, WebSocket] = {}
        print("✔️  Rádio do Garçom (WebSocket) pronto para receber conexões.")

    # <<< INÍCIO DA NOVA FUNÇÃO >>>
    def set_allowed_origins(self, origins: list):
        """Permite que o main.py configure as origens permitidas dinamicamente."""
        self.sio.cors_allowed_origins = origins
        print(f"📡 WebSocket configurado para aceitar conexões de: {origins}")
    # <<< FIM DA NOVA FUNÇÃO >>>

    def set_presence_service(self, presence_service: PresenceService):
        """
        Método chamado pelo main.py no startup para entregar o "rádio"
        de comunicação com o Gerente de Salão.
        """
        self.presence_service = presence_service
        print("✔️  Garçom (WebSocket) recebeu o rádio para falar com o Gerente de Salão (PresenceService).")

    # Seus métodos handle_connection e send_personal_message não precisam de alteração
    # e foram removidos desta resposta para focar na correção do __init__.
    # Mantenha os seus métodos como estão.
    # O importante é a mudança no __init__ e a adição do set_allowed_origins.

# Instância global do serviço WebSocket
websocket_service = WebSocketService()
