import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';

const AdminLogin = ({ onNavigate }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { setAuth, t } = useAppContext();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email === 'praveeshboddu2304@gmail.com' && password === 'Pr@1245') {
      const adminUser = { 
        email, 
        role: 'admin', 
        name: 'Praveesh Boddu',
        token: 'fake-jwt' 
      };
      setAuth(adminUser);
      localStorage.setItem('auth', JSON.stringify(adminUser));
      onNavigate('admin');
    } else {
      setError(t.invalidCreds);
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>{t.adminLogin}</h2>
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t.email}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label>{t.password}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          <button type="submit" className="login-btn">
            {t.login}
          </button>
        </form>

        <div className="login-footer">
          <p>Admin Access Only</p>
          <button onClick={() => onNavigate('home')} className="link-btn">Back to Home</button>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;