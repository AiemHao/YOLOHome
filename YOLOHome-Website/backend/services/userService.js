import User from '../models/User.js';

export class UserService {
    // Kiểm tra user tồn tại
    static async getUserByUsername(username) {
        return await User.findOne({ username });
    }

    // Tạo user mới
    static async createUser(userData) {
        const newUser = new User(userData);
        return await newUser.save();
    }

    // Kiểm tra password (tạm thời, sẽ thay bằng bcrypt sau)
    static validatePassword(inputPassword, storedPassword) {
        return inputPassword === storedPassword;
    }

    // Lấy user info (không include password)
    static getUserInfo(user) {
        return {
            username: user.username,
            fullName: user.fullName,
            createdAt: user.createdAt
        };
    }
}
