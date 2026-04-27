import mongoose from 'mongoose';
import config from './config.js';

export const connectDatabase = async () => {
    try {
        await mongoose.connect(config.mongoURI, {

        });
        console.log('Connected to MongoDB Atlas successfully!');
    } catch (err) {
        console.error('MongoDB connection error:', err.message);
        process.exit(1);
    }
};

export const closeDatabase = async () => {
    try {
        await mongoose.connection.close();
        console.log('MongoDB connection closed');
    } catch (err) {
        console.error('Error closing MongoDB connection:', err);
    }
};
