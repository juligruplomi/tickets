import React, { useState, useContext, createContext, useEffect } from 'react';
import { 
  Sun, Moon, Globe, User, Settings, Plus, Eye, CreditCard, 
  Users, BarChart3, Camera, MapPin, Car, Utensils, 
  Check, X, Clock, Euro, FileText, LogOut, Menu, 
  ChevronDown, Search, Filter, Upload, Edit, Trash2,
  Bell, DollarSign, TrendingUp, Calendar, Download
} from 'lucide-react';

// Context para tema e idioma
const AppContext = createContext();

// Traducciones
const translations = {
  en: {
    // Navigation
    dashboard: "Dashboard",
    createTicket: "Create Ticket",
    myTickets: "My Tickets",
    manageTickets: "Manage Tickets",
    accounting: "Accounting",
    users: "Users",
    roles: "Roles",
    settings: "Settings",
    logout: "Logout",
    
    // Dashboard
    goodMorning: "Good morning",
    goodAfternoon: "Good afternoon", 
    goodEvening: "Good evening",
    pendingPayment: "Pending Payment",
    totalTickets: "Total Tickets",
    paidPercentage: "Paid",
    recentTickets: "Recent Tickets",
    
    // Ticket types
    meal: "Meal",
    parking: "Parking", 
    fuel: "Fuel",
    
    // Ticket form
    newTicket: "New Ticket",
    description: "Description",
    project: "Project",
    amount: "Amount",
    kilometers: "Kilometers", 
    pricePerKm: "Price per km",
    attachPhoto: "Attach Photo",
    photoRequired: "Photo required",
    photoOptional: "Photo optional",
    calculate: "Calculate",
    save: "Save",
    cancel: "Cancel",
    
    // Status
    pending: "Pending",
    validated: "Validated", 
    paid: "Paid",
    rejected: "Rejected",
    
    // Actions
    validate: "Validate",
    reject: "Reject", 
    pay: "Pay",
    edit: "Edit",
    delete: "Delete",
    view: "View",
    
    // Settings
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    language: "Language",
    notifications: "Notifications",
    currency: "Currency",
    
    // Common
    total: "Total",
    date: "Date",
    user: "User",
    actions: "Actions",
    search: "Search",
    filter: "Filter",
    export: "Export",
    loading: "Loading...",
    success: "Success",
    error: "Error"
  },
  es: {
    // Navigation
    dashboard: "Panel",
    createTicket: "Crear Ticket",
    myTickets: "Mis Tickets", 
    manageTickets: "Gestionar Tickets",
    accounting: "Contabilidad",
    users: "Usuarios",
    roles: "Roles", 
    settings: "Configuración",
    logout: "Cerrar Sesión",
    
    // Dashboard
    goodMorning: "Buenos días",
    goodAfternoon: "Buenas tardes",
    goodEvening: "Buenas noches", 
    pendingPayment: "Pendiente de Pago",
    totalTickets: "Total Tickets",
    paidPercentage: "Pagado",
    recentTickets: "Tickets Recientes",
    
    // Ticket types
    meal: "Dieta",
    parking: "Parking",
    fuel: "Gasolina",
    
    // Ticket form
    newTicket: "Nuevo Ticket", 
    description: "Descripción",
    project: "Proyecto",
    amount: "Importe",
    kilometers: "Kilómetros",
    pricePerKm: "Precio por km", 
    attachPhoto: "Adjuntar Foto",
    photoRequired: "Foto obligatoria",
    photoOptional: "Foto opcional",
    calculate: "Calcular",
    save: "Guardar",
    cancel: "Cancelar",
    
    // Status
    pending: "Pendiente",
    validated: "Validado",
    paid: "Pagado", 
    rejected: "Rechazado",
    
    // Actions
    validate: "Validar",
    reject: "Rechazar",
    pay: "Pagar", 
    edit: "Editar",
    delete: "Eliminar",
    view: "Ver",
    
    // Settings
    theme: "Tema",
    light: "Claro", 
    dark: "Oscuro",
    language: "Idioma",
    notifications: "Notificaciones",
    currency: "Moneda",
    
    // Common
    total: "Total",
    date: "Fecha",
    user: "Usuario", 
    actions: "Acciones",
    search: "Buscar",
    filter: "Filtrar",
    export: "Exportar",
    loading: "Cargando...",
    success: "Éxito", 
    error: "Error"
  },
  ca: {
    // Navigation
    dashboard: "Panell",
    createTicket: "Crear Tiquet", 
    myTickets: "Els Meus Tiquets",
    manageTickets: "Gestionar Tiquets",
    accounting: "Comptabilitat",
    users: "Usuaris",
    roles: "Rols",
    settings: "Configuració", 
    logout: "Tancar Sessió",
    
    // Dashboard
    goodMorning: "Bon dia",
    goodAfternoon: "Bona tarda",
    goodEvening: "Bon vespre",
    pendingPayment: "Pendent de Pagament", 
    totalTickets: "Total Tiquets",
    paidPercentage: "Pagat",
    recentTickets: "Tiquets Recents",
    
    // Ticket types
    meal: "Dieta",
    parking: "Pàrquing", 
    fuel: "Gasolina",
    
    // Ticket form
    newTicket: "Nou Tiquet",
    description: "Descripció",
    project: "Projecte",
    amount: "Import", 
    kilometers: "Quilòmetres",
    pricePerKm: "Preu per km",
    attachPhoto: "Adjuntar Foto",
    photoRequired: "Foto obligatòria",
    photoOptional: "Foto opcional",
    calculate: "Calcular", 
    save: "Guardar",
    cancel: "Cancel·lar",
    
    // Status
    pending: "Pendent",
    validated: "Validat",
    paid: "Pagat",
    rejected: "Rebutjat",
    
    // Actions
    validate: "Validar", 
    reject: "Rebutjar",
    pay: "Pagar",
    edit: "Editar",
    delete: "Eliminar",
    view: "Veure",
    
    // Settings
    theme: "Tema",
    light: "Clar", 
    dark: "Fosc",
    language: "Idioma",
    notifications: "Notificacions",
    currency: "Moneda",
    
    // Common
    total: "Total",
    date: "Data", 
    user: "Usuari",
    actions: "Accions",
    search: "Cercar",
    filter: "Filtrar",
    export: "Exportar",
    loading: "Carregant...",
    success: "Èxit",
    error: "Error"
  },
  fr: {
    // Navigation
    dashboard: "Tableau de Bord",
    createTicket: "Créer Ticket",
    myTickets: "Mes Tickets", 
    manageTickets: "Gérer Tickets",
    accounting: "Comptabilité",
    users: "Utilisateurs",
    roles: "Rôles",
    settings: "Paramètres",
    logout: "Déconnexion",
    
    // Dashboard
    goodMorning: "Bonjour",
    goodAfternoon: "Bon après-midi", 
    goodEvening: "Bonsoir",
    pendingPayment: "En Attente de Paiement",
    totalTickets: "Total Tickets",
    paidPercentage: "Payé",
    recentTickets: "Tickets Récents",
    
    // Ticket types
    meal: "Repas", 
    parking: "Parking",
    fuel: "Carburant",
    
    // Ticket form
    newTicket: "Nouveau Ticket",
    description: "Description",
    project: "Projet",
    amount: "Montant",
    kilometers: "Kilomètres", 
    pricePerKm: "Prix par km",
    attachPhoto: "Joindre Photo",
    photoRequired: "Photo obligatoire",
    photoOptional: "Photo optionnelle",
    calculate: "Calculer",
    save: "Enregistrer",
    cancel: "Annuler",
    
    // Status
    pending: "En Attente", 
    validated: "Validé",
    paid: "Payé",
    rejected: "Rejeté",
    
    // Actions
    validate: "Valider",
    reject: "Rejeter",
    pay: "Payer",
    edit: "Modifier", 
    delete: "Supprimer",
    view: "Voir",
    
    // Settings
    theme: "Thème",
    light: "Clair",
    dark: "Sombre",
    language: "Langue",
    notifications: "Notifications", 
    currency: "Devise",
    
    // Common
    total: "Total",
    date: "Date",
    user: "Utilisateur",
    actions: "Actions",
    search: "Rechercher",
    filter: "Filtrer", 
    export: "Exporter",
    loading: "Chargement...",
    success: "Succès",
    error: "Erreur"
  },
  de: {
    // Navigation
    dashboard: "Dashboard",
    createTicket: "Ticket Erstellen", 
    myTickets: "Meine Tickets",
    manageTickets: "Tickets Verwalten",
    accounting: "Buchhaltung",
    users: "Benutzer",
    roles: "Rollen",
    settings: "Einstellungen",
    logout: "Abmelden",
    
    // Dashboard
    goodMorning: "Guten Morgen", 
    goodAfternoon: "Guten Tag",
    goodEvening: "Guten Abend",
    pendingPayment: "Zahlung Ausstehend",
    totalTickets: "Gesamt Tickets",
    paidPercentage: "Bezahlt",
    recentTickets: "Aktuelle Tickets",
    
    // Ticket types
    meal: "Verpflegung", 
    parking: "Parkplatz",
    fuel: "Kraftstoff",
    
    // Ticket form
    newTicket: "Neues Ticket",
    description: "Beschreibung",
    project: "Projekt",
    amount: "Betrag",
    kilometers: "Kilometer", 
    pricePerKm: "Preis pro km",
    attachPhoto: "Foto Anhängen",
    photoRequired: "Foto erforderlich",
    photoOptional: "Foto optional",
    calculate: "Berechnen",
    save: "Speichern",
    cancel: "Abbrechen",
    
    // Status
    pending: "Ausstehend", 
    validated: "Validiert",
    paid: "Bezahlt",
    rejected: "Abgelehnt",
    
    // Actions
    validate: "Validieren",
    reject: "Ablehnen",
    pay: "Bezahlen",
    edit: "Bearbeiten", 
    delete: "Löschen",
    view: "Ansehen",
    
    // Settings
    theme: "Theme",
    light: "Hell",
    dark: "Dunkel",
    language: "Sprache",
    notifications: "Benachrichtigungen", 
    currency: "Währung",
    
    // Common
    total: "Gesamt",
    date: "Datum",
    user: "Benutzer",
    actions: "Aktionen",
    search: "Suchen",
    filter: "Filtern", 
    export: "Exportieren",
    loading: "Wird geladen...",
    success: "Erfolgreich",
    error: "Fehler"
  }
};

// Hook para traducciones
const useTranslation = () => {
  const { language } = useContext(AppContext);
  const t = (key) => translations[language]?.[key] || key;
  return { t };
};

// Componente principal
const ExpenseManagementApp = () => {
  const [theme, setTheme] = useState('light');
  const [language, setLanguage] = useState('es');
  const [currentUser, setCurrentUser] = useState({
    email: 'marc@gruplomi.com',
    role: 'operari', // operari, supervisor, comptabilitat, admin
    name: 'Marc',
    pendingAmount: 1247.50
  });
  const [currentView, setCurrentView] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Datos de ejemplo
  const [tickets, setTickets] = useState([
    {
      id: 1,
      date: '2024-09-15',
      tipus: 'Dieta',
      description: 'Comida con cliente importante',
      project: 'Proyecto Alpha',
      total: 45.50,
      status: 'validated',
      createdBy: 'marc@gruplomi.com',
      image: true
    },
    {
      id: 2,
      date: '2024-09-14', 
      tipus: 'Parking',
      description: 'Parking oficina central',
      project: 'Gestión',
      total: 12.00,
      status: 'paid',
      createdBy: 'marc@gruplomi.com',
      image: true
    },
    {
      id: 3,
      date: '2024-09-14',
      tipus: 'Gasolina',
      description: 'Viaje a Barcelona',
      project: 'Proyecto Beta', 
      total: 68.40,
      kilometers: 120,
      pricePerKm: 0.57,
      status: 'pending',
      createdBy: 'marc@gruplomi.com'
    }
  ]);

  const contextValue = {
    theme, setTheme,
    language, setLanguage, 
    currentUser, setCurrentUser,
    currentView, setCurrentView,
    tickets, setTickets
  };

  return (
    <AppContext.Provider value={contextValue}>
      <div className={`min-h-screen transition-all duration-300 ${
        theme === 'dark' 
          ? 'bg-black text-white' 
          : 'bg-gray-50 text-gray-900'
      }`}>
        <Header isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />
        <div className="flex">
          <Sidebar isMobileMenuOpen={isMobileMenuOpen} />
          <MainContent />
        </div>
      </div>
    </AppContext.Provider>
  );
};

