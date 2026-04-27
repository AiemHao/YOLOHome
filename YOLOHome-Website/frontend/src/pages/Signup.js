import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import yoloLogo from './YOLO-03.png';
import { signupUser } from '../services/api';
import './Login.css'; // Reusing Login's styles for consistency

const Signup = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      const data = await signupUser(username, password, fullName);

      if (!data.success) {
        throw new Error(data.message || 'Đăng ký thất bại');
      }

      setSuccess('Đăng ký thành công! Đang chuyển hướng...');
      setTimeout(() => {
        navigate('/'); // Redirect to login
      }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card" style={{ padding: '30px' }}>
        
        <div className="login-logo">
          <img src={yoloLogo} alt="YOLO Home Logo" style={{width: '240px', height: 'auto', marginBottom: '10px'}} />
        </div>

        <h3 style={{ textAlign: 'center', color: '#1CD0A0', marginBottom: '20px' }}>Đăng Ký Tài Khoản</h3>

        <form className="login-form" onSubmit={handleSignup}>
          {error && <div style={{color: 'red', marginBottom: '15px', textAlign: 'center', fontWeight: '500'}}>{error}</div>}
          {success && <div style={{color: '#1CD0A0', marginBottom: '15px', textAlign: 'center', fontWeight: '500'}}>{success}</div>}
          
          <input 
            type="text" 
            placeholder="Họ và Tên (VD: Administrator)" 
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            style={{ marginBottom: '15px' }}
          />

          <input 
            type="text" 
            placeholder="Tên đăng nhập (username)" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ marginBottom: '15px' }}
          />
          
          <div className="password-input-container" style={{ marginBottom: '20px' }}>
            <input 
              type={showPassword ? "text" : "password"} 
              placeholder="Mật khẩu" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button 
              type="button" 
              className="eye-icon"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={20} color="#1CD0A0" /> : <Eye size={20} color="#1CD0A0" />}
            </button>
          </div>

          <button type="submit" className="btn-primary" style={{textAlign: 'center', display: 'block', width: '100%'}} disabled={isLoading}>
            {isLoading ? 'Đang xử lý...' : 'Đăng Ký'}
          </button>
          
          <div style={{ textAlign: 'center', marginTop: '15px' }}>
            <span style={{ color: '#555' }}>Đã có tài khoản? </span>
            <a href="/" onClick={(e) => { e.preventDefault(); navigate('/'); }} style={{ color: '#1CD0A0', textDecoration: 'none', fontWeight: '600' }}>
              Đăng nhập ngay
            </a>
          </div>
        </form>

      </div>
    </div>
  );
};

export default Signup;
