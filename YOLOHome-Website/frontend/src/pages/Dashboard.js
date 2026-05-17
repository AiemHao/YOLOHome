import React, { useState, useEffect } from 'react';
import { fetchLatestSensors, fetchActiveAlerts, resolveAlert } from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import './Dashboard.css';

const dataTemp = [
  { name: 'Jan', value: 30 }, { name: 'Feb', value: 42 }, { name: 'Mar', value: 38 },
  { name: 'Apr', value: 40 }, { name: 'May', value: 35 }, { name: 'Jun', value: 35 },
  { name: 'Jul', value: 36 }, { name: 'Aug', value: 36 }, { name: 'Sep', value: 35 },
  { name: 'Oct', value: 32 }, { name: 'Nov', value: 30 },
];

const dataHumid = [
  { name: 'Jan', value: 60 }, { name: 'Feb', value: 80 }, { name: 'Mar', value: 75 },
  { name: 'Apr', value: 78 }, { name: 'May', value: 75 }, { name: 'Jun', value: 85 },
  { name: 'Jul', value: 72 }, { name: 'Aug', value: 74 }, { name: 'Sep', value: 70 },
  { name: 'Oct', value: 60 }, { name: 'Nov', value: 58 },
];

const dataLight = [
  { name: 'Jan', value: 60 }, { name: 'Feb', value: 80 }, { name: 'Mar', value: 75 },
  { name: 'Apr', value: 78 }, { name: 'May', value: 75 }, { name: 'Jun', value: 85 },
  { name: 'Jul', value: 72 }, { name: 'Aug', value: 74 }, { name: 'Sep', value: 70 },
  { name: 'Oct', value: 60 }, { name: 'Nov', value: 58 },
];

