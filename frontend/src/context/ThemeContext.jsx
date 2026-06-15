import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext(null)

function applyTheme(dark) {
  const root = document.documentElement
  if (dark) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

export function ThemeProvider({ children }) {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('bs_theme')
    // Si no hay preferencia guardada, detectar preferencia del sistema
    if (!saved) return window.matchMedia('(prefers-color-scheme: dark)').matches
    return saved === 'dark'
  })

  // Aplicar al montar
  useEffect(() => {
    applyTheme(dark)
  }, [])

  const toggle = () => {
    setDark(prev => {
      const next = !prev
      applyTheme(next)
      localStorage.setItem('bs_theme', next ? 'dark' : 'light')
      return next
    })
  }

  return (
    <ThemeContext.Provider value={{ dark, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
