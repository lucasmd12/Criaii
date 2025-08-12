# Arquivo: services/websocket_service.py (VERSÃO HÍBRIDA - Etapa 3)
# Função: O Garçom do Restaurante - Gerencia a comunicação em tempo real com os clientes.

import socketio
import asyncio
from typing import Dict, Any, Optional

# Importamos a CLASSE do serviço com o qual ele vai interagir
from services.presence_service import PresenceService

class WebSocketService:
    """
    Serviço de WebSocket que colabora com o PresenceService para um controle de estado robusto.
    """
    def __init__(self):
        # A inicialização do servidor Socket.IO permanece a mesma.
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*",
            transports=['polling', 'websocket']
        )
        
        # O Garçom agora tem um canal direto para falar com o Gerente.
        # Ele será "entregue" pelo main.py no startup.
        self.presence_service: Optional[PresenceService] = None
        
        # Este mapa de memória local agora serve apenas para uma função:
        # saber qual user_id desconectou, já que o evento 'disconnect' só nos dá o 'sid'.
        self.sid_to_user_map: Dict[str, str] = {}
        
        # Registrar os eventos que o Garçom sabe ouvir.
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('join_user_room', self.handle_join_user_room)

    def set_presence_service(self, presence_service: PresenceService):
        """
        Método chamado pelo main.py no startup para entregar o "rádio"
        de comunicação com o Gerente de Salão.
        """
        self.presence_service = presence_service
        print("✔️  Garçom (WebSocket) recebeu o rádio para falar com o Gerente de Salão (PresenceService).")

    async def handle_connect(self, sid, environ):
        """Evento quando um cliente chega na porta do restaurante."""
        print(f"🚪 Um novo cliente chegou ao restaurante e recebeu a senha de Wi-Fi. (SID: {sid})")
        await self.sio.emit('connection_status', {'status': 'connected'}, room=sid)
    
    async def handle_disconnect(self, sid):
        """Evento quando um cliente vai embora."""
        print(f"👋 Cliente está indo embora... (SID: {sid})")
        
        # Descobre quem era o cliente usando nosso mapa local.
        user_id = self.sid_to_user_map.pop(sid, None)
        
        if user_id and self.presence_service:
            # Avisa o gerente que o usuário saiu para que ele possa riscar da lista principal no Redis.
            await self.presence_service.set_user_offline(user_id)
        elif user_id:
            print(f"⚠️ Usuário {user_id} desconectou, mas o Gerente de Salão não está disponível para ser notificado.")
        else:
            print(f"👻 Um cliente anônimo (SID: {sid}) foi embora sem se identificar.")
    
    async def handle_join_user_room(self, sid, data):
        """Evento quando o cliente se identifica e senta à mesa."""
        user_id = data.get('userId') if isinstance(data, dict) else None
        
        if user_id:
            # Mapeia o SID ao UserID para referência futura (principalmente no disconnect).
            self.sid_to_user_map[sid] = user_id
            # Coloca o cliente em sua própria "sala" VIP para receber mensagens diretas.
            self.sio.enter_room(sid, f"user_{user_id}")
            
            print(f"👍 Usuário {user_id} sentou-se à mesa VIP 'user_{user_id}'. (SID: {sid})")
            
            # Avisa o gerente para anotar a presença do cliente na lista principal do Redis.
            if self.presence_service:
                await self.presence_service.set_user_online(user_id)
            
            await self.sio.emit('joined_room', {'userId': user_id, 'status': 'success'}, room=sid)
        else:
            print(f"🤔 Cliente {sid} tentou sentar sem se identificar. Pedido ignorado.")
            await self.sio.emit('join_error', {'message': 'O ID do usuário (userId) é obrigatório.'}, room=sid)

    async def send_personal_message(self, user_id: str, event: str, data: Dict[str, Any]):
        """
        Envia uma mensagem para a sala VIP de um usuário específico.
        Esta é a forma mais eficiente e agora é o método central de envio.
        """
        room_name = f"user_{user_id}"
        await self.sio.emit(event, data, room=room_name)

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
