import React, { useState, useEffect, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { getLabTests } from '../services/api';
import { motion } from 'framer-motion';

const LabDashboard = ({ onLogout }) => {
  const { auth, t } = useAppContext();
  const [labTests, setLabTests] = useState([]);
  const [activeTab, setActiveTab] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const testsData = await getLabTests();
      setLabTests(testsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadTestResults = async (testId, results, images) => {
    setUploading(true);
    try {
      // Mock API call to upload results
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update local state
      setLabTests(prev => prev.map(test => 
        test.id === testId 
          ? { ...test, status: 'completed', results, images }
          : test
      ));
      
      alert('Test results uploaded successfully!');
    } catch (error) {
      alert('Error uploading results: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = (testId) => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*,.pdf';
    fileInput.multiple = true;
    
    fileInput.onchange = (e) => {
      const files = Array.from(e.target.files);
      const results = prompt('Enter test results:');
      
      if (results) {
        uploadTestResults(testId, results, files.map(f => f.name));
      }
    };
    
    fileInput.click();
  };

  const filteredTests = labTests.filter(test => {
    if (activeTab === 'pending') return test.status === 'pending';
    if (activeTab === 'completed') return test.status === 'completed';
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
          <h1>Lab Dashboard</h1>
          <p>Welcome, {auth.name}</p>
          <p>Lab: {auth.labName}</p>
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
            Pending Tests ({labTests.filter(t => t.status === 'pending').length})
          </button>
          <button 
            className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
            onClick={() => setActiveTab('completed')}
          >
            Completed Tests ({labTests.filter(t => t.status === 'completed').length})
          </button>
          <button 
            className={`tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All Tests ({labTests.length})
          </button>
        </div>

        <div className="tab-content">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <h2>Lab Test Management</h2>
            <div className="data-grid">
              {filteredTests.map(test => (
                <div key={test.id} className="data-card">
                  <h3>{test.testName}</h3>
                  <p><strong>Patient:</strong> {test.patientName}</p>
                  <p><strong>Status:</strong> 
                    <span className={`status-badge ${test.status}`}>
                      {test.status}
                    </span>
                  </p>
                  <p><strong>Requested Date:</strong> {new Date(test.requestedDate).toLocaleDateString()}</p>
                  
                  {test.status === 'completed' && (
                    <div className="test-results">
                      <h4>Results:</h4>
                      <p>{test.results}</p>
                      {test.images && test.images.length > 0 && (
                        <div className="test-images">
                          <h4>Uploaded Files:</h4>
                          <ul>
                            {test.images.map((image, index) => (
                              <li key={index}>{image}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {test.status === 'pending' && (
                    <div className="card-actions">
                      <button 
                        className="btn-primary"
                        onClick={() => handleFileUpload(test.id)}
                        disabled={uploading}
                      >
                        {uploading ? 'Uploading...' : 'Upload Results'}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {filteredTests.length === 0 && (
              <div className="empty-state">
                <p>No {activeTab} tests found.</p>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default LabDashboard; 