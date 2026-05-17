const BASE_URL = 'http://localhost:5000/api';

// --- SENSOR APIs ---
export const fetchLatestSensors = async () => {
    try {
        const response = await fetch(`${BASE_URL}/sensors/latest`);
        const data = await response.json();
        return data; // Returns { success: true, data: { temperature, humidity, light, timestamp } }
    } catch (error) {
        console.error("Lỗi khi lấy dữ liệu cảm biến:", error);
    }
};

// --- DEVICE APIs ---
export const fetchLatestDevices = async () => {
    try {
        const response = await fetch(`${BASE_URL}/devices/latest`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Lỗi khi lấy dữ liệu thiết bị:", error);
    }
};

export const controlDevice = async (deviceName, action, deviceType = '') => {
    try {
        const response = await fetch(`${BASE_URL}/devices/control`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ deviceName, action, deviceType }),
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Lỗi điều khiển thiết bị:", error);
    }
};

// --- USER APIs ---
export const signupUser = async (username, password, fullName) => {
    try {
        const response = await fetch(`${BASE_URL}/users/signup`, {
            method: 'POST', //
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password, fullName }), //
        });
        const data = await response.json();
        
        // Ensure you return a standard structure that Signup.js expects
        if (response.status === 201) {
            return { success: true, data: data.data }; //
        } else {
            return { success: false, message: data.message }; //
        }
    } catch (error) {
        console.error("Lỗi đăng ký:", error);
        return { success: false, message: "Không thể kết nối tới server" };
    }
};

export const loginUser = async (username, password) => {
    try {
        const response = await fetch(`${BASE_URL}/users/login`, {
            method: 'POST', //
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }), //
        });
        const data = await response.json();
        
        if (response.status === 200) {
            return { success: true, data: data.data }; //
        } else {
            return { success: false, message: data.message }; //
        }
    } catch (error) {
        console.error("Lỗi đăng nhập:", error);
        return { success: false, message: "Không thể kết nối tới server" };
    }
};

// --- VOICE APIs ---
export const sendVoiceCommand = async (audioBlob) => {
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'command.wav');

        const response = await fetch(`${BASE_URL}/voice/command`, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Lỗi gửi lệnh giọng nói:", error);
        return { status: 'error', message: "Không thể kết nối tới server" };
    }
};