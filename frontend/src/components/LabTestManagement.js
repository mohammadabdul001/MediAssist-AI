import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const LabTestManagement = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('tests');
  const [labTests, setLabTests] = useState([
    {
      id: 1,
      name: 'Complete Blood Count (CBC)',
      type: 'Blood Test',
      date: '2024-01-15',
      time: '09:00 AM',
      status: 'Completed',
      results: 'Available',
      lab: 'City Medical Lab',
      doctor: 'Dr. Sarah Johnson',
      fasting: true,
      notes: 'Fast for 12 hours before test'
    },
    {
      id: 2,
      name: 'Cholesterol Panel',
      type: 'Blood Test',
      date: '2024-01-20',
      time: '08:30 AM',
      status: 'Scheduled',
      results: 'Pending',
      lab: 'Health Diagnostics Center',
      doctor: 'Dr. Michael Chen',
      fasting: true,
      notes: 'Fast for 14 hours before test'
    },
    {
      id: 3,
      name: 'Urinalysis',
      type: 'Urine Test',
      date: '2024-01-10',
      time: '10:00 AM',
      status: 'Completed',
      results: 'Available',
      lab: 'City Medical Lab',
      doctor: 'Dr. Emily Davis',
      fasting: false,
      notes: 'First morning urine sample preferred'
    }
  ]);

  const [newTest, setNewTest] = useState({
    name: '',
    type: '',
    date: '',
    time: '',
    lab: '',
    doctor: '',
    fasting: false,
    notes: ''
  });

  const testTypes = [
    'Blood Test', 'Urine Test', 'Stool Test', 'X-Ray', 'MRI', 'CT Scan',
    'Ultrasound', 'ECG', 'EKG', 'Biopsy', 'Culture Test', 'Allergy Test'
  ];

  const labs = [
    'City Medical Lab', 'Health Diagnostics Center', 'Regional Medical Center',
    'Community Hospital Lab', 'Specialty Testing Lab'
  ];

  const scheduleTest = () => {
    if (newTest.name && newTest.type && newTest.date && newTest.lab) {
      const test = {
        id: labTests.length + 1,
        ...newTest,
        status: 'Scheduled',
        results: 'Pending'
      };
      setLabTests([...labTests, test]);
      setNewTest({
        name: '', type: '', date: '', time: '', lab: '', doctor: '', fasting: false, notes: ''
      });
    }
  };

  const cancelTest = (id) => {
    setLabTests(labTests.filter(test => test.id !== id));
  };

  const getTestStats = () => {
    const total = labTests.length;
    const completed = labTests.filter(test => test.status === 'Completed').length;
    const scheduled = labTests.filter(test => test.status === 'Scheduled').length;
    const resultsAvailable = labTests.filter(test => test.results === 'Available').length;
    return { total, completed, scheduled, resultsAvailable };
  };

  const stats = getTestStats();

  return (
    <div className="lab-test-management">
      <div className="lab-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lab-title"
        >
          🧪 Lab Test Management
        </motion.h2>

        <div className="lab-stats">
          <div className="stat-card">
            <h3>Total Tests</h3>
            <span className="stat-number">{stats.total}</span>
          </div>
          <div className="stat-card">
            <h3>Completed</h3>
            <span className="stat-number">{stats.completed}</span>
          </div>
          <div className="stat-card">
            <h3>Scheduled</h3>
            <span className="stat-number">{stats.scheduled}</span>
          </div>
          <div className="stat-card">
            <h3>Results Available</h3>
            <span className="stat-number">{stats.resultsAvailable}</span>
          </div>
        </div>

        <div className="lab-tabs">
          <button
            className={`tab ${activeTab === 'tests' ? 'active' : ''}`}
            onClick={() => setActiveTab('tests')}
          >
            My Tests
          </button>
          <button
            className={`tab ${activeTab === 'schedule' ? 'active' : ''}`}
            onClick={() => setActiveTab('schedule')}
          >
            Schedule Test
          </button>
          <button
            className={`tab ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
          >
            Test Results
          </button>
        </div>

        <div className="lab-content">
          {activeTab === 'tests' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="tests-list"
            >
              <h3>My Lab Tests</h3>
              
              {labTests.length === 0 ? (
                <p className="no-tests">No lab tests scheduled</p>
              ) : (
                labTests.map(test => (
                  <motion.div
                    key={test.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="test-item"
                  >
                    <div className="test-header">
                      <div className="test-info">
                        <h4>{test.name}</h4>
                        <p className="test-type">{test.type}</p>
                        <p className="test-lab">🏥 {test.lab}</p>
                      </div>
                      <div className="test-status">
                        <span className={`status-badge ${test.status.toLowerCase()}`}>
                          {test.status}
                        </span>
                        <span className={`results-badge ${test.results.toLowerCase()}`}>
                          {test.results}
                        </span>
                      </div>
                    </div>
                    
                    <div className="test-details">
                      <p><strong>Date:</strong> {test.date}</p>
                      <p><strong>Time:</strong> {test.time}</p>
                      {test.doctor && <p><strong>Doctor:</strong> {test.doctor}</p>}
                      {test.fasting && <p className="fasting-notice">⚠️ Fasting Required</p>}
                      {test.notes && <p className="test-notes">📝 {test.notes}</p>}
                    </div>
                    
                    <div className="test-actions">
                      {test.results === 'Available' && (
                        <button className="btn-primary">📊 View Results</button>
                      )}
                      <button className="btn-secondary">📅 Reschedule</button>
                      <button 
                        onClick={() => cancelTest(test.id)}
                        className="btn-danger"
                      >
                        ❌ Cancel
                      </button>
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
              className="schedule-test"
            >
              <h3>Schedule New Lab Test</h3>
              
              <div className="test-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Test Name</label>
                    <input
                      type="text"
                      value={newTest.name}
                      onChange={(e) => setNewTest({...newTest, name: e.target.value})}
                      placeholder="e.g., Complete Blood Count, Cholesterol Panel"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Test Type</label>
                    <select
                      value={newTest.type}
                      onChange={(e) => setNewTest({...newTest, type: e.target.value})}
                    >
                      <option value="">Select test type...</option>
                      {testTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Laboratory</label>
                    <select
                      value={newTest.lab}
                      onChange={(e) => setNewTest({...newTest, lab: e.target.value})}
                    >
                      <option value="">Select laboratory...</option>
                      {labs.map(lab => (
                        <option key={lab} value={lab}>{lab}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Doctor (Optional)</label>
                    <input
                      type="text"
                      value={newTest.doctor}
                      onChange={(e) => setNewTest({...newTest, doctor: e.target.value})}
                      placeholder="Doctor's name"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Date</label>
                    <input
                      type="date"
                      value={newTest.date}
                      onChange={(e) => setNewTest({...newTest, date: e.target.value})}
                      min={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Time</label>
                    <input
                      type="time"
                      value={newTest.time}
                      onChange={(e) => setNewTest({...newTest, time: e.target.value})}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={newTest.fasting}
                      onChange={(e) => setNewTest({...newTest, fasting: e.target.checked})}
                    />
                    Fasting Required
                  </label>
                </div>

                <div className="form-group">
                  <label>Special Instructions (Optional)</label>
                  <textarea
                    value={newTest.notes}
                    onChange={(e) => setNewTest({...newTest, notes: e.target.value})}
                    placeholder="Any special instructions or notes..."
                    rows="3"
                  />
                </div>

                <button 
                  onClick={scheduleTest}
                  disabled={!newTest.name || !newTest.type || !newTest.date || !newTest.lab}
                  className="btn-primary"
                >
                  Schedule Test
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === 'results' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="test-results"
            >
              <h3>Test Results</h3>
              
              <div className="results-list">
                {labTests.filter(test => test.results === 'Available').length === 0 ? (
                  <p className="no-results">No test results available</p>
                ) : (
                  labTests
                    .filter(test => test.results === 'Available')
                    .map(test => (
                      <motion.div
                        key={test.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="result-item"
                      >
                        <div className="result-header">
                          <h4>{test.name}</h4>
                          <span className="result-date">{test.date}</span>
                        </div>
                        
                        <div className="result-summary">
                          <p><strong>Test Type:</strong> {test.type}</p>
                          <p><strong>Laboratory:</strong> {test.lab}</p>
                          <p><strong>Status:</strong> <span className="status-normal">Normal</span></p>
                        </div>
                        
                        <div className="result-actions">
                          <button className="btn-primary">📊 View Detailed Results</button>
                          <button className="btn-secondary">📤 Share Results</button>
                          <button className="btn-secondary">📄 Download PDF</button>
                        </div>
                      </motion.div>
                    ))
                )}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LabTestManagement; 