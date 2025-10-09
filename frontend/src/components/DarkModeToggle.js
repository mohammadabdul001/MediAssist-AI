import React, { useContext } from 'react';
import { useAppContext } from '../context/AppContext';

const DarkModeToggle = () => {
  const { darkMode, toggleDarkMode } = useAppContext();

  return (
    <button onClick={toggleDarkMode} className="dark-mode-toggle">
      {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
    </button>
  );
};

export default DarkModeToggle;