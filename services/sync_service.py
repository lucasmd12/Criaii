# Arquivo: src/services/sync_service.py
# Função: O Sistema de Comandas Eletrônicas - Conecta a cozinha com o salão de forma eficiente.

import asyncio
import json
from typing import Optional

# Importamos as CLASSES dos serviços que ele vai orquestrar
from services.redis_service import RedisService
from services.presence_service import PresenceService
from services.websocket_service import WebSocketService

class SyncService:
    """
    Ouve por eventos de mudança de dados no Redis (Pub/Sub) e notifica
    os clientes conectados através do WebSocketService.
    """
    def __init__(self, redis_service: Optional[RedisService], 
                 presence_service: Optional[PresenceService], 
                 websocket_service: Optional[WebSocketService]):
        self.redis = redis_service
        self.presence = presence_service
        self.websocket = websocket_service
        self.channel_name = "alquimista:sync_events" # Canal de comunicação interna
        print("📡 Sistema de Comandas (SyncService) pronto para operar.")

    async def publish_event(self, event_type: str, user_id: str, payload: dict):
        """
        Outros serviços chamam este método para publicar uma "comanda" (evento) no sistema.
        Ex: A cozinha publica "prato_pronto" para o usuário X.
        """
        if not self.redis:
            print("⚠️ Sistema de Comandas offline (Redis indisponível). Evento não publicado.")
            return
            
        message = {"event_type": event_type, "payload": payload, "user_id": user_id}
        await self.redis.publish(self.channel_name, message)

    async def listen_for_events(self):
        """
        Loop infinito que fica escutando por novas "comandas" no canal do Redis.
        Esta é a tarefa que o main.py iniciará em background.
        """
        if not all([self.redis, self.presence, self.websocket]):
            print("❌ Sistema de Comandas (SyncService) não pode iniciar. Um ou mais serviços essenciais estão faltando.")
            return

        pubsub = await self.redis.get_pubsub()
        await pubsub.subscribe(self.channel_name)
        print(f"✅ Sistema de Comandas está escutando no canal: {self.channel_name}")

        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = json.loads(message["data"])
                    event_type = data.get("event_type")
                    payload = data.get("payload")
                    target_user_id = data.get("user_id")

                    # O SyncService pergunta ao Gerente de Salão se o cliente está na casa.
                    if await self.presence.is_user_online(target_user_id):
                        # Se estiver, ele pede ao Garçom para entregar a mensagem.
                        await self.websocket.send_personal_message(target_user_id, event_type, payload)
                        # print(f"📲 Comanda '{event_type}' entregue para o cliente {target_user_id}.")
                
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"🚨 ERRO no loop do Sistema de Comandas (SyncService): {e}")
                await asyncio.sleep(5)
