import React, { createContext, useState, useEffect } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [darkMode, setDarkMode] = useState(false);
  const [lang, setLang] = useState('en');
  const [auth, setAuth] = useState(null);

  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode) setDarkMode(JSON.parse(savedMode));
    
    const savedAuth = localStorage.getItem('auth');
    if (savedAuth) setAuth(JSON.parse(savedAuth));
  }, []);

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  const translations = {
    en: {
      heroTitle: "Your AI-Powered Health Companion",
      heroSubtitle: "Real-Time Symptom Analysis. Trusted Care. Anytime, Anywhere.",
      tryNow: "Try Symptom Checker",
      adminLogin: "Admin Login",
      email: "Email",
      password: "Password",
      login: "Login",
      signUp: "Sign Up",
      noAccount: "Don't have an account?",
      haveAccount: "Already have an account?",
      invalidCreds: "Invalid credentials",
      adminDashboard: "Admin Dashboard",
      welcome: "Welcome",
      totalUsers: "Total Users",
      doctors: "Doctors",
      systemHealth: "System Health",
      logout: "Logout",
      accessDenied: "Access Denied",
      adminOnly: "Admins only can access this page.",
      goBack: "Go Back"
    },
    hi: {
      heroTitle: "आपका एआई-संचालित स्वास्थ्य साथी",
      heroSubtitle: "वास्तविक समय में लक्षण विश्लेषण। विश्वसनीय देखभाल। कभी भी, कहीं भी।",
      tryNow: "लक्षण चेकर आज़माएं",
      adminLogin: "एडमिन लॉगिन",
      email: "ईमेल",
      password: "पासवर्ड",
      login: "लॉगिन",
      signUp: "साइन अप",
      noAccount: "खाता नहीं है?",
      haveAccount: "पहले से ही खाता है?",
      invalidCreds: "अमान्य क्रेडेंशियल",
      adminDashboard: "एडमिन डैशबोर्ड",
      welcome: "स्वागत है",
      totalUsers: "कुल उपयोगकर्ता",
      doctors: "डॉक्टर",
      systemHealth: "सिस्टम स्वास्थ्य",
      logout: "लॉग आउट",
      accessDenied: "पहुंच निषेध",
      adminOnly: "केवल एडमिन इस पृष्ठ तक पहुंच सकते हैं।",
      goBack: "वापस जाएं"
    },
    es: {
      heroTitle: "Tu compañero de salud con IA",
      heroSubtitle: "Análisis de síntomas en tiempo real. Atención confiable. En cualquier momento, en cualquier lugar.",
      tryNow: "Prueba el comprobador de síntomas",
      adminLogin: "Inicio de sesión de administrador",
      email: "Correo electrónico",
      password: "Contraseña",
      login: "Iniciar sesión",
      signUp: "Registrarse",
      noAccount: "¿No tienes cuenta?",
      haveAccount: "¿Ya tienes cuenta?",
      invalidCreds: "Credenciales inválidas",
      adminDashboard: "Panel de administración",
      welcome: "Bienvenido",
      totalUsers: "Usuarios totales",
      doctors: "Doctores",
      systemHealth: "Salud del sistema",
      logout: "Cerrar sesión",
      accessDenied: "Acceso denegado",
      adminOnly: "Solo los administradores pueden acceder a esta página.",
      goBack: "Volver"
    }
  };

  const t = translations[lang] || translations.en;

  return (
    <AppContext.Provider value={{ 
      darkMode, 
      toggleDarkMode, 
      lang, 
      setLang, 
      auth, 
      setAuth, 
      t 
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = React.useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

export default AppContext;