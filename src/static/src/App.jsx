import { useState, useEffect } from 'react'
import MusicGenerator from './components/MusicGenerator'
import LoginForm from './components/LoginForm'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Verificar se há token salvo no localStorage
    const token = localStorage.getItem('alquimista_token')
    if (token) {
      // Verificar se o token é válido
      fetch('/api/profile', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.valid) {
          setUser(data.user)
        } else {
          localStorage.removeItem('alquimista_token')
        }
      })
      .catch(() => {
        localStorage.removeItem('alquimista_token')
      })
      .finally(() => {
        setIsLoading(false)
      })
    } else {
      setIsLoading(false)
    }
  }, [])

  const handleLogin = (userData, token) => {
    setUser(userData)
    localStorage.setItem('alquimista_token', token)
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('alquimista_token')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Carregando...</div>
      </div>
    )
  }

  return (
    <div className="App">
      {user ? (
        <MusicGenerator user={user} onLogout={handleLogout} />
      ) : (
        <LoginForm onLogin={handleLogin} />
      )}
    </div>
  )
}

export default App
