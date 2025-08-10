import os
import asyncio
import threading
import time
from datetime import datetime
import httpx
from gradio_client import Client

class KeepAliveService:
    """Serviço para manter o Hugging Face Space sempre ativo."""
    
    def __init__(self):
        self.HUGGING_FACE_SPACE_URL = os.getenv("HUGGING_FACE_SPACE_URL")
        self.is_running = False
        self.ping_interval = 300  # 5 minutos
        self.last_ping = None
        self.ping_thread = None
        
    def start(self):
        """Inicia o serviço de keep-alive."""
        if self.is_running:
            print("⚠️ Keep-alive já está rodando")
            return
            
        if not self.HUGGING_FACE_SPACE_URL:
            print("❌ HUGGING_FACE_SPACE_URL não configurada. Keep-alive não será iniciado.")
            return
            
        self.is_running = True
        self.ping_thread = threading.Thread(target=self._run_keep_alive, daemon=True)
        self.ping_thread.start()
        print(f"🔄 Keep-alive iniciado para {self.HUGGING_FACE_SPACE_URL}")
        print(f"⏰ Ping a cada {self.ping_interval} segundos")
    
    def stop(self):
        """Para o serviço de keep-alive."""
        self.is_running = False
        print("🛑 Keep-alive parado")
    
    def _run_keep_alive(self):
        """Loop principal do keep-alive."""
        while self.is_running:
            try:
                self._ping_space()
                time.sleep(self.ping_interval)
            except Exception as e:
                print(f"❌ Erro no keep-alive: {e}")
                time.sleep(60)  # Espera 1 minuto antes de tentar novamente
    
    def _ping_space(self):
        """Envia um ping leve para o Space."""
        try:
            start_time = time.time()
            
            # Tenta fazer uma requisição HTTP simples primeiro
            with httpx.Client(timeout=30.0) as client:
                response = client.get(self.HUGGING_FACE_SPACE_URL)
                
            if response.status_code == 200:
                ping_time = round((time.time() - start_time) * 1000, 2)
                self.last_ping = datetime.now()
                print(f"🏓 Ping para cozinha: {ping_time}ms - Status: Ativa")
            else:
                print(f"⚠️ Ping retornou status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro no ping: {e}")
            # Se o ping HTTP falhar, tenta um ping via Gradio Client
            try:
                client = Client(self.HUGGING_FACE_SPACE_URL)
                # Faz uma chamada muito simples só para "acordar" o space
                print("🔄 Tentando acordar o Space via Gradio Client...")
                self.last_ping = datetime.now()
            except Exception as gradio_error:
                print(f"❌ Erro no ping via Gradio: {gradio_error}")
    
    def get_status(self):
        """Retorna o status atual do keep-alive."""
        return {
            "is_running": self.is_running,
            "last_ping": self.last_ping.isoformat() if self.last_ping else None,
            "ping_interval": self.ping_interval,
            "space_url": self.HUGGING_FACE_SPACE_URL
        }

# Instância global do serviço
keep_alive_service = KeepAliveService()

