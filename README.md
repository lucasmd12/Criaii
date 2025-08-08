# 🎵 Alquimista Musical - Gerador de Música com IA

Um aplicativo completo para gerar músicas usando Inteligência Artificial, com interface moderna e sistema de autenticação.

## ✨ Funcionalidades

### 🎼 Geração de Música
- **Geração por IA**: Usa Hugging Face (MusicGen) para criar músicas
- **Tipos de Voz**: Instrumental, Masculina, Feminina ou Dueto
- **Personalização**: Nome da música, descrição, gênero e duração
- **Upload Automático**: Salva no Cloudinary automaticamente

### 🎧 Player de Áudio
- **Reprodução**: Player integrado com controles
- **Download**: Baixe suas músicas criadas
- **Biblioteca**: Organize todas suas criações
- **Histórico**: Veja quando cada música foi criada

### 👤 Sistema de Autenticação
- **Login/Registro**: Sistema seguro com JWT
- **Username/Senha**: Sem necessidade de email
- **Sessões**: Mantenha-se logado por 7 dias
- **Segurança**: Senhas criptografadas

### 🎨 Interface Moderna
- **Design Responsivo**: Funciona em desktop e mobile
- **Tema Escuro**: Interface elegante com gradientes
- **Componentes UI**: Usando shadcn/ui e Tailwind CSS
- **Experiência Fluida**: Navegação por abas intuitiva

## 🛠️ Tecnologias

### Backend (Flask)
- **Flask**: Framework web Python
- **MongoDB**: Banco de dados (com fallback em memória)
- **JWT**: Autenticação segura
- **Cloudinary**: Armazenamento de áudio
- **Hugging Face**: API de geração de música
- **CORS**: Configurado para frontend

### Frontend (React)
- **React 18**: Interface moderna
- **Vite**: Build tool rápido
- **Tailwind CSS**: Estilização
- **shadcn/ui**: Componentes UI
- **Lucide Icons**: Ícones modernos

## 🚀 Como Usar

### Pré-requisitos
- Python 3.11+
- Node.js 20+
- Chaves de API configuradas

### Configuração do Backend

1. **Instale as dependências:**
```bash
cd alquimista_musical
pip install -r requirements.txt
```

2. **Configure as variáveis de ambiente (.env):**
```env
SECRET_KEY=alquimista-musical-secret-key-2024-production
HF_TOKEN=seu_token_hugging_face
CLOUDINARY_CLOUD_NAME=seu_cloudinary_name
CLOUDINARY_API_KEY=sua_cloudinary_key
CLOUDINARY_API_SECRET=seu_cloudinary_secret
MONGO_URI=sua_string_conexao_mongodb
```

3. **Execute o servidor:**
```bash
python3 src/main.py
```

### Configuração do Frontend

1. **Instale as dependências:**
```bash
cd alquimista-frontend
npm install
```

2. **Configure a URL da API:**
- Para desenvolvimento local: `http://localhost:5001/api`
- Para produção: `https://alquimistamusical.onrender.com/api`

3. **Execute o servidor de desenvolvimento:**
```bash
npm run dev -- --host
```

## 📁 Estrutura do Projeto

### Backend (`alquimista_musical/`)
```
src/
├── main.py                 # Aplicação principal Flask
├── models/
│   └── mongo_models.py     # Modelos MongoDB com fallback
├── routes/
│   ├── user.py            # Rotas de autenticação
│   ├── music.py           # Rotas de geração de música
│   └── music_list.py      # Rotas de listagem
├── services/
│   ├── cloudinary_service.py    # Upload de áudio
│   ├── firebase_service.py      # Desabilitado
│   └── music_generation_service.py  # Geração com IA
└── static/                # Frontend compilado (opcional)
```

### Frontend (`alquimista-frontend/`)
```
src/
├── App.jsx               # Componente principal
├── components/ui/        # Componentes shadcn/ui
├── assets/              # Recursos estáticos
└── main.jsx             # Ponto de entrada
```

## 🔧 APIs e Endpoints

### Autenticação
- `POST /api/register` - Registrar usuário
- `POST /api/login` - Fazer login
- `GET /api/profile` - Obter perfil (requer token)

### Música
- `POST /api/generate` - Gerar nova música
- `GET /api/musics` - Listar músicas do usuário
- `GET /api/health` - Verificar saúde da API

## 🎯 Funcionalidades Implementadas

### ✅ Concluído
- [x] Sistema de autenticação completo
- [x] Geração de música com IA
- [x] Player de áudio funcional
- [x] Upload automático para Cloudinary
- [x] Interface responsiva
- [x] Banco de dados com fallback
- [x] CORS configurado
- [x] Firebase desabilitado
- [x] Documentação completa

### 🔄 Melhorias Futuras
- [ ] Sistema de notificações em tempo real
- [ ] Compartilhamento de músicas
- [ ] Playlists personalizadas
- [ ] Análise de sentimento das letras
- [ ] Colaboração entre usuários

## 🐛 Solução de Problemas

### MongoDB não conecta
- O sistema usa fallback em memória automaticamente
- Verifique as credenciais no arquivo .env
- Confirme se o IP está liberado no MongoDB Atlas

### Música não gera
- Verifique se o token do Hugging Face está correto
- Confirme se as credenciais do Cloudinary estão configuradas
- Veja os logs do backend para detalhes

### Frontend não conecta
- Confirme se a URL da API está correta no App.jsx
- Verifique se o backend está rodando
- Abra o console do navegador para ver erros

## 📝 Notas de Desenvolvimento

### Banco de Dados
- **MongoDB**: Preferencial para produção
- **Fallback**: Sistema em memória para desenvolvimento
- **Migração**: Automática entre os dois sistemas

### Segurança
- **JWT**: Tokens válidos por 7 dias
- **CORS**: Configurado para aceitar qualquer origem
- **Senhas**: Criptografadas com Werkzeug

### Deploy
- **Backend**: Compatível com Render, Heroku, etc.
- **Frontend**: Pode ser servido pelo próprio Flask
- **Variáveis**: Configure todas as chaves de API

## 🎵 Créditos

Desenvolvido com ❤️ usando:
- [Hugging Face](https://huggingface.co/) para IA de música
- [Cloudinary](https://cloudinary.com/) para armazenamento
- [MongoDB](https://mongodb.com/) para banco de dados
- [React](https://react.dev/) para interface
- [Flask](https://flask.palletsprojects.com/) para backend

---

**Versão**: 1.0.0  
**Status**: Funcional e pronto para uso  
**Última atualização**: Agosto 2025

