import time
import base64
import asyncio
import uuid
from io import BytesIO

import numpy as np
import soundfile as sf
from gradio_client import Client

from ..services.firebase_service import FirebaseService
from ..services.cloudinary_service import CloudinaryService
from ..routes.music_list import add_generated_music


class MusicGenerationService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicGenerationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.client = None
        self.space_url = "https://lucasidcloned-cantai-api.hf.space"
        self.websocket_service = None
        self.notification_service = None
        
        # Importa os serviços aqui para evitar import circular
        try:
            from ..services.websocket_service import websocket_service
            self.websocket_service = websocket_service
        except ImportError:
            print("⚠️ WebSocket service não disponível")
            
        try:
            from ..services.notification_service import notification_service
            self.notification_service = notification_service
        except ImportError:
            print("⚠️ Notification service não disponível")

    async def _emit_progress(self, user_id: str, progress: int, message: str, step: str = "", estimated_time: int = None, process_id: str = None):
        """
        Emite progresso via WebSocket se disponível.
        """
        if self.websocket_service:
            try:
                await self.websocket_service.emit_progress(
                    user_id=user_id,
                    step=step,
                    progress=progress,
                    message=message,
                    estimated_time=estimated_time
                )
                
                # Salva no histórico se disponível
                if self.notification_service and process_id:
                    await self.notification_service.save_process_history(
                        user_id=user_id,
                        process_id=process_id,
                        step=step,
                        status='in_progress',
                        message=message
                    )
                    
            except Exception as e:
                print(f"⚠️ Erro ao emitir progresso via WebSocket: {e}")

    async def _emit_completion(self, user_id: str, music_name: str, music_url: str, process_id: str = None):
        """
        Emite conclusão via WebSocket se disponível.
        """
        if self.websocket_service:
            try:
                await self.websocket_service.emit_completion(
                    user_id=user_id,
                    music_name=music_name,
                    music_url=music_url
                )
                
                # Salva no histórico se disponível
                if self.notification_service and process_id:
                    await self.notification_service.save_process_history(
                        user_id=user_id,
                        process_id=process_id,
                        step='completed',
                        status='success',
                        message=f"Música '{music_name}' criada com sucesso"
                    )
                    
                    # Cria notificação
                    await self.notification_service.create_notification(
                        user_id=user_id,
                        title="🎵 Música Pronta!",
                        message=f"Sua música '{music_name}' foi criada com sucesso e está pronta para download.",
                        notification_type="success",
                        metadata={'music_url': music_url, 'music_name': music_name}
                    )
                    
            except Exception as e:
                print(f"⚠️ Erro ao emitir conclusão via WebSocket: {e}")

    async def _emit_error(self, user_id: str, error_message: str, process_id: str = None):
        """
        Emite erro via WebSocket se disponível.
        """
        if self.websocket_service:
            try:
                await self.websocket_service.emit_error(
                    user_id=user_id,
                    error_message=error_message
                )
                
                # Salva no histórico se disponível
                if self.notification_service and process_id:
                    await self.notification_service.save_process_history(
                        user_id=user_id,
                        process_id=process_id,
                        step='error',
                        status='failed',
                        message=error_message
                    )
                    
                    # Cria notificação de erro
                    await self.notification_service.create_notification(
                        user_id=user_id,
                        title="❌ Erro na Geração",
                        message=f"Ocorreu um erro ao gerar sua música: {error_message}",
                        notification_type="error",
                        metadata={'error': error_message}
                    )
                    
            except Exception as e:
                print(f"⚠️ Erro ao emitir erro via WebSocket: {e}")

    def _connect_to_space(self):
        """
        Conecta ao espaço do Hugging Face.
        """
        try:
            if not self.client:
                self.client = Client(self.space_url)
                print(f"🔌 Conectado ao espaço: {self.space_url}")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar ao espaço: {e}")
            return False

    async def generate_music_async(self, music_data: dict, voice_file=None, user_id: str = None):
        """
        Método assíncrono para gerar música (usado pelo BackgroundTasks).
        """
        try:
            # Processa arquivo de voz se fornecido
            voice_sample_path = None
            if voice_file:
                # Salva temporariamente o arquivo de voz
                voice_sample_path = f"/tmp/voice_{user_id}_{int(time.time())}.wav"
                with open(voice_sample_path, "wb") as f:
                    content = await voice_file.read()
                    f.write(content)
            
            # Chama o método principal de geração
            result = await self.generate_music(
                user_id=user_id or music_data.get("userId"),
                description=music_data.get("description"),
                music_name=music_data.get("musicName"),
                voice_type=music_data.get("voiceType", "instrumental"),
                lyrics=music_data.get("lyrics", ""),
                genre=music_data.get("genre", ""),
                rhythm=music_data.get("rhythm", ""),
                instruments=music_data.get("instruments", ""),
                studio_type=music_data.get("studioType", "studio"),
                voice_sample_path=voice_sample_path
            )
            
            # Remove arquivo temporário se existir
            if voice_sample_path:
                try:
                    import os
                    os.remove(voice_sample_path)
                except:
                    pass
            
            return result
            
        except Exception as e:
            print(f"❌ Erro no generate_music_async: {e}")
            await self._emit_error(user_id or music_data.get("userId"), str(e))
            return {"success": False, "error": str(e)}

    async def generate_music(self, user_id: str, description: str, music_name: str, 
                           voice_type: str = "instrumental", lyrics: str = "", 
                           genre: str = "", rhythm: str = "", instruments: str = "", 
                           studio_type: str = "studio", voice_sample_path: str = None):
        """
        Gera música usando o espaço do Hugging Face com feedback em tempo real.
        """
        process_id = f"music_{user_id}_{int(time.time())}"
        
        try:
            # Inicia o rastreamento do processo
            if self.notification_service:
                self.notification_service.start_process_tracking(user_id, process_id, "music_generation")
            
            # Etapa 1: Pedido recebido
            await self._emit_progress(user_id, 5, "📋 Pedido recebido na cozinha", "received", 180, process_id)
            await asyncio.sleep(1)
            
            # Etapa 2: Conectando com a cozinha
            await self._emit_progress(user_id, 10, "🔌 Conectando com a cozinha IA", "connecting", 170, process_id)
            if not self._connect_to_space():
                raise Exception("Falha ao conectar com a cozinha IA")
            await asyncio.sleep(2)
            
            # Etapa 3: Enviando pedido
            await self._emit_progress(user_id, 20, "📝 Enviando pedido para o chef", "sending_order", 150, process_id)
            await asyncio.sleep(1)
            
            # Etapa 4: Chef analisando
            await self._emit_progress(user_id, 30, "👨‍🍳 Chef IA analisando seu pedido", "preparing", 130, process_id)
            await asyncio.sleep(2)
            
            # Etapa 5: Processando voz (se necessário)
            if voice_sample_path and voice_type != "instrumental":
                await self._emit_progress(user_id, 40, "🎤 Processando sua amostra de voz", "processing_voice", 120, process_id)
                await asyncio.sleep(3)
            
            # Etapa 6: No forno da IA
            await self._emit_progress(user_id, 50, "🔥 Música no forno da IA", "cooking", 90, process_id)
            
            # Preparar prompt completo
            full_prompt = self._build_prompt(description, voice_type, lyrics, genre, rhythm, instruments, studio_type)
            
            # Chamar a API do Hugging Face
            await self._emit_progress(user_id, 70, "⏳ Aguardando resultado da cozinha", "waiting_result", 60, process_id)
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._call_huggingface_api, 
                full_prompt, 
                voice_sample_path
            )
            
            if not result:
                raise Exception("Falha na geração da música")
            
            # Etapa 7: Finalizando
            await self._emit_progress(user_id, 85, "🎵 Finalizando detalhes da música", "finalizing", 30, process_id)
            await asyncio.sleep(2)
            
            # Etapa 8: Upload
            await self._emit_progress(user_id, 95, "☁️ Garçom levando à sua mesa", "uploading", 15, process_id)
            
            # Upload para Cloudinary
            cloudinary_service = CloudinaryService()
            music_url = cloudinary_service.upload_audio(result, f"{music_name}_{user_id}")
            
            if not music_url:
                raise Exception("Falha no upload da música")
            
            # Etapa 9: Salvando
            await self._emit_progress(user_id, 98, "💾 Registrando no cardápio", "saving", 5, process_id)
            
            # Salvar no banco de dados
            add_generated_music({
                "userId": user_id,
                "musicName": music_name,
                "description": description,
                "musicUrl": music_url,
                "voiceType": voice_type,
                "genre": genre,
                "lyrics": lyrics
            })
            
            # Etapa 10: Concluído
            await self._emit_completion(user_id, music_name, music_url, process_id)
            
            # Finaliza o processo
            if self.notification_service:
                self.notification_service.complete_process(process_id, True, f"Música '{music_name}' criada com sucesso")
            
            return {
                "success": True,
                "music_url": music_url,
                "music_name": music_name,
                "message": f"Música '{music_name}' gerada com sucesso!"
            }
            
        except Exception as e:
            error_message = str(e)
            print(f"❌ Erro inesperado: {error_message}")
            
            # Emite erro via WebSocket
            await self._emit_error(user_id, error_message, process_id)
            
            # Finaliza o processo com erro
            if self.notification_service:
                self.notification_service.complete_process(process_id, False, error_message)
            
            return {
                "success": False,
                "error": error_message,
                "message": "Erro ao gerar música. Tente novamente."
            }

    def _build_prompt(self, description: str, voice_type: str, lyrics: str = "", 
                     genre: str = "", rhythm: str = "", instruments: str = "", 
                     studio_type: str = "studio") -> str:
        """
        Constrói o prompt completo para a geração de música.
        """
        prompt_parts = [description]
        
        if genre:
            prompt_parts.append(f"Gênero: {genre}")
        
        if rhythm:
            rhythm_map = {"slow": "lento", "fast": "rápido", "mixed": "ritmo variado"}
            prompt_parts.append(f"Ritmo: {rhythm_map.get(rhythm, rhythm)}")
        
        if instruments:
            prompt_parts.append(f"Instrumentos: {instruments}")
        
        if studio_type == "live":
            prompt_parts.append("Ambiente: gravação ao vivo")
        else:
            prompt_parts.append("Ambiente: estúdio profissional")
        
        if voice_type != "instrumental":
            voice_map = {
                "male": "voz masculina",
                "female": "voz feminina", 
                "both": "dueto (vozes masculina e feminina)"
            }
            prompt_parts.append(f"Tipo de voz: {voice_map.get(voice_type, voice_type)}")
        
        return ". ".join(prompt_parts)

    def _call_huggingface_api(self, prompt: str, voice_sample_path: str = None):
        """
        Chama a API do Hugging Face para gerar música.
        """
        try:
            if voice_sample_path:
                # Com amostra de voz
                result = self.client.predict(
                    prompt,
                    voice_sample_path,
                    api_name="/generate_music_with_voice"
                )
            else:
                # Sem amostra de voz
                result = self.client.predict(
                    prompt,
                    api_name="/generate_music"
                )
            
            return result
            
        except Exception as e:
            print(f"❌ Erro na API do Hugging Face: {e}")
            return None

# Instância global do serviço
music_generation_service = MusicGenerationService()

