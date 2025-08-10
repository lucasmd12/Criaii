# gunicorn_conf.py
import os

# Configuração do Gunicorn para FastAPI
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Preload da aplicação
preload_app = True

# Configurações de processo
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Configurações de SSL (se necessário)
keyfile = None
certfile = None
