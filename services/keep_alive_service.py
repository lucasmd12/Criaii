# Arquivo: services/keep_alive_service.py (VERSÃO HÍBRIDA)
# Função: O Zelador do Restaurante - Garante que a Cozinha de IA esteja sempre aquecida e pronta.

import asyncio
import os
import time
from datetime import datetime
import httpx
from typing import Optional

# Importamos a CLASSE do serviço que ele vai usar
from services.redis_service import RedisService

class KeepAliveService:
    """
    Serviço para manter o Hugging Face Space sempre ativo, usando tarefas asyncio
    que é o padrão para aplicações FastAPI.
    """
    def __init__(self):
        self.HUGGING_FACE_SPACE_URL = os.getenv("HUGGING_FACE_SPACE_URL")
        self.ping_interval = 300  # 5 minutos
        self.redis_service: Optional[RedisService] = None
        self._ping_task: Optional[asyncio.Task] = None
        print("🛠️  Zelador (KeepAliveService) pronto para o trabalho.")

    def set_redis_service(self, redis_service: RedisService):
        """Permite que o main.py injete a dependência do Redis no startup."""
        self.redis_service = redis_service
        print("✔️  Zelador recebeu acesso à memória central para registrar os horários de limpeza.")

    def start(self):
        """Inicia o serviço de keep-alive de forma assíncrona."""
        if self._ping_task and not self._ping_task.done():
            print("⚠️  O Zelador já está trabalhando (Keep-alive rodando).")
            return
            
        if not self.HUGGING_FACE_SPACE_URL:
            print("❌  Endereço da Cozinha de IA não encontrado. O Zelador não pode iniciar o aquecimento.")
            return
            
        # A forma correta de rodar tarefas de background em asyncio
        self._ping_task = asyncio.create_task(self._run_keep_alive_async())
        print(f"🔄  Zelador começou a aquecer a Cozinha de IA em {self.HUGGING_FACE_SPACE_URL}.")
        print(f"⏰  Verificação de temperatura a cada {self.ping_interval} segundos.")
    
    def stop(self):
        """Para o serviço de keep-alive de forma segura."""
        if self._ping_task:
            self._ping_task.cancel()
            self._ping_task = None
            print("🛑  Zelador desligou o aquecimento da Cozinha de IA.")
    
    async def _run_keep_alive_async(self):
        """Loop principal do keep-alive, agora como uma corrotina."""
        while True:
            try:
                await self._ping_space_async()
                await asyncio.sleep(self.ping_interval)
            except asyncio.CancelledError:
                # Erro esperado quando o serviço é parado
                break
            except Exception as e:
                print(f"❌  Erro no trabalho do Zelador: {e}")
                await asyncio.sleep(60)

    async def _ping_space_async(self):
        """Envia um ping leve para o Space de forma assíncrona."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.HUGGING_FACE_SPACE_URL)
                response.raise_for_status() # Lança uma exceção para status de erro (4xx, 5xx)
            
            # Se chegamos aqui, o ping foi bem-sucedido
            if self.redis_service:
                await self.redis_service.set("system:last_keep_alive_ping", str(datetime.utcnow().timestamp()))
            
            print(f"🏓  Ping para a Cozinha de IA bem-sucedido. Temperatura OK.")

        except httpx.RequestError as e:
            print(f"🔥  ALERTA DO ZELADOR: Não foi possível alcançar a Cozinha de IA. Erro de rede: {e}")
        except httpx.HTTPStatusError as e:
            print(f"🔥  ALERTA DO ZELADOR: A Cozinha de IA respondeu com um erro: {e.response.status_code}")
        except Exception as e:
            print(f"🔥  ALERTA DO ZELADOR: Ocorreu um erro inesperado ao verificar a Cozinha de IA: {e}")

# Instância global do serviço (mantemos seu padrão)
keep_alive_service = KeepAliveService()
