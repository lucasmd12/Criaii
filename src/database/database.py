# src/database.py (O Gerente do Cofre)

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Carrega as variáveis de ambiente para garantir que a chave do cofre (URI) esteja disponível
load_dotenv()

class DatabaseConnection:
    """
    O Gerente do Cofre. Responsável por guardar a chave (conexão),
    abrir e fechar o cofre (banco de dados) e supervisionar todas as
    operações de acesso aos registros.
    """
    _client: Optional[AsyncIOMotorClient] = None
    db = None

    async def connect(self):
        """O Gerente chega para trabalhar e abre o cofre."""
        if self._client:
            print("🔑 Gerente do Cofre: O cofre já está aberto e operacional.")
            return

        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("🚨 GERENTE DO COFRE: A CHAVE MESTRA (MONGO_URI) NÃO FOI ENCONTRADA! OPERAÇÃO IMPOSSÍVEL.")
            raise ValueError("MONGO_URI não encontrada no ambiente.")
        
        print("🔑 Gerente do Cofre: Pegando a chave mestra para abrir o cofre (MongoDB)...")
        try:
            self._client = AsyncIOMotorClient(mongo_uri)
            # Forçar uma conexão para verificar se a chave funciona
            await self._client.admin.command('ping')
            self.db = self._client.get_database("alquimista_musical_db")
            print("✅ Gerente do Cofre: Cofre aberto e pronto para as operações do dia!")
        except Exception as e:
            print(f"🚨 GERENTE DO COFRE: A CHAVE MESTRA FALHOU! Não foi possível abrir o cofre. Erro: {e}")
            self._client = None
            self.db = None
            raise e # Levanta o erro para parar a aplicação, pois ela não pode funcionar sem DB

    async def disconnect(self):
        """O Gerente fecha o cofre no final do expediente."""
        if self._client:
            self._client.close()
            self._client = None
            self.db = None
            print("🔒 Gerente do Cofre: Cofre trancado com segurança. Fim do expediente.")

    # =================================================================
    # MÉTODOS DE SUPERVISÃO (LOGS DE ACESSO AO BANCO DE DADOS)
    # =================================================================

    async def find_documents(self, collection_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Supervisiona a busca por registros em uma coleção (gaveta do arquivo)."""
        print(f"🧐 Gerente do Cofre: Supervisionando busca na gaveta '{collection_name}' com a consulta: {query}")
        if not self.db:
            print(f"🚫 Gerente do Cofre: Acesso negado! O cofre está fechado.")
            return []
        collection = self.db[collection_name]
        cursor = collection.find(query)
        documents = await cursor.to_list(length=None)
        print(f"📄 Gerente do Cofre: {len(documents)} registro(s) encontrado(s) na gaveta '{collection_name}'.")
        return documents

    async def insert_document(self, collection_name: str, document: Dict[str, Any]) -> Any:
        """Supervisiona a inserção de um novo registro em uma coleção."""
        print(f"✍️ Gerente do Cofre: Supervisionando a adição de um novo registro na gaveta '{collection_name}'.")
        if not self.db:
            print(f"🚫 Gerente do Cofre: Acesso negado! O cofre está fechado.")
            return None
        collection = self.db[collection_name]
        result = await collection.insert_one(document)
        print(f"✅ Gerente do Cofre: Novo registro com ID '{result.inserted_id}' arquivado com sucesso.")
        return result.inserted_id

# =================================================================
# --- PONTO DE ACESSO ÚNICO AO GERENTE ---
# Em vez de criar a instância aqui, criamos uma instância global que será
# gerenciada pelo ciclo de vida da aplicação.
# Isso evita a importação circular e garante que o gerente só trabalhe
# quando o restaurante estiver aberto.
# =================================================================
db_manager = DatabaseConnection()

# --- FUNÇÃO DE DEPENDÊNCIA ---
# Esta é a forma como os "garçons" e "chefs" devem pedir acesso ao cofre.
# O FastAPI vai garantir que o gerente esteja pronto antes de entregar o acesso.
async def get_database() -> DatabaseConnection:
    """Função para os outros serviços 'pedirem' acesso ao Gerente do Cofre."""
    if not db_manager.db:
        # Isso garante que, mesmo que algo falhe no startup, ele tente reconectar.
        await db_manager.connect()
    return db_manager
