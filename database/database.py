# src/database/database.py (O Gerente do Cofre, agora mais organizado)

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
            await self._client.admin.command('ping')
            self.db = self._client.get_database("alquimista_musical_db")
            print("✅ Gerente do Cofre: Cofre aberto e pronto para as operações do dia!")

            # ADICIONADO: O Gerente agora organiza os arquivos para acesso rápido.
            await self._create_indexes()

        except Exception as e:
            print(f"🚨 GERENTE DO COFRE: A CHAVE MESTRA FALHOU! Não foi possível abrir o cofre. Erro: {e}")
            self._client = None
            self.db = None
            raise e

    async def disconnect(self):
        """O Gerente fecha o cofre no final do expediente."""
        if self._client:
            self._client.close()
            self._client = None
            self.db = None
            print("🔒 Gerente do Cofre: Cofre trancado com segurança. Fim do expediente.")

    # ADICIONADO: Nova função interna para o Gerente organizar os arquivos.
    async def _create_indexes(self):
        """
        O Gerente do Cofre organiza as gavetas (coleções) com etiquetas (índices)
        para encontrar os registros mais rapidamente no futuro.
        """
        print("🗂️  Gerente do Cofre: Organizando os arquivos para acesso rápido...")
        try:
            # Etiqueta na gaveta de clientes para encontrar pelo nome de usuário rapidamente
            # e garantir que não haja dois clientes com o mesmo nome.
            await self.db["users"].create_index("username", unique=True)
            print("  - Etiqueta de 'Nome de Usuário' adicionada à gaveta de clientes.")

            # Etiqueta na gaveta de músicas para encontrar todas as músicas de um cliente,
            # já ordenadas da mais nova para a mais antiga.
            await self.db["musics"].create_index([("userId", 1), ("timestamp", -1)])
            print("  - Etiqueta de 'Músicas por Cliente' adicionada à gaveta de músicas.")

            # Etiqueta na gaveta de notificações para encontrar os avisos de um cliente.
            await self.db["notifications"].create_index([("user_id", 1), ("read", 1), ("created_at", -1)])
            print("  - Etiqueta de 'Avisos por Cliente' adicionada à gaveta de notificações.")

            print("✅ Gerente do Cofre: Arquivos organizados com sucesso!")
        except Exception as e:
            print(f"🚨 GERENTE DO COFRE: Houve um problema ao tentar organizar os arquivos (criar índices): {e}")
            # Não levantamos um erro aqui, pois a aplicação ainda pode funcionar, embora mais lentamente.

    # =================================================================
    # SEUS MÉTODOS DE SUPERVISÃO (permanecem idênticos)
    # =================================================================

    async def find_documents(self, collection_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Supervisiona a busca por registros em uma coleção (gaveta do arquivo)."""
        print(f"🧐 Gerente do Cofre: Supervisionando busca na gaveta '{collection_name}' com a consulta: {query}")
        if self.db is None:
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
        if self.db is None:
            print(f"🚫 Gerente do Cofre: Acesso negado! O cofre está fechado.")
            return None
        collection = self.db[collection_name]
        result = await collection.insert_one(document)
        print(f"✅ Gerente do Cofre: Novo registro com ID '{result.inserted_id}' arquivado com sucesso.")
        return result.inserted_id

# --- PONTO DE ACESSO ÚNICO E FUNÇÃO DE DEPENDÊNCIA (permanecem idênticos) ---
db_manager = DatabaseConnection()

async def get_database() -> DatabaseConnection:
    """Função para os outros serviços 'pedirem' acesso ao Gerente do Cofre."""
    if db_manager.db is None:
        await db_manager.connect()
    return db_manager
