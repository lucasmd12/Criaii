import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Music, 
  User, 
  Lock, 
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const LoginForm = ({ onLogin }) => {
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  })
  
  const [registerData, setRegisterData] = useState({
    username: '',
    password: '',
    confirmPassword: ''
  })
  
  const [isLoading, setIsLoading] = useState(false)
  const [alert, setAlert] = useState(null)

  const showAlert = (type, message) => {
    setAlert({ type, message })
    setTimeout(() => setAlert(null), 5000)
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    
    if (!loginData.username.trim() || !loginData.password.trim()) {
      showAlert('error', 'Por favor, preencha todos os campos.')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      })

      const data = await response.json()

      if (response.ok) {
        showAlert('success', 'Login realizado com sucesso!')
        setTimeout(() => {
          onLogin(data.user, data.token)
        }, 1000)
      } else {
        throw new Error(data.error || 'Erro ao fazer login')
      }
    } catch (error) {
      console.error('Erro no login:', error)
      showAlert('error', error.message || 'Erro ao fazer login. Tente novamente.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    
    if (!registerData.username.trim() || !registerData.password.trim() || !registerData.confirmPassword.trim()) {
      showAlert('error', 'Por favor, preencha todos os campos.')
      return
    }

    if (registerData.password !== registerData.confirmPassword) {
      showAlert('error', 'As senhas não coincidem.')
      return
    }

    if (registerData.password.length < 6) {
      showAlert('error', 'A senha deve ter pelo menos 6 caracteres.')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: registerData.username,
          password: registerData.password
        }),
      })

      const data = await response.json()

      if (response.ok) {
        showAlert('success', 'Conta criada com sucesso!')
        setTimeout(() => {
          onLogin(data.user, data.token)
        }, 1000)
      } else {
        throw new Error(data.error || 'Erro ao criar conta')
      }
    } catch (error) {
      console.error('Erro no registro:', error)
      showAlert('error', error.message || 'Erro ao criar conta. Tente novamente.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full">
              <Music className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Alquimista Musical</h1>
          </div>
          <p className="text-purple-200">
            Entre na sua conta para criar músicas incríveis
          </p>
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
              <Alert className={`${alert.type === 'error' ? 'border-red-500 bg-red-50' : 'border-green-500 bg-green-50'}`}>
                {alert.type === 'error' ? 
                  <AlertCircle className="h-4 w-4 text-red-600" /> : 
                  <CheckCircle className="h-4 w-4 text-green-600" />
                }
                <AlertDescription className={alert.type === 'error' ? 'text-red-800' : 'text-green-800'}>
                  {alert.message}
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Login/Register Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-white/10 backdrop-blur-lg border-white/20">
            <CardHeader>
              <CardTitle className="text-white text-center">Bem-vindo</CardTitle>
              <CardDescription className="text-purple-200 text-center">
                Faça login ou crie sua conta
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="login" className="w-full">
                <TabsList className="grid w-full grid-cols-2 bg-white/10">
                  <TabsTrigger value="login" className="text-white data-[state=active]:bg-white/20">
                    Entrar
                  </TabsTrigger>
                  <TabsTrigger value="register" className="text-white data-[state=active]:bg-white/20">
                    Criar Conta
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="login" className="space-y-4 mt-6">
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-username" className="text-white">
                        Nome de usuário
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-purple-300" />
                        <Input
                          id="login-username"
                          type="text"
                          placeholder="Digite seu usuário"
                          value={loginData.username}
                          onChange={(e) => setLoginData(prev => ({ ...prev, username: e.target.value }))}
                          className="bg-white/10 border-white/20 text-white placeholder:text-purple-300 pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="login-password" className="text-white">
                        Senha
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-purple-300" />
                        <Input
                          id="login-password"
                          type="password"
                          placeholder="Digite sua senha"
                          value={loginData.password}
                          onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
                          className="bg-white/10 border-white/20 text-white placeholder:text-purple-300 pl-10"
                        />
                      </div>
                    </div>
                    
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Entrando...
                        </>
                      ) : (
                        'Entrar'
                      )}
                    </Button>
                  </form>
                </TabsContent>
                
                <TabsContent value="register" className="space-y-4 mt-6">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-username" className="text-white">
                        Nome de usuário
                      </Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-purple-300" />
                        <Input
                          id="register-username"
                          type="text"
                          placeholder="Escolha um usuário"
                          value={registerData.username}
                          onChange={(e) => setRegisterData(prev => ({ ...prev, username: e.target.value }))}
                          className="bg-white/10 border-white/20 text-white placeholder:text-purple-300 pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-password" className="text-white">
                        Senha
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-purple-300" />
                        <Input
                          id="register-password"
                          type="password"
                          placeholder="Crie uma senha (min. 6 caracteres)"
                          value={registerData.password}
                          onChange={(e) => setRegisterData(prev => ({ ...prev, password: e.target.value }))}
                          className="bg-white/10 border-white/20 text-white placeholder:text-purple-300 pl-10"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-confirm-password" className="text-white">
                        Confirmar Senha
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-purple-300" />
                        <Input
                          id="register-confirm-password"
                          type="password"
                          placeholder="Confirme sua senha"
                          value={registerData.confirmPassword}
                          onChange={(e) => setRegisterData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                          className="bg-white/10 border-white/20 text-white placeholder:text-purple-300 pl-10"
                        />
                      </div>
                    </div>
                    
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Criando conta...
                        </>
                      ) : (
                        'Criar Conta'
                      )}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center mt-6 text-purple-300"
        >
          <p className="text-sm">Feito com ❤️ e muito código • Alquimista Musical v1.0</p>
        </motion.div>
      </div>
    </div>
  )
}

export default LoginForm

