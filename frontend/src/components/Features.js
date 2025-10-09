import React, { useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const Features = () => {
  const { t } = useAppContext();

  const features = [
    {
      id: 'symptom-analysis',
      icon: '🔍',
      title: 'Symptom Analysis',
      description: 'AI-powered symptom checker with real-time analysis and preliminary diagnosis',
      color: '#2962ff'
    },
    {
      id: 'health-records',
      icon: '📋',
      title: 'Health Record Management',
      description: 'Secure digital storage and management of medical records and history',
      color: '#4caf50'
    },
    {
      id: 'appointments',
      icon: '📅',
      title: 'Appointment Scheduling',
      description: 'Easy booking and management of doctor appointments and consultations',
      color: '#ff9800'
    },
    {
      id: 'medication',
      icon: '💊',
      title: 'Medication Tracker',
      description: 'Track medications, dosages, and set reminders for timely intake',
      color: '#e91e63'
    },
    {
      id: 'lab-tests',
      icon: '🧪',
      title: 'Lab Test Management',
      description: 'Schedule, track, and receive lab test results with detailed analysis',
      color: '#9c27b0'
    },
    {
      id: 'analytics',
      icon: '📊',
      title: 'Health Analytics',
      description: 'Comprehensive health insights and trend analysis with visual reports',
      color: '#00bcd4'
    },
    {
      id: 'chatbot',
      icon: '🤖',
      title: 'Chatbot Assistance',
      description: '24/7 AI health assistant for instant medical guidance and support',
      color: '#607d8b'
    },
    {
      id: 'emergency',
      icon: '🚨',
      title: 'Emergency SOS Alert',
      description: 'Quick emergency alerts with location sharing and medical information',
      color: '#f44336'
    },
    {
      id: 'telemedicine',
      icon: '📹',
      title: 'Telemedicine Integration',
      description: 'Virtual consultations with healthcare providers from anywhere',
      color: '#3f51b5'
    },
    {
      id: 'recommendations',
      icon: '💡',
      title: 'Personalized Health Recommendations',
      description: 'AI-driven personalized health tips and lifestyle recommendations',
      color: '#8bc34a'
    },
    {
      id: 'multilang',
      icon: '🌐',
      title: 'Multi-Language Support',
      description: 'Access healthcare information in multiple languages for global reach',
      color: '#795548'
    }
  ];

  return (
    <section className="features-section">
      <div className="features-container">
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="features-title"
        >
          Comprehensive Healthcare Features
        </motion.h2>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="features-subtitle"
        >
          Everything you need for complete health management in one platform
        </motion.p>

        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={feature.id}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -5, scale: 1.02 }}
              className="feature-card"
              style={{ '--feature-color': feature.color }}
            >
              <div className="feature-icon" style={{ backgroundColor: feature.color }}>
                {feature.icon}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
              <button className="feature-btn">Learn More</button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
