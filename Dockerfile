# Etapa 1: Use a imagem oficial do Python fornecida pelo Render como base.
# Isso nos dá um ambiente Python 3.12 limpo e padrão.
FROM python:3.12-slim

# Etapa 2: Instale as ferramentas de sistema necessárias ANTES de instalar o Python.
# - 'build-essential' contém compiladores C/C++
# - 'gfortran' é o compilador Fortran que o SciPy precisa.
# - 'libgfortran5' é a biblioteca de tempo de execução do Fortran.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libgfortran5 \
    && rm -rf /var/lib/apt/lists/*

# Etapa 3: Configure o diretório de trabalho dentro do contêiner.
WORKDIR /app

# Etapa 4: Copie o seu arquivo de dependências para dentro do contêiner.
COPY requirements.txt .

# Etapa 5: Instale as dependências do Python usando a "Receita Mestra".
# Agora, quando o SciPy for ser construído, ele encontrará o gfortran.
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 6: Copie todo o resto do seu código para dentro do contêiner.
COPY . .

# Etapa 7: Diga ao Gunicorn em qual porta ele deve escutar.
# O Render espera que os serviços escutem na porta 10000.
ENV PORT 10000

# Etapa 8: O comando para iniciar o seu aplicativo.
# Este comando é executado quando o contêiner é iniciado.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "4", "src.main:application"]
