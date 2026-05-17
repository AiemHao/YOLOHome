import React, { useState, useEffect } from 'react';
import { fetchLatestSensors, fetchActiveAlerts, resolveAlert } from '../services/api';
import './Dashboard.css';

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
    if (!message) return '';
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
            if (type.includes('temp') && temp === '--') { temp = item.value; if (latestTime === '--') latestTime = item.timestamp; }
            if (type.includes('humi') && humi === '--') { humi = item.value; if (latestTime === '--') latestTime = item.timestamp; }
            if (type.includes('light') && light === '--') { light = item.value; if (latestTime === '--') latestTime = item.timestamp; }
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

  const cards = [
    {
      title: 'Nhiệt độ',
      value: `${sensorData.temperature}°C`,
      accent: '#21c7a8',
      badgeBg: '#e7fbf6',
      icon: '🌡️',
      watermark: '🌡️'
    },
    {
      title: 'Độ ẩm',
      value: `${sensorData.humidity}%`,
      accent: '#3aa8ff',
      badgeBg: '#eaf5ff',
      icon: '💧',
      watermark: '💧'
    },
    {
      title: 'Cường độ ánh sáng',
      value: `${sensorData.light} lx`,
      accent: '#f59e0b',
      badgeBg: '#fff7e6',
      icon: '☀️',
      watermark: '☀️'
    }
  ];

  return (
    <div className="dashboard-page">
      <section className="dashboard-heading">
        <p className="dashboard-eyebrow">TỔNG QUAN VỀ MÔI TRƯỜNG</p>
        <h1>Thông tin chung</h1>
      </section>

      <section className="dashboard-grid">
        {cards.map((card) => (
          <article
            key={card.title}
            className="info-card"
            style={{ '--accent': card.accent }}
          >
            <div className="info-card-top">
              <div className="info-badge" style={{ backgroundColor: card.badgeBg }}>
                <span className="info-badge-icon">{card.icon}</span>
              </div>
              <div className="info-watermark">{card.watermark}</div>
            </div>

            <div className="info-card-body">
              <div className="info-title">{card.title}</div>
              <div className="info-value">{card.value}</div>
              <div className={`info-note ${card.noteClass}`}>{card.note}</div>
            </div>
          </article>
        ))}
      </section>

      {alerts.length > 0 && (
        <div className="alert-card alert-card-active">
          <div className="alert-header">
            <h3>Cảnh báo ngưỡng</h3>
            <span className="alert-count">{alerts.length}</span>
          </div>
          <div className="alert-list">
            {alerts.map((alert) => (
              <div
                key={alert._id}
                className={`alert-item alert-${(alert.severity || 'INFO').toLowerCase()}`}
              >
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
  );
};

export default Dashboard;