const Dashboard = () => {
  const [sensorData, setSensorData] = useState({
    temperature: 31,
    humidity: 6,
    light: 334
  });
  const [alerts, setAlerts] = useState([]);

  const ALERT_TYPE_LABELS = {
    temperature: 'Nhiệt độ',
    humidity: 'Độ ẩm',
    light: 'Ánh sáng',
    system: 'Hệ thống'
  };

  const normalizeAlertType = (type) => String(type || '').trim().toLowerCase();

  const translateAlertMessage = (message) => {
    if (!message) {
      return '';
    }
    let translated = message;
    translated = translated.replace('Threshold triggered:', 'Vượt ngưỡng:');
    translated = translated.replace('Sensor=', 'Cảm biến=');
    translated = translated.replace('value=', 'giá trị=');
    translated = translated.replace('Dark Environment', 'Môi trường tối');
    translated = translated.replace('Bright Environment', 'Môi trường sáng');
    translated = translated.replace('High Temperature', 'Nhiệt độ cao');
    translated = translated.replace('Low Temperature', 'Nhiệt độ thấp');
    translated = translated.replace('High Humidity', 'Độ ẩm cao');
    translated = translated.replace('Low Humidity', 'Độ ẩm thấp');
    return translated;
  };

  const fetchSensorData = async () => {
    try {
      const data = await fetchLatestSensors();
      if (data && data.success && data.data) {
        if (Array.isArray(data.data)) {
          let temp = '--', humi = '--', light = '--', latestTime = '--';
          data.data.forEach(item => {
            const type = (item.sensorType || '').toLowerCase();
            if (type.includes('temp') && temp === '--') { temp = item.value; if(latestTime==='--') latestTime = item.timestamp; }
            if (type.includes('humi') && humi === '--') { humi = item.value; if(latestTime==='--') latestTime = item.timestamp; }
            if (type.includes('light') && light === '--') { light = item.value; if(latestTime==='--') latestTime = item.timestamp; }
          });
          
          const timeStr = latestTime !== '--' ? new Date(latestTime).toLocaleTimeString() : '--:--:--';
          setSensorData({ temperature: temp, humidity: humi, light: light, timestamp: timeStr });
        } else {
          setSensorData(data.data);
        }
      }
    } catch (err) {
      console.error('Failed to fetch sensor data:', err);
    }
  };

  useEffect(() => {
    fetchSensorData();
    const fetchAlerts = async () => {
      try {
        const data = await fetchActiveAlerts();
        if (data && data.success && Array.isArray(data.data)) {
          setAlerts(data.data);
        }
      } catch (err) {
        console.error('Failed to fetch alerts:', err);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchSensorData, 5000);
    const alertInterval = setInterval(fetchAlerts, 5000);
    return () => {
      clearInterval(interval);
      clearInterval(alertInterval);
    };
  }, []);

  const handleResolveAlert = async (alertId) => {
    try {
      const data = await resolveAlert(alertId);
      if (data && data.success) {
        setAlerts((prev) => prev.filter((item) => item._id !== alertId));
      }
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <h1>Dashboard</h1>
      </header>

      <div className="dashboard-content">
        <div className="charts-column">
          
          <div className="chart-card" style={{backgroundColor: '#FPFBED'}}>
            <div className="chart-title">
               <span style={{color: '#E06C00', fontSize: '24px', marginRight: '10px'}}>🌡️</span>
               Nhiệt độ
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={dataTemp}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} />
                  <YAxis axisLine={false} tickLine={false} domain={[20, 60]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#E06C00" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card" style={{backgroundColor: '#E1F3FE'}}>
            <div className="chart-title">
               <span style={{color: '#343BFF', fontSize: '24px', marginRight: '10px'}}>💧</span>
               Độ ẩm
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={dataHumid}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} />
                  <YAxis axisLine={false} tickLine={false} domain={[40, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#343BFF" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card" style={{backgroundColor: '#DEFFDB'}}>
            <div className="chart-title">
               <span style={{color: '#DEFFDB', fontSize: '24px', marginRight: '10px'}}>💡</span>
               Cường độ ánh sáng
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={dataLight}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} />
                  <YAxis axisLine={false} tickLine={false} domain={[40, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#41BCFF" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>

        <div className="summary-column">
          <div className="summary-card">
            <h3>Thông tin chung</h3>
            
            <div className="summary-row">
              <div className="summary-item">
                <span className="summary-val" style={{color: '#E63946'}}>{sensorData.temperature}°</span>
                <span className="summary-label">Nhiệt độ</span>
              </div>
              <div className="summary-item">
                <span className="summary-val" style={{color: '#3ABCEE'}}>{sensorData.humidity}%</span>
                <span className="summary-label">Độ ẩm</span>
              </div>
            </div>

            <div className="summary-item mt-4">
              <span className="summary-val" style={{color: '#E06C00'}}>{sensorData.light} <span style={{fontSize: '18px'}}>lux</span></span>
              <span className="summary-label">Ánh sáng</span>
            </div>
          </div>

          {alerts.length > 0 && (
            <div className="alert-card alert-card-active">
            <div className="alert-header">
              <h3>Cảnh báo ngưỡng</h3>
              <span className="alert-count">{alerts.length}</span>
            </div>
            <div className="alert-list">
              {alerts.map((alert) => (
                <div key={alert._id} className={`alert-item alert-${(alert.severity || 'INFO').toLowerCase()}`}>
                  <div className="alert-main">
                    <div className="alert-title">
                      {ALERT_TYPE_LABELS[normalizeAlertType(alert.type)] || alert.type}
                    </div>
                    <div className="alert-message">{translateAlertMessage(alert.message)}</div>
                    <div className="alert-meta">
                      <span>Giá trị: {alert.value}</span>
                      <span>Ngưỡng: {alert.condition} {alert.threshold}</span>
                    </div>
                  </div>
                  <button
                    className="alert-resolve"
                    onClick={() => handleResolveAlert(alert._id)}
                  >
                    Xác nhận
                  </button>
                </div>
              ))}
            </div>
          </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
