#!/usr/bin/env python3
"""
Wrapper Flask para compatibilidade com deploy.
Redireciona para a aplicação FastAPI principal.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Importa a aplicação principal
from src.main import application

# Para compatibilidade com Flask deploy
app = application

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )

