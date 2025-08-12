# Arquivo: src/services/presence_service.py
# Função: O Gerente de Salão - Sabe exatamente quais clientes (usuários) estão no restaurante.
# Usa a memória central (Redis) para nunca esquecer quem está presente.

from typing import Set, Optional
# Importamos a CLASSE, pois a instância será criada no main.py
from services.redis_service import RedisService

class PresenceService:
    """
    Gerencia o estado de presença dos usuários (online/offline) usando o Redis como memória.
    """
    def __init__(self, redis_service: Optional[RedisService]):
        self.redis = redis_service
        # Chave para o conjunto de usuários online no Redis.
        # O prefixo "alquimista:" já será adicionado pelo redis_service.
        self.ONLINE_USERS_KEY = "system:online_users"
        print("🤵‍♂️ Gerente de Salão (PresenceService) pronto para anotar as presenças.")

    async def set_user_online(self, user_id: str):
        """Registra que um usuário entrou no restaurante."""
        if not self.redis:
            print("⚠️ Gerente de Salão sem acesso à memória (Redis). Não é possível registrar presença.")
            return
        await self.redis.sadd(self.ONLINE_USERS_KEY, user_id)
        print(f"📋 Presença registrada na memória central: Usuário {user_id} está online.")

    async def set_user_offline(self, user_id: str):
        """Registra que um usuário saiu do restaurante."""
        if not self.redis:
            return
        await self.redis.srem(self.ONLINE_USERS_KEY, user_id)
        print(f"📋 Presença atualizada na memória central: Usuário {user_id} está offline.")

    async def is_user_online(self, user_id: str) -> bool:
        """Verifica se um usuário específico está no restaurante, consultando a memória central."""
        if not self.redis:
            return False
        is_online = await self.redis.sismember(self.ONLINE_USERS_KEY, user_id)
        return is_online

    async def get_online_users(self) -> Set[str]:
        """Retorna a lista de todos os clientes que estão atualmente no restaurante."""
        if not self.redis:
            return set()
        return await self.redis.smembers(self.ONLINE_USERS_KEY)
