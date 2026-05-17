import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import VoiceControl from './VoiceControl';
import './Layout.css';

const Layout = () => {
  return (
    <div className="layout-container">
      <Sidebar />
      <main className="main-content">
        <Outlet />
      </main>
      <VoiceControl />
    </div>
  );
};

export default Layout;
