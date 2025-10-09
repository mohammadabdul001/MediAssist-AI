import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { login } from '../services/api';
import { motion } from 'framer-motion';

const Login = ({ onNavigate }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth, t } = useAppContext();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const user = await login(email, password);
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
        <h2>{t.login}</h2>
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t.email}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label>{t.password}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Logging in...' : t.login}
          </button>
        </form>

        <div className="login-footer">
          <p>{t.noAccount} <button onClick={() => onNavigate('signup')} className="link-btn">{t.signUp}</button></p>
        </div>

        <div className="demo-accounts">
          <h4>Demo Accounts:</h4>
          <div className="demo-account">
            <strong>Admin:</strong> admin123@gmail.com / Pr@1245
          </div>
          <div className="demo-account">
            <strong>Patient:</strong> patient@example.com / patient123
          </div>
          <div className="demo-account">
            <strong>Doctor:</strong> doctor@example.com / doctor123
          </div>
          <div className="demo-account">
            <strong>Lab:</strong> lab@example.com / lab123
          </div>
          <div className="demo-account">
            <strong>Pharmacy:</strong> pharmacy@example.com / pharmacy123
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login; 