import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { register } from '../services/api';
import { motion } from 'framer-motion';

const Signup = ({ onNavigate }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'patient',
    phone: '',
    specialization: '',
    license: '',
    labName: '',
    pharmacyName: '',
    dateOfBirth: '',
    bloodGroup: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth, t } = useAppContext();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const userData = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
        phone: formData.phone
      };

      // Add role-specific fields
      switch (formData.role) {
        case 'doctor':
          userData.specialization = formData.specialization;
          userData.license = formData.license;
          break;
        case 'lab_person':
          userData.labName = formData.labName;
          break;
        case 'pharmacy':
          userData.pharmacyName = formData.pharmacyName;
          break;
        case 'patient':
          userData.dateOfBirth = formData.dateOfBirth;
          userData.bloodGroup = formData.bloodGroup;
          break;
      }

      const user = await register(userData);
      setAuth(user);
      localStorage.setItem('auth', JSON.stringify(user));
      
      // Navigate based on role
      switch (user.role) {
        case 'admin':
          onNavigate('admin');
          break;
        case 'doctor':
          onNavigate('doctor');
          break;
        case 'lab_person':
          onNavigate('lab');
          break;
        case 'pharmacy':
          onNavigate('pharmacy');
          break;
        case 'patient':
        default:
          onNavigate('patient');
          break;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <motion.div 
        className="login-form"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2>{t.signUp}</h2>
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="Enter your full name"
            />
          </div>

          <div className="form-group">
            <label>{t.email}</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label>Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
              placeholder="Enter your phone number"
            />
          </div>

          <div className="form-group">
            <label>Role</label>
            <select name="role" value={formData.role} onChange={handleChange} required>
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="lab_person">Lab Personnel</option>
              <option value="pharmacy">Pharmacy</option>
            </select>
          </div>

          {/* Role-specific fields */}
          {formData.role === 'doctor' && (
            <>
              <div className="form-group">
                <label>Specialization</label>
                <input
                  type="text"
                  name="specialization"
                  value={formData.specialization}
                  onChange={handleChange}
                  required
                  placeholder="e.g., Cardiology, Neurology"
                />
              </div>
              <div className="form-group">
                <label>License Number</label>
                <input
                  type="text"
                  name="license"
                  value={formData.license}
                  onChange={handleChange}
                  required
                  placeholder="Enter your medical license number"
                />
              </div>
            </>
          )}

          {formData.role === 'lab_person' && (
            <div className="form-group">
              <label>Lab Name</label>
              <input
                type="text"
                name="labName"
                value={formData.labName}
                onChange={handleChange}
                required
                placeholder="Enter your lab name"
              />
            </div>
          )}

          {formData.role === 'pharmacy' && (
            <div className="form-group">
              <label>Pharmacy Name</label>
              <input
                type="text"
                name="pharmacyName"
                value={formData.pharmacyName}
                onChange={handleChange}
                required
                placeholder="Enter your pharmacy name"
              />
            </div>
          )}

          {formData.role === 'patient' && (
            <>
              <div className="form-group">
                <label>Date of Birth</label>
                <input
                  type="date"
                  name="dateOfBirth"
                  value={formData.dateOfBirth}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Blood Group</label>
                <select name="bloodGroup" value={formData.bloodGroup} onChange={handleChange} required>
                  <option value="">Select Blood Group</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
              </div>
            </>
          )}
          
          <div className="form-group">
            <label>{t.password}</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </div>

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              placeholder="Confirm your password"
            />
          </div>
          
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Creating Account...' : t.signUp}
          </button>
        </form>

        <div className="login-footer">
          <p>{t.haveAccount} <button onClick={() => onNavigate('login')} className="link-btn">{t.login}</button></p>
        </div>
      </motion.div>
    </div>
  );
};

export default Signup; 