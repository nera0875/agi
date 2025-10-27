import { create } from 'zustand'

interface User {
  id: string
  name: string
  email: string
  avatar?: string
}

interface AppState {
  // Navigation
  activeSection: 'calendar' | 'timeblocks' | 'chat' | 'settings'
  sidebarOpen: boolean
  
  // Thème
  theme: 'light' | 'dark' | 'system'
  
  // Utilisateur
  user: User | null
  isAuthenticated: boolean
  
  // Vue
  viewMode: 'day' | 'week' | 'month'
  
  // Actions
  setActiveSection: (section: AppState['activeSection']) => void
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setTheme: (theme: AppState['theme']) => void
  setUser: (user: User | null) => void
  setAuthenticated: (authenticated: boolean) => void
  setViewMode: (mode: AppState['viewMode']) => void
  
  // Actions métier
  login: (user: User) => void
  logout: () => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // État initial
  activeSection: 'calendar',
  sidebarOpen: true,
  theme: 'system',
  user: null,
  isAuthenticated: false,
  viewMode: 'day',

  // Actions de base
  setActiveSection: (section) => set({ activeSection: section }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
  setUser: (user) => set({ user }),
  setAuthenticated: (authenticated) => set({ isAuthenticated: authenticated }),
  setViewMode: (mode) => set({ viewMode: mode }),

  // Actions métier
  login: (user) => set({ 
    user, 
    isAuthenticated: true 
  }),
  
  logout: () => set({ 
    user: null, 
    isAuthenticated: false,
    activeSection: 'calendar' // Retour à l'accueil
  })
}))

// Hook pour les préférences utilisateur
export const useUserPreferences = () => {
  const { theme, viewMode, setTheme, setViewMode } = useAppStore()
  
  return {
    theme,
    viewMode,
    setTheme,
    setViewMode,
    
    // Sauvegarde des préférences (localStorage)
    savePreferences: () => {
      const preferences = { theme, viewMode }
      localStorage.setItem('agi-preferences', JSON.stringify(preferences))
    },
    
    // Chargement des préférences
    loadPreferences: () => {
      try {
        const saved = localStorage.getItem('agi-preferences')
        if (saved) {
          const preferences = JSON.parse(saved)
          if (preferences.theme) setTheme(preferences.theme)
          if (preferences.viewMode) setViewMode(preferences.viewMode)
        }
      } catch (error) {
        console.warn('Erreur lors du chargement des préférences:', error)
      }
    }
  }
}

// Hook pour la navigation
export const useNavigation = () => {
  const { activeSection, setActiveSection, sidebarOpen, setSidebarOpen } = useAppStore()
  
  return {
    activeSection,
    sidebarOpen,
    navigate: (section: AppState['activeSection']) => {
      setActiveSection(section)
      // Fermer la sidebar sur mobile après navigation
      if (window.innerWidth < 768) {
        setSidebarOpen(false)
      }
    },
    toggleSidebar: () => setSidebarOpen(!sidebarOpen)
  }
}