// Header Component
const Header = ({ isMobileMenuOpen, setIsMobileMenuOpen }) => {
  const { theme, setTheme, language, setLanguage, currentUser } = useContext(AppContext);
  const { t } = useTranslation();

  const languages = [
    { code: 'en', flag: '🇬🇧', name: 'English' },
    { code: 'es', flag: '🇪🇸', name: 'Español' },
    { code: 'ca', flag: '🇨🇹', name: 'Català' },
    { code: 'fr', flag: '🇫🇷', name: 'Français' },
    { code: 'de', flag: '🇩🇪', name: 'Deutsch' }
  ];

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('goodMorning');
    if (hour < 18) return t('goodAfternoon');
    return t('goodEvening');
  };

  return (
    <header className={`sticky top-0 z-50 transition-all duration-300 backdrop-blur-xl ${
      theme === 'dark'
        ? 'bg-black/80 border-gray-800' 
        : 'bg-white/80 border-gray-200'
    } border-b`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y menú móvil */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                theme === 'dark' ? 'bg-blue-600' : 'bg-blue-500'
              }`}>
                <Euro size={16} className="text-white" />
              </div>
              <h1 className="text-xl font-semibold">GestióGastos</h1>
            </div>
          </div>

          {/* Saludo */}
          <div className="hidden md:block">
            <span className="text-sm opacity-75">
              {getGreeting()}, {currentUser.name}
            </span>
          </div>

          {/* Controles del header */}
          <div className="flex items-center space-x-3">
            {/* Selector de idioma */}
            <div className="relative group">
              <button className={`p-2 rounded-lg transition-all duration-200 ${
                theme === 'dark' 
                  ? 'hover:bg-gray-800 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
                <Globe size={18} />
              </button>
              <div className={`absolute right-0 top-12 min-w-48 rounded-xl shadow-lg transition-all duration-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible ${
                theme === 'dark'
                  ? 'bg-gray-900 border border-gray-700'
                  : 'bg-white border border-gray-200'
              }`}>
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setLanguage(lang.code)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 text-sm transition-colors first:rounded-t-xl last:rounded-b-xl ${
                      language === lang.code
                        ? theme === 'dark' ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                        : theme === 'dark' ? 'hover:bg-gray-800' : 'hover:bg-gray-50'
                    }`}
                  >
                    <span>{lang.flag}</span>
                    <span>{lang.name}</span>
                    {language === lang.code && <Check size={14} />}
                  </button>
                ))}
              </div>
            </div>

            {/* Toggle tema */}
            <button
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              className={`p-2 rounded-lg transition-all duration-200 ${
                theme === 'dark' 
                  ? 'hover:bg-gray-800 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
            >
              {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
            </button>

            {/* Notificaciones */}
            <button className={`p-2 rounded-lg transition-all duration-200 relative ${
              theme === 'dark' 
                ? 'hover:bg-gray-800 text-gray-300 hover:text-white' 
                : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
            }`}>
              <Bell size={18} />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
            </button>

            {/* Avatar usuario */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-gray-200 text-gray-700'
            }`}>
              {currentUser.name[0]}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

// Sidebar Component
const Sidebar = ({ isMobileMenuOpen }) => {
  const { theme, currentView, setCurrentView, currentUser } = useContext(AppContext);
  const { t } = useTranslation();

  const menuItems = [
    { id: 'dashboard', label: t('dashboard'), icon: BarChart3, roles: ['operari', 'supervisor', 'comptabilitat', 'admin'] },
    { id: 'create-ticket', label: t('createTicket'), icon: Plus, roles: ['operari', 'supervisor', 'admin'] },
    { id: 'my-tickets', label: t('myTickets'), icon: FileText, roles: ['operari', 'supervisor', 'admin'] },
    { id: 'manage-tickets', label: t('manageTickets'), icon: Eye, roles: ['supervisor', 'comptabilitat', 'admin'] },
    { id: 'accounting', label: t('accounting'), icon: CreditCard, roles: ['comptabilitat', 'admin'] },
    { id: 'users', label: t('users'), icon: Users, roles: ['admin'] },
    { id: 'roles', label: t('roles'), icon: Settings, roles: ['admin'] },
    { id: 'settings', label: t('settings'), icon: Settings, roles: ['admin'] }
  ];

  const visibleItems = menuItems.filter(item => item.roles.includes(currentUser.role));

  return (
    <>
      {/* Overlay móvil */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
      
      <aside className={`fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 z-50 transition-all duration-300 ${
        theme === 'dark'
          ? 'bg-gray-900 border-gray-800'
          : 'bg-white border-gray-200'
      } border-r transform lg:transform-none ${
        isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        <div className="p-6 space-y-2">
          {visibleItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setCurrentView(item.id);
                setIsMobileMenuOpen(false);
              }}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                currentView === item.id
                  ? theme === 'dark'
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-blue-500 text-white shadow-lg'
                  : theme === 'dark'
                    ? 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          ))}
          
          <div className="pt-6 mt-6 border-t border-gray-200 dark:border-gray-700">
            <button className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
              theme === 'dark'
                ? 'text-red-400 hover:bg-red-900/20 hover:text-red-300'
                : 'text-red-600 hover:bg-red-50 hover:text-red-700'
            }`}>
              <LogOut size={18} />
              <span>{t('logout')}</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

// Main Content Component
const MainContent = () => {
  const { currentView } = useContext(AppContext);

  return (
    <main className="flex-1 lg:ml-64 p-6">
      <div className="max-w-7xl mx-auto">
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'create-ticket' && <CreateTicket />}
        {currentView === 'my-tickets' && <MyTickets />}
        {currentView === 'manage-tickets' && <ManageTickets />}
        {currentView === 'accounting' && <Accounting />}
        {currentView === 'users' && <Users />}
        {currentView === 'roles' && <Roles />}
        {currentView === 'settings' && <SettingsPanel />}
      </div>
    </main>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { theme, currentUser, tickets } = useContext(AppContext);
  const { t } = useTranslation();

  const myTickets = tickets.filter(t => t.createdBy === currentUser.email);
  const pendingTickets = myTickets.filter(t => t.status === 'pending' || t.status === 'validated');
  const paidTickets = myTickets.filter(t => t.status === 'paid');
  const paidPercentage = myTickets.length > 0 ? Math.round((paidTickets.length / myTickets.length) * 100) : 0;

  const getStatusIcon = (status) => {
    const iconProps = { size: 16, className: "flex-shrink-0" };
    switch (status) {
      case 'pending': return <Clock {...iconProps} className="text-orange-500" />;
      case 'validated': return <Check {...iconProps} className="text-blue-500" />;
      case 'paid': return <Check {...iconProps} className="text-green-500" />;
      case 'rejected': return <X {...iconProps} className="text-red-500" />;
      default: return <Clock {...iconProps} />;
    }
  };

  const getTypeIcon = (tipus) => {
    switch (tipus) {
      case 'Dieta': return <Utensils size={16} className="text-green-600" />;
      case 'Parking': return <MapPin size={16} className="text-blue-600" />;
      case 'Gasolina': return <Car size={16} className="text-red-600" />;
      default: return <FileText size={16} />;
    }
  };

  return (
    <div className="space-y-8">
      {/* Saludo personalizado */}
      <div>
        <h1 className="text-3xl font-semibold mb-2">
          {new Date().getHours() < 12 ? t('goodMorning') : 
           new Date().getHours() < 18 ? t('goodAfternoon') : 
           t('goodEvening')}, {currentUser.name}
        </h1>
        <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          {new Date().toLocaleDateString()}
        </p>
      </div>

      {/* Tarjetas de estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pendiente de Pago */}
        <div className={`p-6 rounded-2xl transition-all duration-200 ${
          theme === 'dark'
            ? 'bg-gray-900 border border-gray-800'
            : 'bg-white border border-gray-200 shadow-sm'
        }`}>
          <div className="flex items-center space-x-3 mb-4">
            <div className={`p-2 rounded-xl ${
              theme === 'dark' ? 'bg-orange-600/20' : 'bg-orange-500/10'
            }`}>
              <Euro size={20} className="text-orange-500" />
            </div>
            <h3 className="font-medium">{t('pendingPayment')}</h3>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-semibold">
              €{currentUser.pendingAmount.toFixed(2)}
            </p>
            <div className="flex items-center space-x-2 text-sm opacity-75">
              <TrendingUp size={14} />
              <span>+€