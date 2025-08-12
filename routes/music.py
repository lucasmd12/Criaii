# src/routes/music.py (O Garçom Anotando o Pedido)

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Form, UploadFile, File
from typing import Optional, Literal

# --- CORREÇÃO DE IMPORTAÇÃO ---
from services.music_generation_service import MusicGenerationService
from .user import get_current_user_id
# ================== INÍCIO DA CORREÇÃO ==================
# O Garçom precisa saber como pedir acesso ao Gerente do Cofre para entregar à Cozinha.
from database.database import get_database, DatabaseConnection
# =================== FIM DA CORREÇÃO ====================
# ADICIONADO: Importamos o CacheService para que o Garçom possa falar com o Buffet
from services.cache_service import CacheService

# --- Router do FastAPI ---
music_router = APIRouter()

# Instancia o serviço de geração de música (a conexão direta com a Cozinha)
music_generator = MusicGenerationService()

@music_router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_music(
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    # ================== INÍCIO DA CORREÇÃO ==================
    # O Garçom agora também pega a "chave do cofre" (db_manager) para a Cozinha usar mais tarde.
    db_manager: DatabaseConnection = Depends(get_database),
    # =================== FIM DA CORREÇÃO ====================
    # ADICIONADO: O Garçom agora tem uma linha direta com o Gerente do Buffet
    cache_service: CacheService = Depends(),
    
    # Campos obrigatórios
    description: str = Form(..., description="Descrição/prompt da música (essência)"),
    musicName: str = Form(..., description="Nome da música"),
    voiceType: Literal["instrumental", "male", "female", "both"] = Form(..., description="Tipo de voz"),
    
    # Campos opcionais
    lyrics: Optional[str] = Form(None, description="Letra da música"),
    genre: Optional[str] = Form(None, description="Gênero musical"),
    rhythm: Optional[Literal["slow", "fast", "mixed"]] = Form(None, description="Ritmo musical"),
    instruments: Optional[str] = Form(None, description="Instrumentos específicos"),
    studio_type: Optional[Literal["studio", "live"]] = Form("studio", description="Ambiente de gravação"),
    
    # Arquivo de voz opcional
    voiceSample: Optional[UploadFile] = File(None, description="Arquivo de áudio da voz (até 5 min)")
):
    """
    🎵 O Garçom anota o pedido do cliente para enviar à Cozinha.
    
    Recebe todos os parâmetros do "cardápio" e envia o pedido para a "cozinha" (Hugging Face).
    Retorna imediatamente e processa em background com feedback em tempo real via WebSocket.
    """
    print(f"\n👨‍🍳 Garçom: Anotando um novo pedido do cliente {current_user_id} para a música \'{musicName}\'.")
    
    try:
        # ... (toda a sua lógica de validação permanece exatamente a mesma) ...
        if not description.strip():
            print(f"⚠️ Garçom: Pedido inválido do cliente {current_user_id}. Faltou a descrição.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A descrição da música é obrigatória para fazer o pedido."
            )
        
        if not musicName.strip():
            print(f"⚠️ Garçom: Pedido inválido do cliente {current_user_id}. Faltou o nome da música.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O nome da música é obrigatório para fazer o pedido."
            )
        
        if voiceSample:
            print(f"🎤 Garçom: Cliente forneceu um ingrediente especial (amostra de voz: {voiceSample.filename}). Verificando a qualidade...")
            if voiceSample.size > 50 * 1024 * 1024: # 50MB
                print(f"🚫 Garçom: Ingrediente especial do cliente {current_user_id} é muito pesado ({voiceSample.size} bytes).")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ingrediente especial (voz) muito pesado! Máximo 50MB (aproximadamente 5 minutos)."
                )
            
            allowed_types = ["audio/mp3", "audio/mpeg", "audio/wav", "audio/wave", "audio/m4a", "audio/mp4", "audio/ogg", "audio/flac"]
            if voiceSample.content_type not in allowed_types:
                print(f"🚫 Garçom: Ingrediente especial do cliente {current_user_id} tem um formato não aceito ({voiceSample.content_type}).")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este tipo de ingrediente especial (formato de áudio) não é aceito pela nossa cozinha. Use MP3, WAV, M4A, OGG ou FLAC."
                )
        
        music_data = {
            "description": description.strip(),
            "musicName": musicName.strip(),
            "voiceType": voiceType,
            "lyrics": lyrics.strip() if lyrics else None,
            "genre": genre,
            "rhythm": rhythm,
            "instruments": instruments.strip() if instruments else None,
            "studioType": studio_type,
            "userId": current_user_id
        }
        
        print(f"✅ Garçom: Comanda para \'{musicName}\' pronta! Enviando para a Cozinha em segundo plano.")
        
        # ================== INÍCIO DA CORREÇÃO ==================
        # O Garçom agora entrega a chave do cofre (db_manager) junto com o pedido.
        background_tasks.add_task(
            music_generator.generate_music_async,
            db_manager=db_manager, # <--- MUDANÇA IMPORTANTE
            music_data=music_data,
            voice_file=voiceSample,
            user_id=current_user_id
        )
        # =================== FIM DA CORREÇÃO ====================

        # ADICIONADO: O Garçom avisa o Buffet para limpar o cardápio antigo do cliente.
        await cache_service.invalidate_user_music_list(current_user_id)
        print(f"🧹 Garçom avisou o Buffet: 'O cardápio do cliente {current_user_id} mudou, jogue fora a versão antiga!'")
        
        print(f"👍 Garçom: Pedido da música \'{musicName}\' foi entregue na Cozinha. Informando o cliente.")
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado em nosso sistema. Por favor, tente fazer seu pedido novamente."
        )
