import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import dotenv from 'dotenv';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { startSimulation } from './simulator.js';

dotenv.config();

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 3001;

const app = express();
app.use(cors());
app.use(express.json());

// REST endpoints for initial data load
app.get('/api/persons', (_req, res) => {
  const data = JSON.parse(readFileSync(join(__dirname, 'data', 'persons.json'), 'utf-8'));
  res.json(data);
});

app.get('/api/units', (_req, res) => {
  const data = JSON.parse(readFileSync(join(__dirname, 'data', 'units.json'), 'utf-8'));
  res.json(data);
});

app.get('/api/sensors', (_req, res) => {
  const data = JSON.parse(readFileSync(join(__dirname, 'data', 'sensors.json'), 'utf-8'));
  res.json(data);
});

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

const httpServer = createServer(app);

const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Start real-time simulation
startSimulation(io);

httpServer.listen(PORT, () => {
  console.log(`🌍 Landslide Dashboard Server running on http://localhost:${PORT}`);
  console.log(`📡 WebSocket ready for connections`);
  console.log(`🔄 Simulation active — emitting updates every 2s`);
});
