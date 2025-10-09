import React, { useState, useEffect, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { getStats, getPatients } from '../services/api';
import { motion } from 'framer-motion';

const AdminDashboard = ({ onLogout }) => {
  const { auth, t } = useAppContext();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [websiteSettings, setWebsiteSettings] = useState({
    heroTitle: "Your AI-Powered Health Companion",
    heroSubtitle: "Real-Time Symptom Analysis. Trusted Care. Anytime, Anywhere.",
    featuresTitle: "Comprehensive Healthcare Features",
    featuresSubtitle: "Everything you need for complete health management in one platform"
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, usersData] = await Promise.all([
        getStats(),
        getPatients()
      ]);
      setStats(statsData);
      setUsers(usersData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateWebsiteSettings = (field, value) => {
    setWebsiteSettings(prev => ({
      ...prev,
      [field]: value
    }));
    // In a real app, this would save to backend
    alert(`Website setting "${field}" updated successfully!`);
  };

  const handleUserAction = (action, userId) => {
    switch (action) {
      case 'suspend':
        alert(`User ${userId} suspended`);
        break;
      case 'delete':
        if (confirm('Are you sure you want to delete this user?')) {
          alert(`User ${userId} deleted`);
        }
        break;
      case 'edit':
        alert(`Edit user ${userId}`);
        break;
      default:
        break;
    }
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
          <h1>{t.adminDashboard}</h1>
          <p>{t.welcome}, <strong>{auth.name}</strong>!</p>
          <p>Role: Administrator</p>
        </div>
        <button onClick={onLogout} className="logout-btn">
          {t.logout}
        </button>
      </div>
      
      <div className="admin-content">
        <div className="tab-navigation">
          <button 
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            User Management
          </button>
          <button 
            className={`tab ${activeTab === 'website' ? 'active' : ''}`}
            onClick={() => setActiveTab('website')}
          >
            Website Settings
          </button>
          <button 
            className={`tab ${activeTab === 'system' ? 'active' : ''}`}
            onClick={() => setActiveTab('system')}
          >
            System Settings
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>System Overview</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Total Users</h3>
                  <div className="stat-number">{stats.totalUsers}</div>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: '85%' }}></div>
                    </div>
                    <span className="progress-text">85% Growth</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <h3>Doctors</h3>
                  <div className="stat-number">{stats.doctors}</div>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: '70%' }}></div>
                    </div>
                    <span className="progress-text">70% Active</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <h3>Patients</h3>
                  <div className="stat-number">{stats.patients}</div>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: '90%' }}></div>
                    </div>
                    <span className="progress-text">90% Satisfaction</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <h3>Lab Personnel</h3>
                  <div className="stat-number">{stats.labPersonnel}</div>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: '60%' }}></div>
                    </div>
                    <span className="progress-text">60% Efficiency</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <h3>Pharmacies</h3>
                  <div className="stat-number">{stats.pharmacies}</div>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: '75%' }}></div>
                    </div>
                    <span className="progress-text">75% Coverage</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <h3>System Health</h3>
                  <div className="stat-number">{stats.systemHealth}</div>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: '99%' }}></div>
                    </div>
                    <span className="progress-text">99% Uptime</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'users' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>User Management</h2>
              <div className="data-grid">
                {users.map(user => (
                  <div key={user.id} className="data-card">
                    <h3>{user.name}</h3>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Role:</strong> 
                      <span className={`status-badge ${user.role}`}>
                        {user.role}
                      </span>
                    </p>
                    <p><strong>Phone:</strong> {user.phone}</p>
                    <p><strong>Created:</strong> {new Date(user.createdAt).toLocaleDateString()}</p>
                    <div className="card-actions">
                      <button 
                        className="btn-secondary"
                        onClick={() => handleUserAction('edit', user.id)}
                      >
                        Edit
                      </button>
                      <button 
                        className="btn-secondary"
                        onClick={() => handleUserAction('suspend', user.id)}
                      >
                        Suspend
                      </button>
                      <button 
                        className="btn-danger"
                        onClick={() => handleUserAction('delete', user.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'website' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>Website Settings</h2>
              <div className="settings-form">
                <div className="form-group">
                  <label>Hero Title</label>
                  <input
                    type="text"
                    value={websiteSettings.heroTitle}
                    onChange={(e) => updateWebsiteSettings('heroTitle', e.target.value)}
                    placeholder="Enter hero title"
                  />
                </div>
                
                <div className="form-group">
                  <label>Hero Subtitle</label>
                  <textarea
                    value={websiteSettings.heroSubtitle}
                    onChange={(e) => updateWebsiteSettings('heroSubtitle', e.target.value)}
                    placeholder="Enter hero subtitle"
                    rows="3"
                  />
                </div>
                
                <div className="form-group">
                  <label>Features Section Title</label>
                  <input
                    type="text"
                    value={websiteSettings.featuresTitle}
                    onChange={(e) => updateWebsiteSettings('featuresTitle', e.target.value)}
                    placeholder="Enter features title"
                  />
                </div>
                
                <div className="form-group">
                  <label>Features Section Subtitle</label>
                  <textarea
                    value={websiteSettings.featuresSubtitle}
                    onChange={(e) => updateWebsiteSettings('featuresSubtitle', e.target.value)}
                    placeholder="Enter features subtitle"
                    rows="3"
                  />
                </div>
                
                <button className="btn-primary">Save All Changes</button>
              </div>
            </motion.div>
          )}

          {activeTab === 'system' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <h2>System Settings</h2>
              <div className="admin-actions">
                <h3>System Actions</h3>
                <div className="action-buttons">
                  <button className="action-btn">Backup Database</button>
                  <button className="action-btn">Clear Cache</button>
                  <button className="action-btn">Update System</button>
                  <button className="action-btn">View Logs</button>
                  <button className="action-btn">Security Settings</button>
                  <button className="action-btn">API Configuration</button>
                </div>
              </div>
              
              <div className="system-info">
                <h3>System Information</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <strong>Version:</strong> 1.0.0
                  </div>
                  <div className="info-item">
                    <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
                  </div>
                  <div className="info-item">
                    <strong>Database:</strong> SQLite
                  </div>
                  <div className="info-item">
                    <strong>Environment:</strong> Development
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;