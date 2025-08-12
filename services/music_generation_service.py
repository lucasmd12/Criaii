# Arquivo: src/services/music_generation_service.py (VERSÃO HÍBRIDA - Etapa 6)
# Função: O Chef de Cozinha - Orquestra a criação de músicas, se comunica com a IA e
# publica os resultados no sistema de comandas.

import asyncio
import os
import io
import time
from typing import Optional
import soundfile as sf
from gradio_client import Client, Job

# Importamos as CLASSES dos serviços que ele vai usar
from services.cloudinary_service import CloudinaryService
from services.sync_service import SyncService
from services.notification_service import NotificationService
from models.mongo_models import MongoMusic
from database.database import db_manager # Usaremos o db_manager para obter a conexão

class MusicGenerationService:
    """
    Serviço de orquestração para geração de música.
    Agora desacoplado, ele apenas publica eventos no SyncService e persiste o histórico.
    """
    def __init__(self):
        self.client: Optional[Client] = None
        self.space_url = os.getenv("HF_SPACE_URL", "https://lucasidcloned-cantai-api.hf.space")
        
        # O Chef agora tem acesso direto às suas ferramentas essenciais.
        self.sync_service: Optional[SyncService] = None
        self.notification_service: Optional[NotificationService] = None
        self.cloudinary_service: Optional[CloudinaryService] = None
        print("👨‍🍳 Chef de Cozinha (MusicGenerationService) pronto para receber pedidos.")

    def set_dependencies(self, sync_service: SyncService, notification_service: NotificationService, cloudinary_service: CloudinaryService):
        """Permite que o main.py injete as dependências necessárias no startup."""
        self.sync_service = sync_service
        self.notification_service = notification_service
        self.cloudinary_service = cloudinary_service
        print("✔️  Chef de Cozinha recebeu acesso ao Sistema de Comandas, ao Arquivista e à Despensa de Nuvem.")

    def _connect_to_space(self):
        """Conecta-se à Cozinha de IA (Hugging Face) de forma preguiçosa (lazy)."""
        if not self.client:
            print(f"🔌  Chef está conectando os equipamentos à Cozinha de IA em: {self.space_url}")
            if not self.space_url:
                raise Exception("URL da Cozinha de IA (HF_SPACE_URL) não configurada.")
            try:
                self.client = Client(self.space_url)
                print(f"✅  Equipamentos conectados com sucesso.")
            except Exception as e:
                print(f"❌ ERRO CRÍTICO: O Chef não conseguiu conectar os equipamentos à Cozinha de IA. Erro: {e}")
                raise Exception("A Cozinha de IA parece estar fechada. Por favor, tente novamente em alguns minutos.")
        return self.client

    async def _publish_progress(self, user_id: str, music_id: str, progress: int, message: str):
        """
        Função central para publicar progresso no sistema de comandas e salvar o histórico.
        """
        # 1. Publica o evento para o frontend em tempo real
        if self.sync_service:
            payload = {"music_id": music_id, "status": "in_progress", "progress": progress, "message": message}
            await self.sync_service.publish_event("music_progress", user_id, payload)
        
        # 2. Pede ao Arquivista para salvar um registro do passo
        if self.notification_service:
            await self.notification_service.save_process_history(user_id, music_id, "generation", "in_progress", message)

    async def generate_music(self, music_id: str, user_id: str, prompt: str, audio_file_path: Optional[str] = None):
        """
        O processo completo de cozinhar uma música, desde o pedido até a entrega no balcão.
        """
        print(f"🔥 Novo pedido recebido na cozinha! ID do Prato: {music_id}")
        db = await db_manager.get_database()

        try:
            # 1. Conectar à Cozinha de IA
            await self._publish_progress(user_id, music_id, 10, "🔌 Conectando com a cozinha IA...")
            self._connect_to_space()

            # 2. Enviar o pedido para a IA
            await self._publish_progress(user_id, music_id, 20, "📝 Enviando pedido para o chef IA...")
            job: Job = self.client.submit(prompt, audio_file_path, api_name="/generate_music_with_progress")
            
            # 3. Acompanhar o cozimento em tempo real
            final_result = None
            for i, update in enumerate(job):
                if isinstance(update, str):
                    progress_val = 30 + (i * 5)
                    await self._publish_progress(user_id, music_id, min(85, progress_val), update)
                elif isinstance(update, tuple):
                    final_result = update
                    break
            
            if not final_result:
                raise Exception("A Cozinha de IA não retornou um prato finalizado.")

            sampling_rate, audio_data = final_result
            print(f"🍽️  Prato (música) saiu do forno da IA. ID: {music_id}")

            # 4. Fazer o upload para a nuvem (Cloudinary)
            await self._publish_progress(user_id, music_id, 90, "☁️  Levando o prato para a vitrine da nuvem...")
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, sampling_rate, format='wav')
            buffer.seek(0)
            music_url = await self.cloudinary_service.upload_audio(buffer.getvalue(), music_id)
            if not music_url:
                raise Exception("Falha ao colocar o prato na vitrine (upload para Cloudinary).")

            # 5. Atualizar o banco de dados
            await MongoMusic.update_status(db, music_id, "completed", music_url)
            print(f"✅  Prato {music_id} registrado no cardápio (MongoDB).")

            # 6. Publicar a comanda de "prato pronto"
            if self.sync_service:
                await self.sync_service.publish_event("music_completed", user_id, {"music_id": music_id, "url": music_url})
            
            # 7. Pedir ao Arquivista para criar a notificação final
            if self.notification_service:
                await self.notification_service.create_notification(
                    user_id=user_id,
                    title="🎵 Música Pronta!",
                    message=f"Sua música baseada no prompt '{prompt[:30]}...' está pronta.",
                    notification_type="success",
                    metadata={'music_id': music_id, 'music_url': music_url}
                )

        except Exception as e:
            error_message = str(e)
            print(f"🔥❌ ALERTA DE INCÊNDIO NA COZINHA! Falha ao gerar prato {music_id}. Erro: {error_message}")
            await MongoMusic.update_status(db, music_id, "failed")
            if self.sync_service:
                await self.sync_service.publish_event("music_failed", user_id, {"music_id": music_id, "error": error_message})
            if self.notification_service:
                await self.notification_service.create_notification(
                    user_id=user_id,
                    title="❌ Erro na Geração",
                    message=f"Ocorreu um erro ao gerar sua música: {error_message}",
                    notification_type="error"
                )
        finally:
            if audio_file_path and os.path.exists(audio_file_path):
                try:
                    os.remove(audio_file_path)
                    print(f"🧹  Bancada da cozinha limpa (arquivo temporário removido).")
                except OSError as e:
                    print(f"⚠️  Erro ao limpar a bancada: {e}")

# Instância global do serviço (mantemos seu padrão)
music_generation_service = MusicGenerationService()
