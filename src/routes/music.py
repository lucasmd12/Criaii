from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Form, UploadFile, File
from typing import Optional, Literal

# --- CORREÇÃO DE IMPORTAÇÃO ---
# Adicionando importações relativas para consistência com as outras correções.
from ..services.music_generation_service import MusicGenerationService
from .user import get_current_user_id

# --- Router do FastAPI ---
music_router = APIRouter()

# Instancia o serviço de geração de música uma vez
music_generator = MusicGenerationService()

@music_router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_music(
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    
    # Campos obrigatórios
    description: str = Form(..., description="Descrição/prompt da música (essência)"),
    musicName: str = Form(..., description="Nome da música"),
    voiceType: Literal["instrumental", "male", "female", "both"] = Form(..., description="Tipo de voz"),
    
    # Campos opcionais
    lyrics: Optional[str] = Form(None, description="Letra da música"),
    genre: Optional[str] = Form(None, description="Gênero musical"),
    rhythm: Optional[Literal["slow", "fast", "mixed"]] = Form(None, description="Ritmo musical"),
    instruments: Optional[str] = Form(None, description="Instrumentos específicos"),
    
    # =================================================================
    # CORREÇÃO PRINCIPAL APLICADA AQUI (SyntaxError)
    # Removido o texto duplicado e o erro de sintaxe.
    # =================================================================
    studio_type: Optional[Literal["studio", "live"]] = Form("studio", description="Ambiente de gravação"),
    
    # Arquivo de voz opcional
    voiceSample: Optional[UploadFile] = File(None, description="Arquivo de áudio da voz (até 5 min)")
):
    """
    🎵 Endpoint principal para gerar música no estúdio virtual.
    
    Recebe todos os parâmetros do "cardápio" e envia o pedido para a "cozinha" (Hugging Face).
    Retorna imediatamente e processa em background com feedback em tempo real via WebSocket.
    """
    
    try:
        # Validações básicas
        if not description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A descrição da música é obrigatória"
            )
        
        if not musicName.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O nome da música é obrigatório"
            )
        
        # Validação do arquivo de voz
        if voiceSample:
            if voiceSample.size > 50 * 1024 * 1024: # 50MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Arquivo de voz muito grande. Máximo 50MB (aproximadamente 5 minutos)."
                )
            
            allowed_types = ["audio/mp3", "audio/mpeg", "audio/wav", "audio/wave", "audio/m4a", "audio/mp4", "audio/ogg", "audio/flac"]
            if voiceSample.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de áudio não suportado. Use MP3, WAV, M4A, OGG ou FLAC."
                )
        
        # Prepara os dados para o serviço
        music_data = {
            "description": description.strip(),
            "musicName": musicName.strip(),
            "voiceType": voiceType,
            "lyrics": lyrics.strip() if lyrics else None,
            "genre": genre,
            "rhythm": rhythm,
            "instruments": instruments.strip() if instruments else None,
            "studioType": studio_type, # Corrigido para usar o nome correto da variável
            "userId": current_user_id
        }
        
        # Adiciona a tarefa de geração ao background
        background_tasks.add_task(
            music_generator.generate_music_async,
            music_data=music_data,
            voice_file=voiceSample,
            user_id=current_user_id
        )
        
        return {
            "message": "🍳 Pedido enviado para a cozinha! Acompanhe o progresso em tempo real.",
            "status": "processing",
            "musicName": musicName,
            "userId": current_user_id,
            "note": "Conecte-se ao WebSocket para receber atualizações em tempo real do processo."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro inesperado na geração de música: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

