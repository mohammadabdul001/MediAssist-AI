import React, { useState, useContext, useRef, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';
import {
  HomeIcon,
  SymptomAnalysisIcon,
  HealthRecordsIcon,
  AppointmentsIcon,
  MedicationIcon,
  LabTestsIcon,
  AnalyticsIcon,
  EmergencyIcon,
  TelemedicineIcon,
  RecommendationsIcon
} from './Icons';

const PatientDashboard = ({ onLogout }) => {
  const { auth, t } = useAppContext();
  const [currentFeature, setCurrentFeature] = useState('home');
  const [showChat, setShowChat] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [profileImage, setProfileImage] = useState(null);
  const [notifications, setNotifications] = useState(3);
  const [userStatus, setUserStatus] = useState('online');
  const fileInputRef = useRef(null);
  const profileRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setShowProfile(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const features = [
    { id: 'home', name: 'Home', icon: HomeIcon, component: 'Hero' },
    { id: 'symptom-analysis', name: 'Symptom Analysis', icon: SymptomAnalysisIcon, component: 'SymptomAnalysis' },
    { id: 'health-records', name: 'Health Records', icon: HealthRecordsIcon, component: 'HealthRecords' },
    { id: 'appointments', name: 'Appointments', icon: AppointmentsIcon, component: 'AppointmentScheduling' },
    { id: 'medication', name: 'Medication', icon: MedicationIcon, component: 'MedicationTracker' },
    { id: 'lab-tests', name: 'Lab Tests', icon: LabTestsIcon, component: 'LabTestManagement' },
    { id: 'analytics', name: 'Analytics', icon: AnalyticsIcon, component: 'HealthAnalytics' },
    { id: 'emergency', name: 'Emergency SOS', icon: EmergencyIcon, component: 'EmergencySOS' },
    { id: 'telemedicine', name: 'Telemedicine', icon: TelemedicineIcon, component: 'Telemedicine' },
    { id: 'recommendations', name: 'Recommendations', icon: RecommendationsIcon, component: 'HealthRecommendations' }
  ];
  const renderFeature = () => {
    switch (currentFeature) {
      case 'home':
        return (
          <div className="patient-home">
            <div className="welcome-section">
              <motion.h1
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="welcome-title"
              >
                Welcome Back, {auth.name}! 👋
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="welcome-subtitle"
              >
                Ready to take control of your health journey? We're here to support you every step of the way with personalized care and advanced medical insights.
              </motion.p>
            </div>

            <div className="quick-actions">
              <motion.h2
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                Quick Actions
              </motion.h2>
              <div className="quick-actions-grid">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="quick-action-card primary"
                  onClick={() => setCurrentFeature('symptom-analysis')}
                >
                  <div className="action-icon">🔍</div>
                  <h3>Symptom Analysis</h3>
                  <p>Describe your symptoms and get AI-powered health insights and recommendations</p>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="quick-action-card secondary"
                  onClick={() => setCurrentFeature('appointments')}
                >
                  <div className="action-icon">📅</div>
                  <h3>Appointments</h3>
                  <p>Schedule, manage, and track your medical appointments with healthcare providers</p>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="quick-action-card emergency"
                  onClick={() => setCurrentFeature('emergency')}
                >
                  <div className="action-icon">🚨</div>
                  <h3>Emergency SOS</h3>
                  <p>Immediate medical assistance and emergency contact access when you need it most</p>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="quick-action-card chat"
                  onClick={() => setShowChat(true)}
                >
                  <div className="action-icon">💬</div>
                  <h3>AI Health Assistant</h3>
                  <p>24/7 AI-powered health guidance and medical information at your fingertips</p>
                </motion.button>
              </div>
            </div>

            <div className="health-summary">
              <motion.h2
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.6 }}
              >
                Health Overview
              </motion.h2>
              <div className="health-stats-grid">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 0.8 }}
                  className="health-stat-card"
                >
                  <div className="stat-icon">❤️</div>
                  <div className="stat-content">
                    <h3>Heart Rate</h3>
                    <p className="stat-value">72 BPM</p>
                    <p className="stat-status normal">Normal</p>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 0.9 }}
                  className="health-stat-card"
                >
                  <div className="stat-icon">🩸</div>
                  <div className="stat-content">
                    <h3>Blood Pressure</h3>
                    <p className="stat-value">120/80</p>
                    <p className="stat-status normal">Normal</p>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 1.0 }}
                  className="health-stat-card"
                >
                  <div className="stat-icon">🌡️</div>
                  <div className="stat-content">
                    <h3>Temperature</h3>
                    <p className="stat-value">98.6°F</p>
                    <p className="stat-status normal">Normal</p>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 1.1 }}
                  className="health-stat-card"
                >
                  <div className="stat-icon">💊</div>
                  <div className="stat-content">
                    <h3>Medications</h3>
                    <p className="stat-value">3 Active</p>
                    <p className="stat-status warning">2 Due Today</p>
                  </div>
                </motion.div>
              </div>
            </div>

            <div className="recent-activity">
              <motion.h2
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6, delay: 1.2 }}
              >
                Recent Medical Activity
              </motion.h2>
              <div className="activity-list">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 1.4 }}
                  className="activity-item"
                >
                  <div className="activity-icon">📋</div>
                  <div className="activity-content">
                    <h4>Appointment Scheduled</h4>
                    <p>Dr. Johnson - Cardiology - Tomorrow 2:00 PM</p>
                    <span className="activity-time">2 hours ago</span>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 1.5 }}
                  className="activity-item"
                >
                  <div className="activity-icon">🧪</div>
                  <div className="activity-content">
                    <h4>Lab Results Ready</h4>
                    <p>Blood Test Results Available</p>
                    <span className="activity-time">1 day ago</span>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 1.6 }}
                  className="activity-item"
                >
                  <div className="activity-icon">💊</div>
                  <div className="activity-content">
                    <h4>Medication Refilled</h4>
                    <p>Aspirin 100mg - 30 tablets</p>
                    <span className="activity-time">3 days ago</span>
                  </div>
                </motion.div>
              </div>
            </div>
          </div>
        );
      default:
        return <div className="feature-placeholder">Feature content will be loaded here</div>;
    }
  };

  return (
    <div className="patient-dashboard">
      <nav className="patient-navigation">
        <div className="nav-container">
          <div className="nav-brand">
            <h2>🏥 MediAssist AI</h2>
          </div>
          
          <div className="nav-features">
            {features.map(feature => {
              const IconComponent = feature.icon;
              return (
                <motion.button
                  key={feature.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`nav-feature ${currentFeature === feature.id ? 'active' : ''}`}
                  onClick={() => setCurrentFeature(feature.id)}
                >
                  <span className="feature-icon">
                    <IconComponent size={20} />
                  </span>
                  <span className="feature-name">{feature.name}</span>
                </motion.button>
              );
            })}
          </div>
          
          <div className="nav-user">
            <div className="user-profile-section" ref={profileRef}>
              <motion.div 
                className="user-info"
                onClick={() => setShowProfile(!showProfile)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="user-avatar">
                  {profileImage ? (
                    <img src={profileImage} alt="Profile" />
                  ) : (
                    auth.name.charAt(0).toUpperCase()
                  )}
                  <div className={`status-indicator ${userStatus}`}></div>
                </div>
                <div className="user-details">
                  <span className="user-name">{auth.name}</span>
                  <span className="user-role">Patient</span>
                </div>
                <div className="profile-dropdown-arrow">
                  ▼
                </div>
              </motion.div>
              
              {showProfile && (
                <motion.div 
                  className="profile-dropdown"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <div className="profile-header">
                    <div className="profile-avatar-large">
                      {profileImage ? (
                        <img src={profileImage} alt="Profile" />
                      ) : (
                        auth.name.charAt(0).toUpperCase()
                      )}
                    </div>
                    <div className="profile-info">
                      <h3>{auth.name}</h3>
                      <p>Patient</p>
                      <span className="user-email">{auth.email}</span>
                    </div>
                  </div>
                  
                  <div className="profile-actions">
                    <button 
                      className="profile-action-btn"
                      onClick={() => fileInputRef.current.click()}
                    >
                      <span className="action-icon">📷</span>
                      Change Photo
                    </button>
                    <button className="profile-action-btn">
                      <span className="action-icon">⚙️</span>
                      Settings
                    </button>
                    <button 
                      className="profile-action-btn"
                      onClick={() => {
                        const statuses = ['online', 'away', 'busy'];
                        const currentIndex = statuses.indexOf(userStatus);
                        const nextIndex = (currentIndex + 1) % statuses.length;
                        setUserStatus(statuses[nextIndex]);
                      }}
                    >
                      <span className="action-icon">🔒</span>
                      Privacy
                      <span className="status-text">{userStatus}</span>
                    </button>
                    <button className="profile-action-btn">
                      <span className="action-icon">📊</span>
                      Health Stats
                    </button>
                    <button className="profile-action-btn">
                      <span className="action-icon">📋</span>
                      Medical History
                    </button>
                    <button className="profile-action-btn">
                      <span className="action-icon">💊</span>
                      Medications
                    </button>
                    <button className="profile-action-btn">
                      <span className="action-icon">📅</span>
                      Appointments
                    </button>
                    <button 
                      className="profile-action-btn"
                      onClick={() => setNotifications(0)}
                    >
                      <span className="action-icon">🔔</span>
                      Notifications
                      {notifications > 0 && (
                        <span className="notification-badge">{notifications}</span>
                      )}
                    </button>
                    <button className="profile-action-btn">
                      <span className="action-icon">❓</span>
                      Help & Support
                    </button>
                    <button 
                      className="profile-action-btn logout-action"
                      onClick={onLogout}
                    >
                      <span className="action-icon">🚪</span>
                      Logout
                    </button>
                  </div>
                </motion.div>
              )}
              
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files[0];
                  if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => setProfileImage(e.target.result);
                    reader.readAsDataURL(file);
                  }
                }}
              />
            </div>
          </div>
        </div>
      </nav>

      <main className="patient-content">
        {renderFeature()}
      </main>

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
    </div>
  );
};

export default PatientDashboard; 