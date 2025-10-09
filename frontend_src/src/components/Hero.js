import React, { useContext, useState } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const Hero = () => {
  const { darkMode, t } = useAppContext();
  const [showChat, setShowChat] = useState(false);

  const scrollToFeatures = () => {
    const featuresSection = document.querySelector('.features-section');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className={`hero ${darkMode ? 'dark' : ''}`}>
      <div className="hero-content">
        <motion.h1
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {t.heroTitle}
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="hero-subtitle"
        >
          {t.heroSubtitle}
        </motion.p>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="hero-buttons"
        >
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="cta-btn primary"
            onClick={() => setShowChat(true)}
          >
            {t.tryNow}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="cta-btn secondary"
            onClick={scrollToFeatures}
          >
            Explore Features
          </motion.button>
        </motion.div>
      </div>

      {showChat && (
        <div className="chat-overlay">
          <div className="chat-container">
            <div className="chat-header">
              <h3>AI Health Assistant</h3>
              <button onClick={() => setShowChat(false)} className="close-btn">×</button>
            </div>
            <div className="chat-body">
              <div className="message ai">Hello! How are you feeling today?</div>
            </div>
            <div className="chat-footer">
              <input type="text" placeholder="Describe your symptoms..." />
              <button>Send</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default Hero;