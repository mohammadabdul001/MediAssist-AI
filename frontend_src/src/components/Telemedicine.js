import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const Telemedicine = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('consultations');
  const [isInCall, setIsInCall] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [consultationType, setConsultationType] = useState('');
  const [symptoms, setSymptoms] = useState('');

  const [consultations, setConsultations] = useState([
    {
      id: 1,
      doctor: 'Dr. Sarah Reddy',
      specialty: 'Cardiology',
      date: '2024-01-20',
      time: '10:00 AM',
      status: 'Scheduled',
      type: 'Follow-up',
      duration: '30 min',
      symptoms: 'Chest pain and shortness of breath'
    },
    {
      id: 2,
      doctor: 'Dr. Michael Chen',
      specialty: 'Dermatology',
      date: '2024-01-18',
      time: '2:30 PM',
      status: 'Completed',
      type: 'Initial Consultation',
      duration: '45 min',
      symptoms: 'Skin rash on arms'
    }
  ]);

  const availableDoctors = [
    {
      id: 1,
      name: 'Dr. Sarah Reddy',
      specialty: 'Cardiology',
      rating: 4.8,
      experience: '15 years',
      available: true,
      nextSlot: '10:00 AM',
      languages: ['English', 'Spanish'],
      image: '👩‍⚕️'
    },
    {
      id: 2,
      name: 'Dr. Michael Chen',
      specialty: 'Dermatology',
      rating: 4.9,
      experience: '12 years',
      available: true,
      nextSlot: '2:30 PM',
      languages: ['English', 'Mandarin'],
      image: '👨‍⚕️'
    },
    {
      id: 3,
      name: 'Dr. Emily Davis',
      specialty: 'Pediatrics',
      rating: 4.7,
      experience: '8 years',
      available: false,
      nextSlot: 'Tomorrow 9:00 AM',
      languages: ['English'],
      image: '👩‍⚕️'
    },
    {
      id: 4,
      name: 'Dr. Robert Wilson',
      specialty: 'Orthopedics',
      rating: 4.6,
      experience: '20 years',
      available: true,
      nextSlot: '3:00 PM',
      languages: ['English', 'French'],
      image: '👨‍⚕️'
    }
  ];

  const consultationTypes = [
    'Initial Consultation',
    'Follow-up',
    'Emergency Consultation',
    'Second Opinion',
    'Prescription Renewal',
    'Mental Health Session'
  ];

  const scheduleConsultation = () => {
    if (selectedDoctor && consultationType && symptoms) {
      const doctor = availableDoctors.find(d => d.id === selectedDoctor);
      const newConsultation = {
        id: consultations.length + 1,
        doctor: doctor.name,
        specialty: doctor.specialty,
        date: new Date().toISOString().split('T')[0],
        time: doctor.nextSlot,
        status: 'Scheduled',
        type: consultationType,
        duration: '30 min',
        symptoms: symptoms
      };
      setConsultations([...consultations, newConsultation]);
      setSelectedDoctor(null);
      setConsultationType('');
      setSymptoms('');
    }
  };

  const startCall = (consultationId) => {
    setIsInCall(true);
    // Simulate call interface
    setTimeout(() => {
      alert('Call ended');
      setIsInCall(false);
    }, 5000);
  };

  return (
    <div className="telemedicine">
      <div className="telemedicine-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="telemedicine-title"
        >
          📹 Telemedicine Integration
        </motion.h2>

        <div className="telemedicine-tabs">
          <button
            className={`tab ${activeTab === 'consultations' ? 'active' : ''}`}
            onClick={() => setActiveTab('consultations')}
          >
            My Consultations
          </button>
          <button
            className={`tab ${activeTab === 'schedule' ? 'active' : ''}`}
            onClick={() => setActiveTab('schedule')}
          >
            Schedule Consultation
          </button>
          <button
            className={`tab ${activeTab === 'doctors' ? 'active' : ''}`}
            onClick={() => setActiveTab('doctors')}
          >
            Available Doctors
          </button>
        </div>

        <div className="telemedicine-content">
          {activeTab === 'consultations' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="consultations-list"
            >
              <h3>My Telemedicine Consultations</h3>
              
              {consultations.length === 0 ? (
                <p className="no-consultations">No consultations scheduled</p>
              ) : (
                consultations.map(consultation => (
                  <motion.div
                    key={consultation.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="consultation-item"
                  >
                    <div className="consultation-header">
                      <div className="consultation-info">
                        <h4>{consultation.doctor}</h4>
                        <p className="consultation-specialty">{consultation.specialty}</p>
                        <p className="consultation-type">{consultation.type}</p>
                      </div>
                      <div className="consultation-status">
                        <span className={`status-badge ${consultation.status.toLowerCase()}`}>
                          {consultation.status}
                        </span>
                      </div>
                    </div>
                    
                    <div className="consultation-details">
                      <p><strong>Date:</strong> {consultation.date}</p>
                      <p><strong>Time:</strong> {consultation.time}</p>
                      <p><strong>Duration:</strong> {consultation.duration}</p>
                      <p><strong>Symptoms:</strong> {consultation.symptoms}</p>
                    </div>
                    
                    <div className="consultation-actions">
                      {consultation.status === 'Scheduled' && (
                        <button 
                          onClick={() => startCall(consultation.id)}
                          className="btn-primary"
                        >
                          📞 Join Call
                        </button>
                      )}
                      <button className="btn-secondary">📅 Reschedule</button>
                      <button className="btn-secondary">📝 Notes</button>
                      {consultation.status === 'Scheduled' && (
                        <button className="btn-danger">❌ Cancel</button>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          )}

          {activeTab === 'schedule' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="schedule-consultation"
            >
              <h3>Schedule New Consultation</h3>
              
              <div className="consultation-form">
                <div className="form-group">
                  <label>Select Doctor</label>
                  <select
                    value={selectedDoctor || ''}
                    onChange={(e) => setSelectedDoctor(parseInt(e.target.value))}
                  >
                    <option value="">Choose a doctor...</option>
                    {availableDoctors
                      .filter(doctor => doctor.available)
                      .map(doctor => (
                        <option key={doctor.id} value={doctor.id}>
                          {doctor.name} - {doctor.specialty} (Next: {doctor.nextSlot})
                        </option>
                      ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Consultation Type</label>
                  <select
                    value={consultationType}
                    onChange={(e) => setConsultationType(e.target.value)}
                  >
                    <option value="">Select type...</option>
                    {consultationTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Describe Your Symptoms</label>
                  <textarea
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    placeholder="Please describe your symptoms or reason for consultation..."
                    rows="4"
                  />
                </div>

                {selectedDoctor && (
                  <div className="doctor-preview">
                    <h4>Selected Doctor</h4>
                    {(() => {
                      const doctor = availableDoctors.find(d => d.id === selectedDoctor);
                      return (
                        <div className="doctor-card">
                          <div className="doctor-avatar">{doctor.image}</div>
                          <div className="doctor-details">
                            <h5>{doctor.name}</h5>
                            <p>{doctor.specialty}</p>
                            <p>⭐ {doctor.rating} • {doctor.experience} experience</p>
                            <p>🗣️ {doctor.languages.join(', ')}</p>
                            <p>⏰ Next available: {doctor.nextSlot}</p>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}

                <button 
                  onClick={scheduleConsultation}
                  disabled={!selectedDoctor || !consultationType || !symptoms}
                  className="btn-primary"
                >
                  Schedule Consultation
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === 'doctors' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="available-doctors"
            >
              <h3>Available Doctors</h3>
              
              <div className="doctors-grid">
                {availableDoctors.map(doctor => (
                  <motion.div
                    key={doctor.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="doctor-card"
                  >
                    <div className="doctor-header">
                      <div className="doctor-avatar">{doctor.image}</div>
                      <div className="doctor-info">
                        <h4>{doctor.name}</h4>
                        <p className="doctor-specialty">{doctor.specialty}</p>
                        <div className="doctor-rating">
                          <span>⭐ {doctor.rating}</span>
                          <span>• {doctor.experience} experience</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="doctor-details">
                      <p><strong>Languages:</strong> {doctor.languages.join(', ')}</p>
                      <p><strong>Next Available:</strong> {doctor.nextSlot}</p>
                      <span className={`availability-status ${doctor.available ? 'available' : 'unavailable'}`}>
                        {doctor.available ? '🟢 Available Now' : '🔴 Unavailable'}
                      </span>
                    </div>
                    
                    <div className="doctor-actions">
                      <button 
                        className="btn-primary"
                        disabled={!doctor.available}
                      >
                        📅 Book Appointment
                      </button>
                      <button className="btn-secondary">👁️ View Profile</button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {isInCall && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="call-interface"
          >
            <div className="call-container">
              <div className="call-header">
                <h3>📹 Telemedicine Call</h3>
                <span className="call-status">Connected</span>
              </div>
              
              <div className="call-video">
                <div className="video-placeholder">
                  <span>🎥 Video Call Interface</span>
                  <p>Your doctor will join shortly...</p>
                </div>
              </div>
              
              <div className="call-controls">
                <button className="control-btn">🎤 Mute</button>
                <button className="control-btn">📹 Video</button>
                <button className="control-btn">📱 Screen Share</button>
                <button className="control-btn end-call">📞 End Call</button>
              </div>
              
              <div className="call-info">
                <p><strong>Doctor:</strong> Dr. Sarah Johnson</p>
                <p><strong>Duration:</strong> 00:05:30</p>
                <p><strong>Connection:</strong> Stable</p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Telemedicine; 