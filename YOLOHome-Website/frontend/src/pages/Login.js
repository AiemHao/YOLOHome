import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import yoloLogo from './YOLO-03.png';
import { loginUser } from '../services/api';
import './Login.css';

const TEST_ACCOUNT = {
  username: 'admin',
  password: '123'
};

const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await loginUser(username, password);

      if (!data.success) {
        throw new Error(data.message || 'Đăng nhập thất bại');
      }

      localStorage.setItem('user', JSON.stringify(data.data));
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillTestAccount = () => {
    setUsername(TEST_ACCOUNT.username);
    setPassword(TEST_ACCOUNT.password);
    setError(null);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        
        <div className="login-logo">
          <img src={yoloLogo} alt="YOLO Home Logo" style={{width: '300px', height: 'auto'}} />
        </div>

        <form className="login-form" onSubmit={handleLogin}>
          {error && <div style={{color: 'red', marginBottom: '15px', textAlign: 'center', fontWeight: '500'}}>{error}</div>}

          <div className="test-account-box">
            <div className="test-account-title">Tài khoản test</div>
            <div className="test-account-row">
              <span>Username:</span>
              <strong>{TEST_ACCOUNT.username}</strong>
            </div>
            <div className="test-account-row">
              <span>Password:</span>
              <strong>{TEST_ACCOUNT.password}</strong>
            </div>
            <button type="button" className="test-account-btn" onClick={handleFillTestAccount}>
              Dùng tài khoản test
            </button>
          </div>
          
          <input 
            type="text" 
            placeholder="Nhập username" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          
          <div className="password-input-container">
            <input 
              type={showPassword ? "text" : "password"} 
              placeholder="Nhập password" 
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

          <div className="forgot-password">
            <a href="#forgot" onClick={(e) => e.preventDefault()}>Quên mật khẩu?</a>
          </div>

          <button type="submit" className="btn-primary" style={{textAlign: 'center', textDecoration: 'none', display: 'block'}} disabled={isLoading}>
            {isLoading ? 'Đang xử lý...' : 'Đăng nhập'}
          </button>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <span style={{ color: '#555' }}>Chưa có tài khoản? </span>
            <Link to="/signup" style={{ color: '#1CD0A0', textDecoration: 'none', fontWeight: '600' }}>
              Đăng ký ngay
            </Link>
          </div>
        </form>

      </div>
    </div>
  );
};

export default Login;
