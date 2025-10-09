import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const EmergencySOS = () => {
  const { t } = useAppContext();
  const [isEmergency, setIsEmergency] = useState(false);
  const [emergencyType, setEmergencyType] = useState('');
  const [location, setLocation] = useState('');
  const [medicalInfo, setMedicalInfo] = useState('');
  const [contacts, setContacts] = useState([
    { name: 'Emergency Services', number: '911', type: 'emergency' },
    { name: 'Dr. Sarah Johnson', number: '+1-555-0123', type: 'doctor' },
    { name: 'John Doe (Spouse)', number: '+1-555-0456', type: 'family' }
  ]);

  const [emergencyHistory, setEmergencyHistory] = useState([
    {
      id: 1,
      type: 'Medical Emergency',
      date: '2024-01-10',
      time: '14:30',
      location: 'Home',
      status: 'Resolved',
      description: 'Chest pain - called ambulance'
    }
  ]);

  const emergencyTypes = [
    'Medical Emergency',
    'Accident/Injury',
    'Heart Attack',
    'Stroke',
    'Severe Bleeding',
    'Difficulty Breathing',
    'Unconsciousness',
    'Other'
  ];

  const triggerEmergency = () => {
    setIsEmergency(true);
    // Simulate emergency alert
    setTimeout(() => {
      alert('Emergency alert sent! Emergency services and contacts have been notified.');
      setIsEmergency(false);
      
      // Add to history
      const newEmergency = {
        id: emergencyHistory.length + 1,
        type: emergencyType || 'Emergency',
        date: new Date().toISOString().split('T')[0],
        time: new Date().toLocaleTimeString(),
        location: location || 'Current Location',
        status: 'Active',
        description: medicalInfo || 'Emergency triggered'
      };
      setEmergencyHistory([newEmergency, ...emergencyHistory]);
    }, 2000);
  };

  const addContact = () => {
    const newContact = {
      name: prompt('Enter contact name:'),
      number: prompt('Enter contact number:'),
      type: 'family'
    };
    if (newContact.name && newContact.number) {
      setContacts([...contacts, newContact]);
    }
  };

  const removeContact = (index) => {
    setContacts(contacts.filter((_, i) => i !== index));
  };

  return (
    <div className="emergency-sos">
      <div className="sos-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="sos-title"
        >
          🚨 Emergency SOS Alert
        </motion.h2>

        <div className="sos-content">
          <div className="emergency-panel">
            <div className="emergency-header">
              <h3>Emergency Alert System</h3>
              <p>Quick access to emergency services and medical contacts</p>
            </div>

            <div className="emergency-actions">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`sos-button ${isEmergency ? 'active' : ''}`}
                onClick={triggerEmergency}
                disabled={isEmergency}
              >
                {isEmergency ? '🚨 ALERTING...' : '🚨 SOS EMERGENCY'}
              </motion.button>

              <div className="emergency-info">
                <div className="info-item">
                  <label>Emergency Type:</label>
                  <select
                    value={emergencyType}
                    onChange={(e) => setEmergencyType(e.target.value)}
                  >
                    <option value="">Select type...</option>
                    {emergencyTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div className="info-item">
                  <label>Location:</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Current location or address"
                  />
                </div>

                <div className="info-item">
                  <label>Medical Information:</label>
                  <textarea
                    value={medicalInfo}
                    onChange={(e) => setMedicalInfo(e.target.value)}
                    placeholder="Brief description of emergency..."
                    rows="3"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="contacts-section">
            <div className="section-header">
              <h3>Emergency Contacts</h3>
              <button onClick={addContact} className="btn-add">+ Add Contact</button>
            </div>

            <div className="contacts-list">
              {contacts.map((contact, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="contact-item"
                >
                  <div className="contact-info">
                    <span className="contact-name">{contact.name}</span>
                    <span className="contact-number">{contact.number}</span>
                    <span className={`contact-type ${contact.type}`}>
                      {contact.type === 'emergency' ? '🚨' : contact.type === 'doctor' ? '👨‍⚕️' : '👨‍👩‍👧‍👦'}
                      {contact.type}
                    </span>
                  </div>
                  <div className="contact-actions">
                    <button className="btn-call">📞 Call</button>
                    {contact.type !== 'emergency' && (
                      <button 
                        onClick={() => removeContact(index)}
                        className="btn-remove"
                      >
                        🗑️
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="medical-info-section">
            <h3>Medical Information</h3>
            <div className="medical-cards">
              <div className="medical-card">
                <h4>Allergies</h4>
                <p>Penicillin, Peanuts, Latex</p>
              </div>
              <div className="medical-card">
                <h4>Blood Type</h4>
                <p>O+</p>
              </div>
              <div className="medical-card">
                <h4>Current Medications</h4>
                <p>Aspirin 100mg daily</p>
              </div>
              <div className="medical-card">
                <h4>Emergency Contact</h4>
                <p>John Doe (Spouse) - +1-555-0456</p>
              </div>
            </div>
          </div>

          <div className="emergency-history">
            <h3>Emergency History</h3>
            <div className="history-list">
              {emergencyHistory.map(emergency => (
                <motion.div
                  key={emergency.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="history-item"
                >
                  <div className="history-header">
                    <span className="emergency-type">{emergency.type}</span>
                    <span className={`emergency-status ${emergency.status.toLowerCase()}`}>
                      {emergency.status}
                    </span>
                  </div>
                  <div className="history-details">
                    <p><strong>Date:</strong> {emergency.date} at {emergency.time}</p>
                    <p><strong>Location:</strong> {emergency.location}</p>
                    <p><strong>Description:</strong> {emergency.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="safety-tips">
            <h3>Emergency Safety Tips</h3>
            <div className="tips-grid">
              <div className="tip-card">
                <h4>🚨 Stay Calm</h4>
                <p>Take deep breaths and try to remain calm during emergencies</p>
              </div>
              <div className="tip-card">
                <h4>📞 Call 911</h4>
                <p>Immediately call emergency services for life-threatening situations</p>
              </div>
              <div className="tip-card">
                <h4>📍 Know Your Location</h4>
                <p>Be prepared to provide your exact location to emergency responders</p>
              </div>
              <div className="tip-card">
                <h4>💊 Medical Info</h4>
                <p>Keep a list of medications and allergies readily available</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencySOS; 