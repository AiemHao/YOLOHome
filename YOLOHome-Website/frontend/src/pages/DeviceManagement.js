import React, { useState, useEffect } from 'react';
import { fetchLatestDevices, controlDevice } from '../services/api';
import { Wrench, RefreshCw } from 'lucide-react';
import './DeviceManagement.css';

const DeviceManagement = () => {
  const [devices, setDevices] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDevices = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:5000/api/devices/latest');
      const data = await response.json();
      
      if (!data || !data.success) {
        throw new Error(data?.message || 'Không thể lấy dữ liệu thiết bị (Server có thể đang tắt)');
      }

      setDevices(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const pollDevices = async () => {
    try {
      const data = await fetchLatestDevices();
      if (data && data.success) {
        // Only update state if data exists, don't trigger loading spinners
        setDevices(prevDevices => {
          // Merge new statuses with existing loading states to preserve UI feedback
          return data.data.map(newDev => {
            const existing = prevDevices.find(d => d.deviceName === newDev.deviceName);
            return existing ? { ...newDev, isLoading: existing.isLoading } : newDev;
          });
        });
      }
    } catch (err) {
      // Silent error on polling
    }
  };

  const handleToggle = async (device) => {
    if (device.isLoading) return; // Prevent double clicks

    const newAction = device.status === 'on' ? 'off' : 'on';
    
    // Optimistic UI update
    setDevices(prevDevices => 
      prevDevices.map(d => 
        d.deviceName === device.deviceName ? { ...d, status: newAction, isLoading: true } : d
      )
    );

    try {
      const res = await controlDevice(device.deviceName, newAction, device.deviceType || device.deviceName.toLowerCase());
      
      if (res && res.success) {
        setDevices(prevDevices => 
          prevDevices.map(d => 
            d.deviceName === device.deviceName ? { ...d, isLoading: false } : d
          )
        );
      } else {
        throw new Error(res?.message || 'Không thể điều khiển thiết bị');
      }
    } catch (err) {
      alert("Lỗi: " + err.message);
      // Revert optimistic update on failure
      setDevices(prevDevices => 
        prevDevices.map(d => 
          d.deviceName === device.deviceName ? { ...d, status: device.status, isLoading: false } : d
        )
      );
    }
  };

  useEffect(() => {
    loadDevices();
    const interval = setInterval(pollDevices, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="devices-page">
      <header className="page-header" style={{display: 'flex', justifyContent: 'space-between', padding: '0 40px'}}>
        <div style={{width: '24px'}}></div>
        <h1>Quản lý thiết bị</h1>
        <button onClick={loadDevices} style={{background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center'}}>
          <RefreshCw size={24} color="#333" className={isLoading ? "spin" : ""} />
        </button>
      </header>
      
      <div className="devices-content">
        <div className="devices-list">
          {error && <div style={{color: 'red', textAlign: 'center'}}>{error}</div>}
          
          {!isLoading && devices.length === 0 && !error && (
            <div style={{textAlign: 'center', color: '#888'}}>Không có thiết bị nào.</div>
          )}

          {devices.map((device, idx) => (
            <div className="device-item" key={device.deviceName || idx}>
              <div className="device-info">
                <div className="device-icon">
                  <Wrench size={20} color="#1CD0A0" />
                </div>
                <span className="device-name">{device.deviceName}</span>
              </div>
              
              <label className="switch">
                <input 
                  type="checkbox" 
                  checked={device.status === 'on'} 
                  onChange={() => handleToggle(device)}
                  disabled={device.isLoading || isLoading}
                />
                <span className="slider" style={{ opacity: device.isLoading ? 0.6 : 1 }}></span>
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DeviceManagement;
