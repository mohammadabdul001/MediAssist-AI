import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const MedicationTracker = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('medications');
  const [medications, setMedications] = useState([
    {
      id: 1,
      name: 'Aspirin',
      dosage: '100mg',
      frequency: 'Once daily',
      time: '08:00',
      status: 'Active',
      startDate: '2024-01-01',
      endDate: '2024-02-01',
      takenToday: true,
      notes: 'Take with food'
    },
    {
      id: 2,
      name: 'Vitamin D',
      dosage: '1000 IU',
      frequency: 'Once daily',
      time: '12:00',
      status: 'Active',
      startDate: '2024-01-01',
      endDate: null,
      takenToday: false,
      notes: 'Take with breakfast'
    }
  ]);

  const [newMedication, setNewMedication] = useState({
    name: '',
    dosage: '',
    frequency: '',
    time: '',
    startDate: '',
    endDate: '',
    notes: ''
  });

  const [reminders, setReminders] = useState([
    {
      id: 1,
      medicationId: 1,
      time: '08:00',
      enabled: true,
      type: 'notification'
    },
    {
      id: 2,
      medicationId: 2,
      time: '12:00',
      enabled: true,
      type: 'notification'
    }
  ]);

  const frequencies = [
    'Once daily', 'Twice daily', 'Three times daily', 'Four times daily',
    'Every 6 hours', 'Every 8 hours', 'Every 12 hours', 'As needed'
  ];

  const addMedication = () => {
    if (newMedication.name && newMedication.dosage && newMedication.frequency) {
      const medication = {
        id: medications.length + 1,
        ...newMedication,
        status: 'Active',
        takenToday: false
      };
      setMedications([...medications, medication]);
      setNewMedication({
        name: '', dosage: '', frequency: '', time: '', startDate: '', endDate: '', notes: ''
      });
    }
  };

  const toggleMedicationTaken = (id) => {
    setMedications(medications.map(med => 
      med.id === id ? { ...med, takenToday: !med.takenToday } : med
    ));
  };

  const deleteMedication = (id) => {
    setMedications(medications.filter(med => med.id !== id));
  };

  const getTodayStats = () => {
    const total = medications.length;
    const taken = medications.filter(med => med.takenToday).length;
    const missed = total - taken;
    return { total, taken, missed };
  };

  const stats = getTodayStats();

  return (
    <div className="medication-tracker">
      <div className="tracker-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="tracker-title"
        >
          💊 Medication Tracker
        </motion.h2>

        <div className="tracker-stats">
          <div className="stat-card">
            <h3>Today's Progress</h3>
            <div className="progress-circle">
              <span className="progress-text">{stats.taken}/{stats.total}</span>
            </div>
          </div>
          <div className="stat-card">
            <h3>Active Medications</h3>
            <span className="stat-number">{stats.total}</span>
          </div>
          <div className="stat-card">
            <h3>Missed Today</h3>
            <span className="stat-number missed">{stats.missed}</span>
          </div>
        </div>

        <div className="tracker-tabs">
          <button
            className={`tab ${activeTab === 'medications' ? 'active' : ''}`}
            onClick={() => setActiveTab('medications')}
          >
            My Medications
          </button>
          <button
            className={`tab ${activeTab === 'add' ? 'active' : ''}`}
            onClick={() => setActiveTab('add')}
          >
            Add Medication
          </button>
          <button
            className={`tab ${activeTab === 'reminders' ? 'active' : ''}`}
            onClick={() => setActiveTab('reminders')}
          >
            Reminders
          </button>
        </div>

        <div className="tracker-content">
          {activeTab === 'medications' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="medications-list"
            >
              <h3>Today's Medications</h3>
              
              {medications.length === 0 ? (
                <p className="no-medications">No medications added</p>
              ) : (
                medications.map(medication => (
                  <motion.div
                    key={medication.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`medication-item ${medication.takenToday ? 'taken' : ''}`}
                  >
                    <div className="medication-header">
                      <div className="medication-info">
                        <h4>{medication.name}</h4>
                        <p className="medication-dosage">{medication.dosage} - {medication.frequency}</p>
                        <p className="medication-time">⏰ {medication.time}</p>
                      </div>
                      <div className="medication-status">
                        <span className={`status-badge ${medication.takenToday ? 'taken' : 'pending'}`}>
                          {medication.takenToday ? '✅ Taken' : '⏳ Pending'}
                        </span>
                      </div>
                    </div>
                    
                    {medication.notes && (
                      <p className="medication-notes">📝 {medication.notes}</p>
                    )}
                    
                    <div className="medication-actions">
                      <button
                        onClick={() => toggleMedicationTaken(medication.id)}
                        className={`btn-toggle ${medication.takenToday ? 'taken' : ''}`}
                      >
                        {medication.takenToday ? '✅ Mark as Not Taken' : '💊 Mark as Taken'}
                      </button>
                      <button className="btn-secondary">📅 Schedule</button>
                      <button 
                        onClick={() => deleteMedication(medication.id)}
                        className="btn-danger"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          )}

          {activeTab === 'add' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="add-medication"
            >
              <h3>Add New Medication</h3>
              
              <div className="medication-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Medication Name</label>
                    <input
                      type="text"
                      value={newMedication.name}
                      onChange={(e) => setNewMedication({...newMedication, name: e.target.value})}
                      placeholder="e.g., Aspirin, Vitamin D"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Dosage</label>
                    <input
                      type="text"
                      value={newMedication.dosage}
                      onChange={(e) => setNewMedication({...newMedication, dosage: e.target.value})}
                      placeholder="e.g., 100mg, 1 tablet"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Frequency</label>
                    <select
                      value={newMedication.frequency}
                      onChange={(e) => setNewMedication({...newMedication, frequency: e.target.value})}
                    >
                      <option value="">Select frequency...</option>
                      {frequencies.map(freq => (
                        <option key={freq} value={freq}>{freq}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Time</label>
                    <input
                      type="time"
                      value={newMedication.time}
                      onChange={(e) => setNewMedication({...newMedication, time: e.target.value})}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Start Date</label>
                    <input
                      type="date"
                      value={newMedication.startDate}
                      onChange={(e) => setNewMedication({...newMedication, startDate: e.target.value})}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>End Date (Optional)</label>
                    <input
                      type="date"
                      value={newMedication.endDate}
                      onChange={(e) => setNewMedication({...newMedication, endDate: e.target.value})}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Notes (Optional)</label>
                  <textarea
                    value={newMedication.notes}
                    onChange={(e) => setNewMedication({...newMedication, notes: e.target.value})}
                    placeholder="Special instructions, side effects, etc."
                    rows="3"
                  />
                </div>

                <button 
                  onClick={addMedication}
                  disabled={!newMedication.name || !newMedication.dosage || !newMedication.frequency}
                  className="btn-primary"
                >
                  Add Medication
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === 'reminders' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="reminders-settings"
            >
              <h3>Reminder Settings</h3>
              
              <div className="reminders-list">
                {reminders.map(reminder => (
                  <div key={reminder.id} className="reminder-item">
                    <div className="reminder-info">
                      <span className="reminder-time">⏰ {reminder.time}</span>
                      <span className="reminder-type">{reminder.type}</span>
                    </div>
                    <div className="reminder-actions">
                      <label className="toggle-switch">
                        <input
                          type="checkbox"
                          checked={reminder.enabled}
                          onChange={() => {
                            setReminders(reminders.map(r => 
                              r.id === reminder.id ? { ...r, enabled: !r.enabled } : r
                            ));
                          }}
                        />
                        <span className="toggle-slider"></span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>

              <div className="reminder-settings">
                <h4>Notification Settings</h4>
                <div className="setting-item">
                  <label>
                    <input type="checkbox" defaultChecked /> Enable push notifications
                  </label>
                </div>
                <div className="setting-item">
                  <label>
                    <input type="checkbox" defaultChecked /> Enable email reminders
                  </label>
                </div>
                <div className="setting-item">
                  <label>
                    <input type="checkbox" /> Enable SMS reminders
                  </label>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MedicationTracker; 