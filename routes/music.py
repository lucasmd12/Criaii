# src/routes/music.py (O Garçom Anotando o Pedido - VERSÃO COM DEPENDENCY INJECTION)

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Form, UploadFile, File
from typing import Optional, Literal

# --- CORREÇÃO CRÍTICA: Usar dependency injection em vez de importações diretas ---
from .user import get_current_user_id
from dependencies import get_db_manager, get_cache_service, get_music_generation_service

# --- Importações de CLASSE para Type Hinting ---
from services.music_generation_service import MusicGenerationService
from services.cache_service import CacheService
from database.database import DatabaseConnection

# --- Router do FastAPI ---
music_router = APIRouter()

@music_router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_music(
    # Dependências de infraestrutura
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    db_manager: DatabaseConnection = Depends(get_db_manager),
    cache_service: CacheService = Depends(get_cache_service),
    music_generator: MusicGenerationService = Depends(get_music_generation_service),
    
    # Campos do formulário
    description: str = Form(..., description="Descrição/prompt da música (essência)"),
    musicName: str = Form(..., description="Nome da música"),
    voiceType: Literal["instrumental", "male", "female", "both"] = Form(..., description="Tipo de voz"),
    lyrics: Optional[str] = Form(None, description="Letra da música"),
    genre: Optional[str] = Form(None, description="Gênero musical"),
    rhythm: Optional[Literal["slow", "fast", "mixed"]] = Form(None, description="Ritmo musical"),
    instruments: Optional[str] = Form(None, description="Instrumentos específicos"),
    studio_type: Optional[Literal["studio", "live"]] = Form("studio", description="Ambiente de gravação"),
    voiceSample: Optional[UploadFile] = File(None, description="Arquivo de áudio da voz (até 5 min)")
):
    """
    🎵 O Garçom anota o pedido do cliente para enviar à Cozinha.
    """
    print(f"\n👨‍🍳 Garçom: Anotando um novo pedido do cliente {current_user_id} para a música '{musicName}'.")
    
    try:
        # Validação dos dados (sua lógica original mantida)
        if not description.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A descrição da música é obrigatória.")
        if not musicName.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O nome da música é obrigatório.")
        
        if voiceSample:
            print(f"🎤 Garçom: Cliente forneceu um ingrediente especial (amostra de voz: {voiceSample.filename}). Verificando a qualidade...")
            if voiceSample.size > 50 * 1024 * 1024:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo de voz muito pesado! Máximo 50MB.")
            allowed_types = ["audio/mp3", "audio/mpeg", "audio/wav", "audio/wave", "audio/m4a", "audio/mp4", "audio/ogg", "audio/flac"]
            if voiceSample.content_type not in allowed_types:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de áudio não suportado.")
        
        music_data = {
            "description": description.strip(), "musicName": musicName.strip(), "voiceType": voiceType,
            "lyrics": lyrics.strip() if lyrics else None, "genre": genre, "rhythm": rhythm,
            "instruments": instruments.strip() if instruments else None, "studioType": studio_type,
            "userId": current_user_id
        }
        
        print(f"✅ Garçom: Comanda para '{musicName}' pronta! Enviando para a Cozinha em segundo plano.")
        
        # O Garçom agora usa o 'music_generator' que o Maître (FastAPI) lhe entregou.
        background_tasks.add_task(
            music_generator.generate_music,
            db_manager=db_manager,
            music_data=music_data,
            voice_file=voiceSample,
            user_id=current_user_id
        )

        # O Garçom avisa o Buffet para limpar o cardápio antigo do cliente.
        await cache_service.invalidate_user_music_list(current_user_id)
        print(f"🧹 Garçom avisou o Buffet: 'O cardápio do cliente {current_user_id} mudou, jogue fora a versão antiga!'")
        
        print(f"👍 Garçom: Pedido da música '{musicName}' foi entregue na Cozinha. Informando o cliente.")
        
        return {
            "message": "Seu pedido foi anotado e enviado para nossa cozinha de IA! Acompanhe o progresso pelo painel de avisos.",
            "status": "processing",
            "musicName": musicName,
            "userId": current_user_id,
            "note": "Conecte-se ao WebSocket para receber atualizações em tempo real do processo."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🚨 Garçom: Houve um grande problema ao tentar anotar o pedido: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ocorreu um erro inesperado em nosso sistema.")

# Adicione aqui outras rotas relacionadas a música, como deletar, se necessário,
# lembrando de injetar as dependências da mesma forma.
