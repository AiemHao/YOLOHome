import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, ShieldCheck } from 'lucide-react'; 
import yoloLogo from './YOLO-03.png';
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
    <div className="logout-overlay">
      <div className="logout-modal-card">
        <div className="login-logo-wrapper">
          <img 
            src={yoloLogo} 
            alt="YOLO Home Logo" 
            className="logout-logo-img"
          />
        </div>

        <h2 className="logout-title">Bạn có chắc chắn muốn đăng xuất không?</h2>
        <p className="logout-subtitle">
          Đăng xuất sẽ kết thúc phiên làm việc hiện tại của bạn. Bạn cần đăng nhập lại để điều khiển thiết bị hoặc truy cập các quy trình tự động hóa của mình.
        </p>

        <div className="logout-stats-box">
          <div className="stat-column">
            <span className="stat-label">Số Hub đang hoạt động</span>
            <span className="stat-number text-green">04</span>
          </div>

          <div className="stat-divider"></div>

          <div className="stat-column">
            <span className="stat-label">Tổng số thiết bị</span>
            <span className="stat-number text-green">28</span>
          </div>
        </div>

        <div className="logout-actions-vertical">
          <button className="btn-confirm-logout" onClick={ handleLogout }>
            <LogOut size={18} />
            <span>Đăng xuất</span>
          </button>

          <button className="btn-cancel-logout" onClick={ handleCancel }>
            Hủy
          </button>
        </div>

        <div className="logout-card-footer">
          <ShieldCheck size={14} color="#94a3b8" />
          <span>Quản lý phiên bảo mật</span>
        </div>
      </div>
    </div>
  );
};

export default Logout;
