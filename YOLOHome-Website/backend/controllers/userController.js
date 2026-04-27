import { UserService } from '../services/userService.js';

export class UserController {
    // Đăng ký tài khoản
    static async signup(req, res, next) {
        try {
            const { username, password, fullName } = req.body;

            // Validate input
            if (!username || !password) {
                return res.status(400).json({
                    success: false,
                    message: 'Username và password là bắt buộc'
                });
            }

            // Kiểm tra user tồn tại
            const existingUser = await UserService.getUserByUsername(username);
            if (existingUser) {
                return res.status(400).json({
                    success: false,
                    message: 'Tên đăng nhập đã tồn tại!'
                });
            }

            // Tạo user mới
            const newUser = await UserService.createUser({
                username,
                password,
                fullName
            });

            res.status(201).json({
                success: true,
                message: 'Đăng ký tài khoản thành công!',
                data: UserService.getUserInfo(newUser)
            });
        } catch (error) {
            next(error);
        }
    }

    // Đăng nhập
    static async login(req, res, next) {
        try {
            const { username, password } = req.body;

            // Validate input
            if (!username || !password) {
                return res.status(400).json({
                    success: false,
                    message: 'Username và password là bắt buộc'
                });
            }

            // Tìm user
            const user = await UserService.getUserByUsername(username);
            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: 'Tài khoản không tồn tại!'
                });
            }

            // Kiểm tra password
            const isPasswordValid = UserService.validatePassword(password, user.password);
            if (!isPasswordValid) {
                return res.status(401).json({
                    success: false,
                    message: 'Sai mật khẩu!'
                });
            }

            // Đăng nhập thành công
            res.status(200).json({
                success: true,
                message: 'Đăng nhập thành công!',
                data: UserService.getUserInfo(user)
            });
        } catch (error) {
            next(error);
        }
    }
}
