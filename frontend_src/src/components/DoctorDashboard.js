import React, { useState, useEffect, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { getPatients, getLabTests, getPrescriptions } from '../services/api';
import { motion } from 'framer-motion';

const DoctorDashboard = ({ onLogout }) => {
  const { auth, t } = useAppContext();
  const [patients, setPatients] = useState([]);
  const [labTests, setLabTests] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [activeTab, setActiveTab] = useState('patients');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [patientsData, labTestsData, prescriptionsData] = await Promise.all([
        getPatients(),
        getLabTests(),
        getPrescriptions()
      ]);
      setPatients(patientsData);
      setLabTests(labTestsData);
      setPrescriptions(prescriptionsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const requestLabTest = (patientId, testName) => {
    // Mock function to request lab test
    alert(`Lab test "${testName}" requested for patient ${patientId}`);
  };

  const sendPrescription = (patientId, medications) => {
    // Mock function to send prescription to pharmacy
    alert(`Prescription sent to pharmacy for patient ${patientId}`);
  };

  if (loading) {
    return (
      <div className="admin-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div>
          <h1>Doctor Dashboard</h1>
          <p>Welcome, Dr. {auth.name}</p>
          <p>Specialization: {auth.specialization}</p>
        </div>
        <button onClick={onLogout} className="logout-btn">
          {t.logout}
        </button>
      </div>
      
      <div className="admin-content">
        <div className="tab-navigation">
          <button 
            className={`tab ${activeTab === 'patients' ? 'active' : ''}`}
            onClick={() => setActiveTab('patients')}
          >
            Patients ({patients.length})
          </button>
          <button 
            className={`tab ${activeTab === 'lab-tests' ? 'active' : ''}`}
            onClick={() => setActiveTab('lab-tests')}
          >
            Lab Tests ({labTests.length})
          </button>
          <button 
            className={`tab ${activeTab === 'prescriptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('prescriptions')}
          >
            Prescriptions ({prescriptions.length})
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'patients' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>Patient Records</h2>
              <div className="data-grid">
                {patients.map(patient => (
                  <div key={patient.id} className="data-card">
                    <h3>{patient.name}</h3>
                    <p><strong>Email:</strong> {patient.email}</p>
                    <p><strong>Phone:</strong> {patient.phone}</p>
                    <p><strong>Blood Group:</strong> {patient.bloodGroup}</p>
                    <p><strong>Date of Birth:</strong> {patient.dateOfBirth}</p>
                    <div className="card-actions">
                      <button 
                        className="btn-primary"
                        onClick={() => requestLabTest(patient.id, 'Blood Test')}
                      >
                        Request Lab Test
                      </button>
                      <button 
                        className="btn-secondary"
                        onClick={() => sendPrescription(patient.id, [])}
                      >
                        Send Prescription
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'lab-tests' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>Lab Test Requests</h2>
              <div className="data-grid">
                {labTests.map(test => (
                  <div key={test.id} className="data-card">
                    <h3>{test.testName}</h3>
                    <p><strong>Patient:</strong> {test.patientName}</p>
                    <p><strong>Status:</strong> 
                      <span className={`status-badge ${test.status}`}>
                        {test.status}
                      </span>
                    </p>
                    <p><strong>Requested Date:</strong> {new Date(test.requestedDate).toLocaleDateString()}</p>
                    {test.results && (
                      <div className="test-results">
                        <h4>Results:</h4>
                        <p>{test.results}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'prescriptions' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>Prescriptions</h2>
              <div className="data-grid">
                {prescriptions.map(prescription => (
                  <div key={prescription.id} className="data-card">
                    <h3>Prescription #{prescription.id}</h3>
                    <p><strong>Patient:</strong> {prescription.patientName}</p>
                    <p><strong>Doctor:</strong> {prescription.doctorName}</p>
                    <p><strong>Status:</strong> 
                      <span className={`status-badge ${prescription.status}`}>
                        {prescription.status}
                      </span>
                    </p>
                    <p><strong>Prescribed Date:</strong> {new Date(prescription.prescribedDate).toLocaleDateString()}</p>
                    <div className="medications">
                      <h4>Medications:</h4>
                      {prescription.medications.map((med, index) => (
                        <div key={index} className="medication-item">
                          <p><strong>{med.name}</strong> - {med.dosage}</p>
                          <p>Frequency: {med.frequency}</p>
                          <p>Duration: {med.duration}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DoctorDashboard; 