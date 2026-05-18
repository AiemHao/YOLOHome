import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import VoiceControl from './VoiceControl';
import { Bell, Search, Settings, UserCircle2 } from 'lucide-react';
import yoloLogo from '../pages/YOLO-03.png'; 
import './Layout.css';

const Layout = () => {
  return (
    <div className="layout-container">
      <header className="topbar">
        <div className="topbar-left-logo">
          <img src={yoloLogo} alt="YOLO Home Logo" className="header-logo-img" />
        </div>

        <div className="topbar-right-content">
          <div className="topbar-search">
            <Search size={18} className="topbar-search-icon" />
            <input
              type="text"
              placeholder="Search devices..."
              aria-label="Search devices"
            />
          </div>

          <div className="topbar-actions">
            <button className="topbar-icon-btn" aria-label="Notifications">
              <Bell size={20} />
            </button>
            <button className="topbar-icon-btn" aria-label="Settings">
              <Settings size={20} />
            </button>
            <button className="topbar-avatar" aria-label="Profile">
              <UserCircle2 size={24} />
            </button>
          </div>
        </div>
      </header>

      <div className="app-body-wrapper">
        <Sidebar />
        <main className="main-content">
          <Outlet />
        </main>
      </div>

      <VoiceControl />
    </div>
  );
};

export default Layout;