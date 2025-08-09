# src/database.py
import os
import motor.motor_asyncio
from dotenv import load_dotenv

# Carrega as variáveis de ambiente para garantir que a URI do Mongo esteja disponível
load_dotenv()

MONGO_DB_URI = os.getenv("MONGO_DB_URI")

if not MONGO_DB_URI:
    raise Exception("❌ A variável de ambiente MONGO_DB_URI não foi definida!")

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        print("🔌 Conectando ao MongoDB Atlas...")
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DB_URI)
            # O nome do banco de dados é geralmente parte da URI, mas podemos definir um padrão
            self.db = self.client.get_database("alquimista_musical_db") 
            print("✅ MongoDB Atlas conectado com sucesso!")
        except Exception as e:
            print(f"❌ Falha ao conectar ao MongoDB: {e}")
            self.client = None
            self.db = None
    
    def disconnect(self):
        if self.client:
            self.client.close()
            print("🔌 Conexão com o MongoDB fechada.")

# Cria uma instância única que será usada em toda a aplicação
db_connection = Database()

# Exporta a variável 'db' que será o objeto do banco de dados após a conexão
# Inicialmente será None, mas será preenchida no startup do FastAPI
db = None
