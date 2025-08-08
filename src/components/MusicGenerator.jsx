import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Music,
  Mic,
  Upload,
  Sparkles,
  Play,
  Download,
  AlertCircle,
  CheckCircle,
  Loader2,
  LogOut,
  User,
  History,
  Pause,
  Bell,
  Settings,
  Radio,
  Headphones,
  Volume2,
  Clock,
  Eye
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import io from 'socket.io-client';

const MusicGenerator = ({ user, onLogout }) => {
  const [formData, setFormData] = useState({
    description: '',
    lyrics: '',
    musicName: '',
    voiceType: 'instrumental',
    genre: '',
    rhythm: '',
    instruments: '',
    studioType: 'studio'
  });
  
  const [voiceFile, setVoiceFile] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [alert, setAlert] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [estimatedTime, setEstimatedTime] = useState(null);
  const [userMusics, setUserMusics] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [processHistory, setProcessHistory] = useState([]);
  const [currentProcess, setCurrentProcess] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentPlayingId, setCurrentPlayingId] = useState(null);
  const [socket, setSocket] = useState(null);
  const [activeTab, setActiveTab] = useState('create');
  
  const fileInputRef = useRef(null);
  const audioRef = useRef(null);

  // Conecta ao WebSocket quando o componente monta
  useEffect(() => {
    const newSocket = io('/', {
      transports: ['websocket', 'polling']
    });

    newSocket.on('connect', () => {
      console.log('🔌 Conectado ao WebSocket');
      // Entra na sala do usuário para receber atualizações
      newSocket.emit('join_user_room', { userId: user.id });
    });

    newSocket.on('music_progress', (data) => {
      console.log('📊 Progresso recebido:', data);
      setProgress(data.progress);
      setProgressMessage(data.message);
      setEstimatedTime(data.estimated_time);
      setCurrentProcess(data);
    });

    newSocket.on('music_completed', (data) => {
      console.log('✅ Música concluída:', data);
      setIsGenerating(false);
      setProgress(100);
      setProgressMessage('🎉 Música pronta!');
      showAlert('success', `Sua música "${data.musicName}" está pronta!`);
      loadUserMusics();
      loadNotifications();
    });

    newSocket.on('music_error', (data) => {
      console.log('❌ Erro na geração:', data);
      setIsGenerating(false);
      setProgress(0);
      setProgressMessage('');
      showAlert('error', data.message || 'Erro na geração da música');
      loadNotifications();
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [user.id]);

  useEffect(() => {
    loadUserMusics();
    loadNotifications();
    loadProcessHistory();
  }, [user]);

  const loadUserMusics = async () => {
    try {
      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/music/musics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserMusics(data.musics || []);
      }
    } catch (error) {
      console.error('Erro ao carregar músicas:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/notifications/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
        setUnreadCount(data.filter(n => !n.read).length);
      }
    } catch (error) {
      console.error('Erro ao carregar notificações:', error);
    }
  };

  const loadProcessHistory = async () => {
    try {
      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/notifications/process-history', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProcessHistory(data);
      }
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    }
  };

  const markNotificationsAsRead = async () => {
    try {
      const token = localStorage.getItem('alquimista_token');
      await fetch('/api/notifications/mark-read', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Erro ao marcar notificações como lidas:', error);
    }
  };

  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      const allowedTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/flac'];
      if (!allowedTypes.includes(file.type)) {
        showAlert('error', 'Formato não suportado. Use MP3, WAV, M4A, OGG ou FLAC.');
        return;
      }
      
      if (file.size > 50 * 1024 * 1024) {
        showAlert('error', 'Arquivo muito grande. Máximo 50MB (aproximadamente 5 minutos).');
        return;
      }
      
      setVoiceFile(file);
      showAlert('success', `Arquivo "${file.name}" selecionado com sucesso!`);
    }
  };

  const handleGenerate = async () => {
    if (!formData.description.trim()) {
      showAlert('error', 'Por favor, descreva o estilo da música.');
      return;
    }
    
    if (!formData.musicName.trim()) {
      showAlert('error', 'Por favor, dê um nome para sua música.');
      return;
    }

    setIsGenerating(true);
    setProgress(5);
    setProgressMessage('📋 Preparando seu pedido...');
    showAlert('info', 'Enviando seu pedido para a cozinha musical...');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('description', formData.description);
      formDataToSend.append('musicName', formData.musicName);
      formDataToSend.append('voiceType', formData.voiceType);
      formDataToSend.append('lyrics', formData.lyrics);
      formDataToSend.append('genre', formData.genre);
      formDataToSend.append('rhythm', formData.rhythm);
      formDataToSend.append('instruments', formData.instruments);
      formDataToSend.append('studioType', formData.studioType);
      
      if (voiceFile) {
        formDataToSend.append('voiceSample', voiceFile);
      }

      const token = localStorage.getItem('alquimista_token');
      const response = await fetch('/api/music/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formDataToSend,
      });

      if (response.ok) {
        const result = await response.json();
        showAlert('success', result.message);
        setActiveTab('monitor'); // Muda para a aba de monitoramento
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao gerar música');
      }
    } catch (error) {
      console.error('Erro:', error);
      showAlert('error', error.message || 'Erro ao gerar música. Tente novamente.');
      setIsGenerating(false);
      setProgress(0);
      setProgressMessage('');
    }
  };

  const handlePlay = (musicUrl, musicId) => {
    if (currentPlayingId === musicId && isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      setCurrentPlayingId(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = musicUrl;
        audioRef.current.play();
        setIsPlaying(true);
        setCurrentPlayingId(musicId);
      }
    }
  };

  const handleDownload = (musicUrl, musicName) => {
    const link = document.createElement('a');
    link.href = musicUrl;
    link.download = `${musicName}.mp3`;
    link.click();
    showAlert('success', 'Download iniciado!');
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return "";
    return new Date(timestamp * 1000).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTimestamp = (isoString) => {
    return new Date(isoString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full">
              <Music className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white">Alquimista Musical</h1>
              <p className="text-purple-200">
                Estúdio Virtual Completo - Bem-vindo, {user.username}!
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Notificações */}
            <Button
              onClick={() => {
                setActiveTab('notifications');
                markNotificationsAsRead();
              }}
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10 relative"
            >
              <Bell className="w-4 h-4 mr-2" />
              Notificações
              {unreadCount > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-500 text-white text-xs">
                  {unreadCount}
                </Badge>
              )}
            </Button>
            
            <div className="flex items-center gap-2 text-white bg-white/10 px-3 py-2 rounded-lg">
              <User className="w-4 h-4" />
              <span>{user.username}</span>
            </div>
            <Button
              onClick={onLogout}
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sair
            </Button>
          </div>
        </motion.div>

        {/* Alert */}
        <AnimatePresence>
          {alert && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6"
            >
              <Alert className={`${
                alert.type === 'error' ? 'border-red-500 bg-red-50' : 
                alert.type === 'success' ? 'border-green-500 bg-green-50' :
                'border-blue-500 bg-blue-50'
              }`}>
                {alert.type === 'error' ? 
                  <AlertCircle className="h-4 w-4 text-red-600" /> : 
                  alert.type === 'success' ?
                  <CheckCircle className="h-4 w-4 text-green-600" /> :
                  <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                }
                <AlertDescription className={
                  alert.type === 'error' ? 'text-red-800' : 
                  alert.type === 'success' ? 'text-green-800' :
                  'text-blue-800'
                }>
                  {alert.message}
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-white/10 backdrop-blur-lg">
            <TabsTrigger value="create" className="text-white data-[state=active]:bg-purple-500">
              <Sparkles className="w-4 h-4 mr-2" />
              Criar Música
            </TabsTrigger>
            <TabsTrigger value="monitor" className="text-white data-[state=active]:bg-purple-500">
              <Eye className="w-4 h-4 mr-2" />
              Acompanhar Processo
            </TabsTrigger>
            <TabsTrigger value="history" className="text-white data-[state=active]:bg-purple-500">
              <History className="w-4 h-4 mr-2" />
              Suas Músicas
            </TabsTrigger>
            <TabsTrigger value="notifications" className="text-white data-[state=active]:bg-purple-500">
              <Bell className="w-4 h-4 mr-2" />
              Notificações
            </TabsTrigger>
          </TabsList>

          {/* Aba Criar Música */}
          <TabsContent value="create" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  Estúdio Virtual - Criar Nova Música
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Configure todos os parâmetros do seu estúdio virtual
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Coluna Esquerda */}
                  <div className="space-y-4">
                    {/* Nome da Música */}
                    <div className="space-y-2">
                      <Label htmlFor="musicName" className="text-white">
                        Nome da Música *
                      </Label>
                      <Input
                        id="musicName"
                        placeholder="Ex: Noite Chuvosa no Rio"
                        value={formData.musicName}
                        onChange={(e) => setFormData(prev => ({ ...prev, musicName: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                      />
                    </div>

                    {/* Descrição/Prompt */}
                    <div className="space-y-2">
                      <Label htmlFor="description" className="text-white">
                        Descrição/Prompt * (Essência da música)
                      </Label>
                      <Textarea
                        id="description"
                        placeholder="Ex: Uma bossa nova melancólica com piano suave, como uma noite chuvosa no Rio de Janeiro..."
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                        rows={3}
                      />
                    </div>

                    {/* Gênero Musical */}
                    <div className="space-y-2">
                      <Label className="text-white">Gênero Musical</Label>
                      <Select value={formData.genre} onValueChange={(value) => setFormData(prev => ({ ...prev, genre: value }))}>
                        <SelectTrigger className="bg-white/10 border-white/20 text-white">
                          <SelectValue placeholder="Selecione o gênero" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">Não especificado</SelectItem>
                          <SelectItem value="funk">Funk</SelectItem>
                          <SelectItem value="rock">Rock</SelectItem>
                          <SelectItem value="sertanejo">Sertanejo</SelectItem>
                          <SelectItem value="rap">Rap</SelectItem>
                          <SelectItem value="pop">Pop</SelectItem>
                          <SelectItem value="pagode">Pagode</SelectItem>
                          <SelectItem value="bossa-nova">Bossa Nova</SelectItem>
                          <SelectItem value="mpb">MPB</SelectItem>
                          <SelectItem value="eletronica">Eletrônica</SelectItem>
                          <SelectItem value="jazz">Jazz</SelectItem>
                          <SelectItem value="blues">Blues</SelectItem>
                          <SelectItem value="reggae">Reggae</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Ritmo */}
                    <div className="space-y-2">
                      <Label className="text-white">Ritmo Musical</Label>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { value: 'slow', label: 'Lento', icon: '🐌' },
                          { value: 'fast', label: 'Rápido', icon: '⚡' },
                          { value: 'mixed', label: 'Mesclado', icon: '🌊' }
                        ].map((option) => (
                          <Button
                            key={option.value}
                            type="button"
                            variant={formData.rhythm === option.value ? "default" : "outline"}
                            onClick={() => setFormData(prev => ({ ...prev, rhythm: option.value }))}
                            className={`${
                              formData.rhythm === option.value 
                                ? 'bg-purple-500 text-white' 
                                : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                            }`}
                          >
                            {option.icon} {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Coluna Direita */}
                  <div className="space-y-4">
                    {/* Tipo de Voz */}
                    <div className="space-y-2">
                      <Label className="text-white">Tipo de Voz *</Label>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { value: 'instrumental', label: 'Instrumental', icon: '🎼' },
                          { value: 'male', label: 'Voz Masculina', icon: '👨' },
                          { value: 'female', label: 'Voz Feminina', icon: '👩' },
                          { value: 'both', label: 'Dueto', icon: '👫' }
                        ].map((option) => (
                          <Button
                            key={option.value}
                            type="button"
                            variant={formData.voiceType === option.value ? "default" : "outline"}
                            onClick={() => setFormData(prev => ({ ...prev, voiceType: option.value }))}
                            className={`${
                              formData.voiceType === option.value 
                                ? 'bg-purple-500 text-white' 
                                : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                            }`}
                          >
                            {option.icon} {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Ambiente do Estúdio */}
                    <div className="space-y-2">
                      <Label className="text-white">Ambiente de Gravação</Label>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { value: 'studio', label: 'Estúdio', icon: <Headphones className="w-4 h-4" /> },
                          { value: 'live', label: 'Ao Vivo', icon: <Radio className="w-4 h-4" /> }
                        ].map((option) => (
                          <Button
                            key={option.value}
                            type="button"
                            variant={formData.studioType === option.value ? "default" : "outline"}
                            onClick={() => setFormData(prev => ({ ...prev, studioType: option.value }))}
                            className={`${
                              formData.studioType === option.value 
                                ? 'bg-purple-500 text-white' 
                                : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                            }`}
                          >
                            {option.icon}
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Instrumentos */}
                    <div className="space-y-2">
                      <Label htmlFor="instruments" className="text-white">
                        Instrumentos Específicos (Opcional)
                      </Label>
                      <Input
                        id="instruments"
                        placeholder="Ex: piano, violão, bateria, saxofone..."
                        value={formData.instruments}
                        onChange={(e) => setFormData(prev => ({ ...prev, instruments: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                      />
                    </div>

                    {/* Letra da Música */}
                    <div className="space-y-2">
                      <Label htmlFor="lyrics" className="text-white">
                        Letra da Música (Opcional)
                      </Label>
                      <Textarea
                        id="lyrics"
                        placeholder="Digite aqui a letra da sua música..."
                        value={formData.lyrics}
                        onChange={(e) => setFormData(prev => ({ ...prev, lyrics: e.target.value }))}
                        className="bg-white/10 border-white/20 text-white placeholder:text-purple-300"
                        rows={3}
                      />
                    </div>
                  </div>
                </div>

                {/* Canta aí, solte a voz */}
                {formData.voiceType !== 'instrumental' && (
                  <div className="space-y-2">
                    <Label className="text-white">🎤 Canta aí, solte a voz! (Até 5 minutos)</Label>
                    <div className="flex flex-col gap-3">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        className="bg-white/10 border-white/20 text-white hover:bg-white/20 justify-start"
                      >
                        {voiceFile ? (
                          <>
                            <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                            {voiceFile.name}
                          </>
                        ) : (
                          <>
                            <Upload className="w-4 h-4 mr-2" />
                            Gravar ou selecionar arquivo de áudio
                          </>
                        )}
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="audio/*"
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="secondary" className="bg-white/10 text-purple-200">MP3</Badge>
                        <Badge variant="secondary" className="bg-white/10 text-purple-200">WAV</Badge>
                        <Badge variant="secondary" className="bg-white/10 text-purple-200">M4A</Badge>
                        <Badge variant="secondary" className="bg-white/10 text-purple-200">Max 50MB</Badge>
                        <Badge variant="secondary" className="bg-white/10 text-purple-200">Até 5 min</Badge>
                      </div>
                    </div>
                  </div>
                )}

                {/* Botão de Gerar */}
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-4 text-lg"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Criando Magia Musical...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 mr-2" />
                      🍳 Enviar Pedido para a Cozinha
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aba Acompanhar Processo */}
          <TabsContent value="monitor" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Eye className="w-5 h-5 text-purple-400" />
                  👀 Olhando pelo Vidro da Cozinha
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Acompanhe em tempo real cada etapa da criação da sua música
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {isGenerating || currentProcess ? (
                  <div className="space-y-4">
                    {/* Barra de Progresso Principal */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-white">
                        <span className="font-medium">{progressMessage || 'Processando...'}</span>
                        <div className="flex items-center gap-2">
                          <span>{Math.round(progress)}%</span>
                          {estimatedTime && (
                            <Badge variant="secondary" className="bg-white/10 text-purple-200">
                              <Clock className="w-3 h-3 mr-1" />
                              ~{estimatedTime}s
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Progress value={progress} className="bg-white/20 h-3" />
                    </div>

                    {/* Status Atual */}
                    <div className="bg-white/5 rounded-lg p-4">
                      <h3 className="text-white font-medium mb-2">Status Atual:</h3>
                      <p className="text-purple-200">{progressMessage}</p>
                      {currentProcess && (
                        <div className="mt-2 text-sm text-purple-300">
                          Etapa: {currentProcess.step} | Processo ID: {currentProcess.process_id?.slice(0, 8)}...
                        </div>
                      )}
                    </div>

                    {/* Etapas do Processo */}
                    <div className="space-y-2">
                      <h3 className="text-white font-medium">Etapas do Processo:</h3>
                      <div className="space-y-1 text-sm">
                        {[
                          { step: 'received', label: '📋 Pedido recebido', min: 0, max: 10 },
                          { step: 'connecting', label: '🔌 Conectando com a cozinha', min: 10, max: 20 },
                          { step: 'sending_order', label: '📝 Enviando pedido', min: 20, max: 30 },
                          { step: 'preparing', label: '👨‍🍳 Chef IA analisando', min: 30, max: 50 },
                          { step: 'cooking', label: '🔥 No forno da IA', min: 50, max: 70 },
                          { step: 'waiting_result', label: '⏳ Aguardando resultado', min: 70, max: 85 },
                          { step: 'finalizing', label: '🎵 Finalizando detalhes', min: 85, max: 95 },
                          { step: 'uploading', label: '☁️ Garçom levando à mesa', min: 95, max: 98 },
                          { step: 'saving', label: '💾 Registrando no cardápio', min: 98, max: 100 },
                          { step: 'completed', label: '🎉 Música servida!', min: 100, max: 100 }
                        ].map((item) => (
                          <div
                            key={item.step}
                            className={`flex items-center gap-2 p-2 rounded ${
                              progress >= item.min ? 'bg-green-500/20 text-green-300' : 'bg-white/5 text-purple-300'
                            }`}
                          >
                            <div className={`w-2 h-2 rounded-full ${
                              progress >= item.min ? 'bg-green-400' : 'bg-gray-400'
                            }`} />
                            {item.label}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">🍽️</div>
                    <h3 className="text-white text-xl mb-2">Cozinha Vazia</h3>
                    <p className="text-purple-200">
                      Nenhum pedido em andamento. Vá para "Criar Música" para fazer um novo pedido!
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aba Suas Músicas */}
          <TabsContent value="history" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-purple-400" />
                  Suas Músicas
                </CardTitle>
                <CardDescription className="text-purple-200">
                  {userMusics.length} música{userMusics.length !== 1 ? 's' : ''} criada{userMusics.length !== 1 ? 's' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {userMusics.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-4xl mb-4">🎵</div>
                      <p className="text-purple-200">
                        Você ainda não criou nenhuma música. Que tal começar agora?
                      </p>
                    </div>
                  ) : (
                    userMusics.map((music, index) => (
                      <motion.div
                        key={music._id || index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h3 className="text-white font-medium">{music.musicName || 'Música Sem Nome'}</h3>
                            <p className="text-purple-300 text-sm mt-1">
                              {music.description?.substring(0, 100)}...
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge variant="secondary" className="bg-purple-500/20 text-purple-200">
                                {music.voiceType || 'instrumental'}
                              </Badge>
                              {music.genre && (
                                <Badge variant="secondary" className="bg-blue-500/20 text-blue-200">
                                  {music.genre}
                                </Badge>
                              )}
                              <span className="text-purple-400 text-xs">
                                {formatDate(music.timestamp)}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 ml-4">
                            <Button
                              onClick={() => handlePlay(music.musicUrl, music._id)}
                              size="sm"
                              variant="outline"
                              className="border-white/20 text-white hover:bg-white/10"
                            >
                              {currentPlayingId === music._id && isPlaying ? (
                                <Pause className="w-4 h-4" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                            </Button>
                            <Button
                              onClick={() => handleDownload(music.musicUrl, music.musicName)}
                              size="sm"
                              variant="outline"
                              className="border-white/20 text-white hover:bg-white/10"
                            >
                              <Download className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </motion.div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aba Notificações */}
          <TabsContent value="notifications" className="mt-6">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Bell className="w-5 h-5 text-purple-400" />
                  Central de Notificações
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Histórico completo de processos e notificações
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-4xl mb-4">🔔</div>
                      <p className="text-purple-200">
                        Nenhuma notificação ainda. Suas notificações aparecerão aqui!
                      </p>
                    </div>
                  ) : (
                    notifications.map((notification, index) => (
                      <motion.div
                        key={notification.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`bg-white/5 rounded-lg p-4 border-l-4 ${
                          notification.type === 'success' ? 'border-green-400' :
                          notification.type === 'error' ? 'border-red-400' :
                          'border-blue-400'
                        } ${!notification.read ? 'bg-white/10' : ''}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="text-white font-medium">{notification.title}</h3>
                            <p className="text-purple-300 text-sm mt-1">{notification.message}</p>
                            <span className="text-purple-400 text-xs">
                              {formatTimestamp(notification.timestamp)}
                            </span>
                          </div>
                          {!notification.read && (
                            <div className="w-2 h-2 bg-blue-400 rounded-full ml-2 mt-2" />
                          )}
                        </div>
                      </motion.div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Audio Element */}
        <audio
          ref={audioRef}
          onEnded={() => {
            setIsPlaying(false);
            setCurrentPlayingId(null);
          }}
          className="hidden"
        />
      </div>
    </div>
  );
};

export default MusicGenerator;

