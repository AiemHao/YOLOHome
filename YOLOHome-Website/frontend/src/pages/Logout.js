import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Logout.css';

const Logout = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/');
  };

  const handleCancel = () => {
    navigate(-1); // Go back to the previous page
  };

  return (
    <div className="logout-page">
      <header className="page-header" style={{display: 'flex', justifyContent: 'center'}}>
        <h1>Đăng xuất</h1>
      </header>

      <div className="logout-content">
        <div className="logout-card">
          <h2>Đăng xuất khỏi tài khoản của bạn?</h2>
          
          <div className="logout-actions">
            <button className="btn-cancel" onClick={handleCancel}>Hủy</button>
            <button className="btn-confirm" onClick={handleLogout}>Đăng xuất</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Logout;
