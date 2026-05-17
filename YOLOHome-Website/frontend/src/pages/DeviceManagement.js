import React, { useState, useEffect } from 'react';
import { fetchLatestDevices, controlDevice } from '../services/api';
import { Lightbulb, Fan, Settings, Filter, Plus, RefreshCw } from 'lucide-react';
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
        setDevices(prevDevices => {
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
    if (device.isLoading) return;

    const newAction = device.status === 'on' ? 'off' : 'on';
    
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

  const getDeviceConfig = (name) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('led')) {
      return {
        icon: <Lightbulb size={22} color="#0284c7" />,
        className: "icon-led",
        subtitle: "Độ sáng: 80%"
      };
    }
    if (lowerName.includes('fan')) {
      return {
        icon: <Fan size={22} color="#0d9488" />,
        className: "icon-fan",
      };
    }
    if (lowerName.includes('servo')) {
      return {
        icon: <Settings size={22} color="#0d9488" />,
        className: "icon-servo",
      };
    }
    return {
      icon: <Settings size={22} color="#64748b" />,
      className: "icon-default",
      subtitle: "Đã kết nối"
    };
  };

  return (
    <div className="devices-container">
      <div className="devices-header-section">
        <div className="header-text-group">
          <h1>Các thiết bị được kết nối</h1>
          <p>Quản lý và giám sát cả {devices.length} thiết bị thông minh đang hoạt động trong nhà bạn.</p>
        </div>
        
        <div className="header-action-buttons">
          <button className="btn-filter">
            <Filter size={16} />
            <span>Filter</span>
          </button>
          
          <button className="btn-add-device">
            <Plus size={16} />
            <span>Add Device</span>
          </button>
        </div>
      </div>

      {error && <div className="device-status-msg error">{error}</div>}
      {!isLoading && devices.length === 0 && !error && (
        <div className="device-status-msg empty">Không tìm thấy thiết bị nào đang hoạt động.</div>
      )}

      <div className="devices-grid-layout">
        {devices.map((device, idx) => {
          const config = getDeviceConfig(device.deviceName);
          return (
            <div className={`device-card-item ${device.status === 'on' ? 'active-state' : ''}`} key={device.deviceName || idx}>
              <div className="card-top-row">
                <div className={`card-icon-wrapper ${config.className}`}>
                  {config.icon}
                </div>
                
                <label className="custom-toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={device.status === 'on'} 
                    onChange={() => handleToggle(device)}
                    disabled={device.isLoading || isLoading}
                  />
                  <span className="toggle-slider" style={{ opacity: device.isLoading ? 0.6 : 1 }}></span>
                </label>
              </div>

              <div className="card-bottom-details">
                <h3 className="card-device-title">{device.deviceName.toUpperCase()}</h3>
                <span className="card-device-subtitle">{config.subtitle}</span>
                <div className="card-status-indicator">
                  <span className="dot-active"></span>
                  <span className="status-text">Active</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DeviceManagement;