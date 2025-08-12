# Arquivo: src/services/redis_service.py
# Função: A Central Elétrica do Restaurante - Fornece acesso à memória ultrarrápida (Redis).

from redis import asyncio as aioredis
from typing import Optional, Set
import json

class RedisService:
    """
    Encapsula toda a comunicação de baixo nível com o Redis.
    Os outros serviços (Cache, Presence, Sync) usarão este para executar os comandos.
    """
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        # Adicionamos um prefixo para garantir que as chaves deste projeto
        # não colidam com as do seu outro app VoIP.
        self.PREFIX = "alquimista:"
        print(f"⚡️ Central Elétrica (RedisService) configurada. Todas as chaves usarão o prefixo '{self.PREFIX}'.")

    def _get_key(self, key: str) -> str:
        """Adiciona o prefixo global a todas as chaves para garantir isolamento."""
        return f"{self.PREFIX}{key}"

    async def get(self, key: str) -> Optional[str]:
        """Busca um valor bruto do Redis."""
        return await self.redis.get(self._get_key(key))

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """Define um valor bruto no Redis."""
        await self.redis.set(self._get_key(key), value, ex=ex)

    async def delete(self, key: str, *keys):
        """Deleta uma ou mais chaves do Redis."""
        prefixed_keys = [self._get_key(k) for k in (key,) + keys]
        return await self.redis.delete(*prefixed_keys)

    async def sadd(self, key: str, *members: str) -> int:
        """Adiciona membros a um conjunto (Set) no Redis."""
        return await self.redis.sadd(self._get_key(key), *members)

    async def srem(self, key: str, *members: str) -> int:
        """Remove membros de um conjunto (Set) no Redis."""
        return await self.redis.srem(self._get_key(key), *members)

    async def sismember(self, key: str, member: str) -> bool:
        """Verifica se um membro pertence a um conjunto (Set) no Redis."""
        return await self.redis.sismember(self._get_key(key), member)

    async def smembers(self, key: str) -> Set[str]:
        """Retorna todos os membros de um conjunto (Set) no Redis."""
        return await self.redis.smembers(self._get_key(key))

    async def publish(self, channel: str, payload: dict):
        """Publica uma mensagem em um canal do Redis (Pub/Sub)."""
        # O nome do canal em si não precisa de prefixo, pois é um sistema separado.
        await self.redis.publish(channel, json.dumps(payload))

    async def get_pubsub(self):
        """Retorna um objeto PubSub para escutar canais."""
        return self.redis.pubsub()
