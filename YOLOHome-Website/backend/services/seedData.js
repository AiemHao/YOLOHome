import mongoose from 'mongoose';
import User from '../models/User.js';
import Sensor from '../models/Sensor.js';
import Device from '../models/Device.js';

const defaultUsers = [
    {
        _id: new mongoose.Types.ObjectId('69c9636ffa95cab8db06f49a'),
        username: 'admin',
        password: '123',
        fullName: 'admin',
        createdAt: new Date('2026-03-29T17:37:51.889Z')
    }
];

const defaultSensors = [
    {
        _id: new mongoose.Types.ObjectId('69c9f9ce53d100e64537eff8'),
        temperature: 27.2,
        humidity: 49.8,
        light: 78,
        timestamp: new Date('2026-03-30T04:19:26.702Z')
    }
];

const defaultDevices = [
    {
        _id: new mongoose.Types.ObjectId('69c9f9ce53d100e64537effa'),
        light: 'off',
        fan: 'off',
        servo: 'off',
        timestamp: new Date('2026-03-30T04:19:26.736Z')
    }
];

export const seedDefaultData = async () => {
    const [userCount, sensorCount, deviceCount] = await Promise.all([
        User.countDocuments(),
        Sensor.countDocuments(),
        Device.countDocuments()
    ]);

    if (userCount === 0) {
        console.log('Seeding default User data...');
        await User.insertMany(defaultUsers);
        console.log('Default User data seeded.');
    } else {
        console.log('User data already exists. Skip seeding User.');
    }

    if (sensorCount === 0) {
        console.log('Seeding default Sensor data...');
        await Sensor.insertMany(defaultSensors);
        console.log('Default Sensor data seeded.');
    } else {
        console.log('Sensor data already exists. Skip seeding Sensor.');
    }

    if (deviceCount === 0) {
        console.log('Seeding default Device data...');
        await Device.insertMany(defaultDevices);
        console.log('Default Device data seeded.');
    } else {
        console.log('Device data already exists. Skip seeding Device.');
    }
};
