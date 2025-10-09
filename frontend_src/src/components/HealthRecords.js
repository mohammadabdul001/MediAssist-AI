import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const HealthRecords = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('overview');
  const [records, setRecords] = useState([
    {
      id: 1,
      type: 'Medical History',
      date: '2024-01-15',
      doctor: 'Dr. Sarah Johnson',
      description: 'Annual physical examination',
      status: 'Completed',
      file: 'medical_history_2024.pdf'
    },
    {
      id: 2,
      type: 'Lab Results',
      date: '2024-01-10',
      doctor: 'Dr. Michael Chen',
      description: 'Blood work and cholesterol test',
      status: 'Available',
      file: 'lab_results_jan2024.pdf'
    },
    {
      id: 3,
      type: 'Prescription',
      date: '2024-01-08',
      doctor: 'Dr. Emily Davis',
      description: 'Antibiotics for sinus infection',
      status: 'Active',
      file: 'prescription_antibiotics.pdf'
    }
  ]);

  const [newRecord, setNewRecord] = useState({
    type: '',
    description: '',
    date: '',
    doctor: ''
  });

  const addRecord = () => {
    if (newRecord.type && newRecord.description) {
      const record = {
        id: records.length + 1,
        ...newRecord,
        status: 'Pending',
        file: null
      };
      setRecords([...records, record]);
      setNewRecord({ type: '', description: '', date: '', doctor: '' });
    }
  };

  const recordTypes = [
    'Medical History', 'Lab Results', 'Prescription', 'Vaccination',
    'Surgery', 'Allergy', 'Immunization', 'Dental', 'Vision', 'Mental Health'
  ];

  return (
    <div className="health-records">
      <div className="records-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="records-title"
        >
          📋 Health Record Management
        </motion.h2>

        <div className="records-tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'add' ? 'active' : ''}`}
            onClick={() => setActiveTab('add')}
          >
            Add Record
          </button>
          <button
            className={`tab ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            Search
          </button>
        </div>

        <div className="records-content">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="records-overview"
            >
              <div className="records-stats">
                <div className="stat-card">
                  <h3>Total Records</h3>
                  <span className="stat-number">{records.length}</span>
                </div>
                <div className="stat-card">
                  <h3>Recent</h3>
                  <span className="stat-number">{records.filter(r => r.status === 'Available').length}</span>
                </div>
                <div className="stat-card">
                  <h3>Pending</h3>
                  <span className="stat-number">{records.filter(r => r.status === 'Pending').length}</span>
                </div>
              </div>

              <div className="records-list">
                <h3>Recent Records</h3>
                {records.map(record => (
                  <motion.div
                    key={record.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="record-item"
                  >
                    <div className="record-header">
                      <span className="record-type">{record.type}</span>
                      <span className={`record-status ${record.status.toLowerCase()}`}>
                        {record.status}
                      </span>
                    </div>
                    <div className="record-details">
                      <p><strong>Date:</strong> {record.date}</p>
                      <p><strong>Doctor:</strong> {record.doctor}</p>
                      <p><strong>Description:</strong> {record.description}</p>
                    </div>
                    <div className="record-actions">
                      {record.file && (
                        <button className="btn-download">📄 Download</button>
                      )}
                      <button className="btn-view">👁️ View</button>
                      <button className="btn-share">📤 Share</button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'add' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="add-record"
            >
              <h3>Add New Health Record</h3>
              <div className="form-group">
                <label>Record Type</label>
                <select
                  value={newRecord.type}
                  onChange={(e) => setNewRecord({...newRecord, type: e.target.value})}
                >
                  <option value="">Select type...</option>
                  {recordTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newRecord.description}
                  onChange={(e) => setNewRecord({...newRecord, description: e.target.value})}
                  placeholder="Describe the health record..."
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    value={newRecord.date}
                    onChange={(e) => setNewRecord({...newRecord, date: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Doctor/Provider</label>
                  <input
                    type="text"
                    value={newRecord.doctor}
                    onChange={(e) => setNewRecord({...newRecord, doctor: e.target.value})}
                    placeholder="Doctor's name"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Upload File (Optional)</label>
                <input type="file" accept=".pdf,.doc,.docx,.jpg,.png" />
              </div>

              <button onClick={addRecord} className="btn-primary">
                Add Record
              </button>
            </motion.div>
          )}

          {activeTab === 'search' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="search-records"
            >
              <h3>Search Records</h3>
              <div className="search-filters">
                <input
                  type="text"
                  placeholder="Search by type, doctor, or description..."
                  className="search-input"
                />
                <select className="filter-select">
                  <option value="">All Types</option>
                  {recordTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                <select className="filter-select">
                  <option value="">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="available">Available</option>
                  <option value="pending">Pending</option>
                </select>
                <button className="btn-search">🔍 Search</button>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthRecords; 