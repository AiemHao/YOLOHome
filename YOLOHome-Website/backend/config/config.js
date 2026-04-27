import dotenv from 'dotenv';

dotenv.config();

const config = {
    port: process.env.PORT || 5000,
    mongoURI: process.env.MONGO_URI || 'mongodb://localhost:27017/yolohome',
    nodeEnv: process.env.NODE_ENV || 'development',
    corsOrigin: process.env.CORS_ORIGIN || '*'
};

// Validate required environment variables
const requiredVars = ['MONGO_URI'];
for (const envVar of requiredVars) {
    if (!process.env[envVar]) {
        console.error(`Error: Missing required environment variable: ${envVar}`);
        process.exit(1);
    }
}

export default config;
