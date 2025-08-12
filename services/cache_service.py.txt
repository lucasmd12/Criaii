# Arquivo: src/services/cache_service.py
# Função: O Buffet de Acesso Rápido - Armazena e serve pratos (dados) comuns rapidamente.

from typing import Optional, List, Dict, Any
import json
from services.redis_service import RedisService

class CacheService:
    """
    Gerencia o cache de dados da aplicação para reduzir a carga no MongoDB.
    Inspirado nas referências profissionais, com métodos semânticos e invalidação clara.
    """
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        # TTLs (Time-To-Live) em segundos, inspirados na sua referência
        self.TTL_SHORT = 300      # 5 minutos
        self.TTL_MEDIUM = 1800     # 30 minutos
        self.TTL_LONG = 3600       # 1 hora
        print("👨‍🍳 Buffet (CacheService) pronto para servir pratos rápidos.")

    # --- Métodos de Cache para Usuários ---

    async def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca os dados de um usuário do cache."""
        key = f"user:{user_id}"
        cached_data = await self.redis.get(key)
        if cached_data:
            print(f"CACHE HIT: Dados para o usuário {user_id} servidos do buffet.")
            return json.loads(cached_data)
        print(f"CACHE MISS: Dados para o usuário {user_id} não encontrados no buffet.")
        return None

    async def set_user_data(self, user_id: str, data: Dict[str, Any]):
        """Coloca os dados de um usuário no buffet (cache)."""
        key = f"user:{user_id}"
        await self.redis.set(key, json.dumps(data), ex=self.TTL_LONG)
        print(f"CACHE SET: Dados para o usuário {user_id} colocados no buffet por {self.TTL_LONG}s.")

    async def invalidate_user_data(self, user_id: str):
        """Remove os dados de um usuário do buffet (invalida o cache)."""
        key = f"user:{user_id}"
        await self.redis.delete(key)
        print(f"CACHE INVALIDATE: Dados para o usuário {user_id} removidos do buffet.")

    # --- Métodos de Cache para Listas de Músicas ---

    async def get_user_music_list(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Busca a lista de músicas de um usuário do cache."""
        key = f"musics:user:{user_id}"
        cached_data = await self.redis.get(key)
        if cached_data:
            print(f"CACHE HIT: Lista de músicas do usuário {user_id} servida do buffet.")
            return json.loads(cached_data)
        print(f"CACHE MISS: Lista de músicas do usuário {user_id} não encontrada no buffet.")
        return None

    async def set_user_music_list(self, user_id: str, data: List[Dict[str, Any]]):
        """Coloca a lista de músicas de um usuário no buffet."""
        key = f"musics:user:{user_id}"
        await self.redis.set(key, json.dumps(data), ex=self.TTL_MEDIUM)
        print(f"CACHE SET: Lista de músicas do usuário {user_id} colocada no buffet por {self.TTL_MEDIUM}s.")

    async def invalidate_user_music_list(self, user_id: str):
        """Invalida a lista de músicas de um usuário no cache."""
        # Esta é a invalidação inteligente. Quando uma música é criada ou deletada,
        # chamamos este método para garantir que a próxima busca pegue a lista atualizada do DB.
        key = f"musics:user:{user_id}"
        await self.redis.delete(key)
        print(f"CACHE INVALIDATE: Lista de músicas do usuário {user_id} removida do buffet.")

    # --- Exemplo de Invalidação por Padrão (da sua referência) ---
    
    async def invalidate_all_user_related_cache(self, user_id: str):
        """
        Invalida TODAS as chaves relacionadas a um usuário.
        Usa a capacidade do Redis de buscar chaves por padrão.
        """
        # CUIDADO: O comando KEYS pode ser lento em produção com muitas chaves.
        # Para este projeto, com um número razoável de usuários, é aceitável.
        pattern = f"*{user_id}*" # Um padrão simples para pegar 'user:123' e 'musics:user:123'
        
        # Esta é uma funcionalidade que precisaria ser adicionada ao nosso RedisService
        # Vamos mantê-la em mente para uma futura melhoria.
        print(f"INFO: A invalidação por padrão para o usuário {user_id} seria uma ótima próxima melhoria.")
        # Exemplo de como seria:
        # keys_to_delete = await self.redis.keys(pattern)
        # if keys_to_delete:
        #     await self.redis.delete(*keys_to_delete)
        
        # Por enquanto, invalidamos o que sabemos:
        await self.invalidate_user_data(user_id)
        await self.invalidate_user_music_list(user_id)

