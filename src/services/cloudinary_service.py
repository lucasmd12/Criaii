import os
import cloudinary
import cloudinary.uploader
from io import BytesIO

class CloudinaryService:
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Inicializa o Cloudinary"""
        if cls._initialized:
            return
            
        try:
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
                api_key=os.getenv('CLOUDINARY_API_KEY'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            )
            
            if not all([os.getenv('CLOUDINARY_CLOUD_NAME'), os.getenv('CLOUDINARY_API_KEY'), os.getenv('CLOUDINARY_API_SECRET')]):
                print("⚠️  Credenciais do Cloudinary não configuradas. Upload de áudio desabilitado.")
                return
                
            cls._initialized = True
            print("✅ Cloudinary inicializado com sucesso.")
            
        except Exception as error:
            print(f"❌ Erro ao inicializar Cloudinary: {error}")
    
    @classmethod
    def upload_audio(cls, audio_buffer, file_name):
        """Faz upload de um buffer de áudio para o Cloudinary"""
        if not cls._initialized:
            print("Cloudinary não inicializado. Retornando URL de exemplo.")
            return "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
            
        try:
            # Converte buffer para BytesIO se necessário
            if isinstance(audio_buffer, bytes):
                audio_stream = BytesIO(audio_buffer)
            else:
                audio_stream = audio_buffer
                
            # Upload para o Cloudinary
            result = cloudinary.uploader.upload(
                audio_stream,
                resource_type="video",  # Cloudinary trata áudio como vídeo
                public_id=f"alquimista/{file_name}",
                format="mp3",
                overwrite=True
            )
            
            print(f"✅ Áudio enviado para Cloudinary: {result['secure_url']}")
            return result['secure_url']
            
        except Exception as error:
            print(f"❌ Erro ao fazer upload do áudio: {error}")
            # Retorna URL de exemplo em caso de erro
            return "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

