import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Sliders, Mic, HelpCircle, LogOut } from 'lucide-react';
import './Sidebar.css';

const Sidebar = () => {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon-box">
          <Sliders size={18} color="#10b981" />
        </div>
        <div className="brand-text">
          <span className="brand-title">SmartHome</span>
        </div>
      </div>
      
      <nav className="sidebar-nav-container">
        <div className="nav-group">
          <NavLink to="/dashboard" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
            <LayoutDashboard size={20} className="link-icon" />
            <span>Dashboard</span>
          </NavLink>
          
          <NavLink to="/devices" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
            <Sliders size={20} className="link-icon" />
            <span>Quản lý thiết bị</span>
          </NavLink>

          <NavLink to="/logout" className={({isActive}) => isActive ? "sidebar-link active" : "sidebar-link"}>
            <LogOut size={20} className="link-icon" />
            <span>Đăng xuất</span>
          </NavLink>
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;