import socketio
import asyncio
from typing import Dict, Any

class WebSocketService:
    """Serviço para gerenciar comunicação em tempo real via WebSocket."""
    
    def __init__(self):
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            async_mode='asgi'
        )
        self.connected_users: Dict[str, str] = {}  # user_id -> session_id
        
        # Registrar eventos
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('join_user_room', self.handle_join_user_room)
    
    async def handle_connect(self, sid, environ):
        """Evento quando um cliente se conecta."""
        print(f"🔌 Cliente conectado: {sid}")
        await self.sio.emit('connection_status', {'status': 'connected'}, room=sid)
    
    async def handle_disconnect(self, sid):
        """Evento quando um cliente se desconecta."""
        print(f"🔌 Cliente desconectado: {sid}")
        # Remove o usuário da lista de conectados
        user_to_remove = None
        for user_id, session_id in self.connected_users.items():
            if session_id == sid:
                user_to_remove = user_id
                break
        if user_to_remove:
            del self.connected_users[user_to_remove]
    
    async def handle_join_user_room(self, sid, data):
        """Evento para associar um usuário a uma sessão WebSocket."""
        user_id = data.get('userId')
        if user_id:
            self.connected_users[user_id] = sid
            await self.sio.enter_room(sid, f"user_{user_id}")
            print(f"👤 Usuário {user_id} entrou na sala: {sid}")
            await self.sio.emit('joined_room', {'userId': user_id}, room=sid)
    
    async def send_progress_update(self, user_id: str, progress_data: Dict[str, Any]):
        """Envia atualização de progresso para um usuário específico."""
        if user_id in self.connected_users:
            room = f"user_{user_id}"
            await self.sio.emit('music_progress', progress_data, room=room)
            print(f"📊 Progresso enviado para {user_id}: {progress_data}")
        else:
            print(f"⚠️ Usuário {user_id} não está conectado via WebSocket")
    
    async def send_completion_notification(self, user_id: str, music_data: Dict[str, Any]):
        """Envia notificação de conclusão para um usuário específico."""
        if user_id in self.connected_users:
            room = f"user_{user_id}"
            await self.sio.emit('music_completed', music_data, room=room)
            print(f"✅ Notificação de conclusão enviada para {user_id}")
        else:
            print(f"⚠️ Usuário {user_id} não está conectado via WebSocket")
    
    async def send_error_notification(self, user_id: str, error_data: Dict[str, Any]):
        """Envia notificação de erro para um usuário específico."""
        if user_id in self.connected_users:
            room = f"user_{user_id}"
            await self.sio.emit('music_error', error_data, room=room)
            print(f"❌ Notificação de erro enviada para {user_id}")
        else:
            print(f"⚠️ Usuário {user_id} não está conectado via WebSocket")
    
    # Método alias para compatibilidade
    async def emit_error(self, user_id: str, error_message: str):
        """Método alias para enviar erro (compatibilidade)."""
        error_data = {
            'error': error_message,
            'timestamp': asyncio.get_event_loop().time()
        }
        await self.send_error_notification(user_id, error_data)
    
    # Método alias para compatibilidade
    async def emit_progress(self, user_id: str, step: str, progress: int, message: str = "", estimated_time: int = None):
        """Método alias para enviar progresso (compatibilidade)."""
        progress_data = {
            'step': step,
            'progress': progress,
            'message': message,
            'estimated_time': estimated_time,
            'process_id': f"proc_{user_id}_{int(asyncio.get_event_loop().time())}"
        }
        await self.send_progress_update(user_id, progress_data)
    
    # Método alias para compatibilidade
    async def emit_completion(self, user_id: str, music_name: str, music_url: str):
        """Método alias para enviar conclusão (compatibilidade)."""
        completion_data = {
            'music_name': music_name,
            'music_url': music_url,
            'timestamp': asyncio.get_event_loop().time()
        }
        await self.send_completion_notification(user_id, completion_data)

# Instância global do serviço WebSocket
websocket_service = WebSocketService()

