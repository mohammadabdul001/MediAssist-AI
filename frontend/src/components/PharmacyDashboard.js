import React, { useState, useEffect, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { getPrescriptions } from '../services/api';
import { motion } from 'framer-motion';

const PharmacyDashboard = ({ onLogout }) => {
  const { auth, t } = useAppContext();
  const [prescriptions, setPrescriptions] = useState([]);
  const [activeTab, setActiveTab] = useState('pending');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const prescriptionsData = await getPrescriptions();
      setPrescriptions(prescriptionsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fulfillPrescription = (prescriptionId) => {
    // Mock function to fulfill prescription
    setPrescriptions(prev => prev.map(prescription => 
      prescription.id === prescriptionId 
        ? { ...prescription, status: 'fulfilled' }
        : prescription
    ));
    alert(`Prescription ${prescriptionId} has been fulfilled!`);
  };

  const filteredPrescriptions = prescriptions.filter(prescription => {
    if (activeTab === 'pending') return prescription.status === 'pending';
    if (activeTab === 'fulfilled') return prescription.status === 'fulfilled';
    return true;
  });

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
          <h1>Pharmacy Dashboard</h1>
          <p>Welcome, {auth.name}</p>
          <p>Pharmacy: {auth.pharmacyName}</p>
        </div>
        <button onClick={onLogout} className="logout-btn">
          {t.logout}
        </button>
      </div>
      
      <div className="admin-content">
        <div className="tab-navigation">
          <button 
            className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending Prescriptions ({prescriptions.filter(p => p.status === 'pending').length})
          </button>
          <button 
            className={`tab ${activeTab === 'fulfilled' ? 'active' : ''}`}
            onClick={() => setActiveTab('fulfilled')}
          >
            Fulfilled Prescriptions ({prescriptions.filter(p => p.status === 'fulfilled').length})
          </button>
          <button 
            className={`tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All Prescriptions ({prescriptions.length})
          </button>
        </div>

        <div className="tab-content">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <h2>Prescription Management</h2>
            <div className="data-grid">
              {filteredPrescriptions.map(prescription => (
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
                        <div className="medication-header">
                          <h5>{med.name}</h5>
                          <span className="medication-dosage">{med.dosage}</span>
                        </div>
                        <p><strong>Frequency:</strong> {med.frequency}</p>
                        <p><strong>Duration:</strong> {med.duration}</p>
                        <div className="medication-actions">
                          <button className="btn-secondary">Check Stock</button>
                          <button className="btn-secondary">View Details</button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {prescription.status === 'pending' && (
                    <div className="card-actions">
                      <button 
                        className="btn-primary"
                        onClick={() => fulfillPrescription(prescription.id)}
                      >
                        Fulfill Prescription
                      </button>
                      <button className="btn-secondary">
                        Contact Doctor
                      </button>
                    </div>
                  )}
                  
                  {prescription.status === 'fulfilled' && (
                    <div className="fulfillment-info">
                      <p><strong>Fulfilled Date:</strong> {new Date().toLocaleDateString()}</p>
                      <p><strong>Fulfilled By:</strong> {auth.name}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {filteredPrescriptions.length === 0 && (
              <div className="empty-state">
                <p>No {activeTab} prescriptions found.</p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default PharmacyDashboard; 