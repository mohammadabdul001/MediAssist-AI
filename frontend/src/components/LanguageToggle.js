import React, { useContext } from 'react';
import { useAppContext } from '../context/AppContext';

const LanguageToggle = () => {
  const { lang, setLang } = useAppContext();

  return (
    <div className="lang-toggle">
      {['en', 'hi', 'es'].map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          className={lang === l ? 'active' : ''}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
};

export default LanguageToggle;