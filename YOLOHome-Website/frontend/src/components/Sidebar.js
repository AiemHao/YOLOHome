import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Wrench, LogOut } from 'lucide-react';
import yoloLogo from '../pages/YOLO-03.png';
import './Sidebar.css';

const Sidebar = () => {
  return (
    <div className="sidebar">
      <div className="sidebar-top">
        <div className="logo-box">
          <img src={yoloLogo} alt="YOLO Home Logo" style={{width: '60px', height: 'auto'}} />
          <span className="logo-text" style={{ color: '#1CD0A0', fontWeight: 'bold', marginTop: '5px', fontSize: '14px', letterSpacing: '1px' }}>YOLO:HOME</span>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <div className="icon-wrapper" style={{color: '#28D6AC'}}><LayoutDashboard size={24} /></div>
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/devices" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <div className="icon-wrapper" style={{color: '#28D6AC'}}><Wrench size={24} /></div>
          <span>Quản lý thiết bị</span>
        </NavLink>
        <NavLink 
          to="/logout" 
          className={({isActive}) => isActive ? "nav-item active" : "nav-item"}
        >
          <div className="icon-wrapper" style={{color: '#28D6AC'}}><LogOut size={24} /></div>
          <span>Đăng xuất</span>
        </NavLink>
      </nav>

      <div className="sidebar-bottom"></div>
    </div>
  );
};

export default Sidebar;
