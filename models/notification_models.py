# src/models/notification_models.py
# Função: O Fichário de Registro do Alquimista Musical
# Responsabilidade: Moldes e fichas padronizadas para avisos e histórico de comandas

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId

# ================== FICHÁRIO DE REGISTRO DO ALQUIMISTA MUSICAL ==================
# Este arquivo contém as "fichas de registro" padronizadas que o Arquivista utiliza
# para documentar cada aviso, cada comanda e cada etapa do processo alquímico.
# Cada classe representa um tipo específico de registro no livro principal do restaurante.
# =================================================================================

class NotificationBase(BaseModel):
    """Ficha base para todos os avisos do Painel de Avisos do Alquimista Musical."""
    
    class Config:
        # Permite que ObjectIds sejam convertidos automaticamente
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat() if v else None
        }

class Notification(NotificationBase):
    """
    Ficha de Registro para Avisos do Painel.
    Representa cada mensagem que o Arquivista registra no livro de avisos dos clientes.
    Cada instância é como uma nota adesiva no painel pessoal do cliente.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="ID do cliente no restaurante")
    title: str = Field(..., description="Título do aviso no painel")
    message: str = Field(..., description="Mensagem completa do aviso")
    type: str = Field(default="info", description="Tipo do aviso (info, success, warning, error)")
    read: bool = Field(default=False, description="Indica se o cliente já leu este aviso")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Momento em que o aviso foi criado")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dados adicionais do aviso")
    
    @classmethod
    async def create_in_db(cls, db, user_id: str, title: str, message: str, 
                          notification_type: str = "info", metadata: Dict = None) -> Optional[str]:
        """
        O Arquivista registra um novo aviso no painel do cliente.
        Retorna o ID do registro criado ou None em caso de erro.
        """
        try:
            notification_data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "read": False,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            result = await db.notifications.insert_one(notification_data)
            print(f"📋 Arquivista registrou novo aviso para cliente {user_id}: {title}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Arquivista falhou ao registrar aviso: {e}")
            return None
    
    @classmethod
    async def find_user_notifications(cls, db, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict]:
        """
        O Arquivista consulta o painel de avisos de um cliente específico.
        Retorna uma lista organizada dos avisos mais recentes primeiro.
        """
        try:
            cursor = db.notifications.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
            notifications = await cursor.to_list(length=limit)
            
            # O Arquivista formata os dados para apresentação no Salão de Jantar
            for notification in notifications:
                notification["id"] = str(notification.pop("_id"))
                notification["timestamp"] = notification["timestamp"].isoformat()
            
            print(f"📖 Arquivista consultou painel: {len(notifications)} avisos encontrados para cliente {user_id}")
            return notifications
            
        except Exception as e:
            print(f"❌ Arquivista falhou ao consultar painel: {e}")
            return []
    
    @classmethod
    async def count_unread_for_user(cls, db, user_id: str) -> int:
        """
        O Arquivista conta rapidamente quantos avisos não lidos um cliente possui.
        Essencial para indicadores visuais no Salão de Jantar.
        """
        try:
            count = await db.notifications.count_documents({"user_id": user_id, "read": False})
            print(f"🔢 Arquivista contou: cliente {user_id} tem {count} avisos não lidos")
            return count
        except Exception as e:
            print(f"❌ Arquivista falhou ao contar avisos não lidos: {e}")
            return 0
    
    @classmethod
    async def mark_as_read_for_user(cls, db, user_id: str, notification_ids: List[str] = None) -> int:
        """
        O Arquivista marca avisos como lidos no painel do cliente.
        Pode marcar avisos específicos ou todos os não lidos.
        """
        try:
            query = {"user_id": user_id, "read": False}
            if notification_ids:
                query["_id"] = {"$in": [ObjectId(nid) for nid in notification_ids]}
            
            result = await db.notifications.update_many(query, {"$set": {"read": True}})
            
            action_description = f"{len(notification_ids)} avisos específicos" if notification_ids else "todos os avisos não lidos"
            print(f"✅ Arquivista marcou {action_description} como lidos para cliente {user_id}")
            return result.modified_count
            
        except Exception as e:
            print(f"❌ Arquivista falhou ao marcar avisos como lidos: {e}")
            return 0

class ProcessHistoryBase(BaseModel):
    """Ficha base para todos os registros de histórico de comandas do Alquimista Musical."""
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat() if v else None
        }

class ProcessHistory(ProcessHistoryBase):
    """
    Ficha de Registro para o Histórico de Comandas.
    Representa cada etapa documentada no processo de preparação de uma música.
    O Arquivista utiliza esta ficha para manter um registro detalhado de cada comanda
    desde o momento em que chega à Cozinha até sua entrega final no Salão de Jantar.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="ID do cliente que fez o pedido")
    process_id: str = Field(..., description="ID único da comanda em processamento")
    step: str = Field(..., description="Etapa atual do processo alquímico")
    status: str = Field(..., description="Status da etapa (processing, completed, error)")
    message: str = Field(..., description="Descrição detalhada da etapa")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Momento de registro da etapa")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dados técnicos adicionais da etapa")
    
    @classmethod
    async def save_process_step(cls, db, user_id: str, process_id: str, step: str, 
                               status: str, message: str, metadata: Dict = None):
        """
        O Arquivista registra uma nova etapa no histórico de uma comanda específica.
        Utiliza upsert para garantir que cada comanda tenha apenas um registro atual.
        """
        try:
            process_data = {
                "user_id": user_id,
                "process_id": process_id,
                "step": step,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            await db.process_history.update_one(
                {"user_id": user_id, "process_id": process_id},
                {"$set": process_data, "$setOnInsert": {"user_id": user_id, "process_id": process_id}},
                upsert=True
            )
            
            print(f"📋 Arquivista registrou etapa da comanda {process_id}: {step} ({status})")
            
        except Exception as e:
            print(f"❌ Arquivista falhou ao registrar etapa da comanda: {e}")
    
    @classmethod
    async def find_user_history(cls, db, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """
        O Arquivista consulta o histórico completo de comandas de um cliente.
        Organiza cronologicamente as etapas de todas as comandas processadas.
        """
        try:
            cursor = db.process_history.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
            history = await cursor.to_list(length=limit)
            
            # O Arquivista formata os registros para apresentação
            for record in history:
                record["id"] = str(record.pop("_id"))
                record["timestamp"] = record["timestamp"].isoformat()
            
            print(f"📚 Arquivista consultou histórico: {len(history)} registros encontrados para cliente {user_id}")
            return history
            
        except Exception as e:
            print(f"❌ Arquivista falhou ao consultar histórico: {e}")
            return []

# ================== REGISTRO FINAL DO FICHÁRIO ==================
# O Arquivista mantém uma instância de serviço que utiliza estas fichas
# para organizar e gerenciar todos os registros do restaurante.
# Esta instância é "alimentada" externamente com o gerenciador de banco de dados.
# ================================================================

class ArchivistService:
    """
    O Arquivista do Alquimista Musical.
    Responsável por manter organizados todos os registros de avisos e histórico de comandas.
    Utiliza as fichas padronizadas para garantir consistência nos registros.
    """
    
    def __init__(self):
        print("🗄️ Arquivista do Alquimista Musical iniciado. Fichário de registros pronto para operação.")
    
    async def register_notification(self, db_manager, user_id: str, title: str, message: str, 
                                  notification_type: str = "info", metadata: Dict = None) -> Optional[str]:
        """Registra um novo aviso utilizando a ficha padronizada de notificação."""
        return await Notification.create_in_db(db_manager.db, user_id, title, message, notification_type, metadata)
    
    async def register_process_step(self, db_manager, user_id: str, process_id: str, step: str, 
                                   status: str, message: str, metadata: Dict = None):
        """Registra uma etapa do processo utilizando a ficha padronizada de histórico."""
        await ProcessHistory.save_process_step(db_manager.db, user_id, process_id, step, status, message, metadata)
    
    async def get_user_notifications(self, db_manager, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict]:
        """Consulta avisos de um cliente utilizando a ficha de notificação."""
        return await Notification.find_user_notifications(db_manager.db, user_id, limit, skip)
    
    async def get_unread_count(self, db_manager, user_id: str) -> int:
        """Conta avisos não lidos de um cliente utilizando a ficha de notificação."""
        return await Notification.count_unread_for_user(db_manager.db, user_id)
    
    async def mark_notifications_as_read(self, db_manager, user_id: str, notification_ids: List[str] = None) -> int:
        """Marca avisos como lidos utilizando a ficha de notificação."""
        return await Notification.mark_as_read_for_user(db_manager.db, user_id, notification_ids)
    
    async def get_process_history(self, db_manager, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Consulta histórico de comandas de um cliente utilizando a ficha de histórico."""
        return await ProcessHistory.find_user_history(db_manager.db, user_id, limit, skip)

# ================== INSTÂNCIA GLOBAL DO ARQUIVISTA ==================
# O Arquivista está sempre disponível para ser consultado pelo Maître D'
# através do sistema de dependências do restaurante.
notification_service = ArchivistService()
# ====================================================================
