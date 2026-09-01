import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Load base data
const baseSensors = JSON.parse(readFileSync(join(__dirname, 'data', 'sensors.json'), 'utf-8'));
const baseUnits = JSON.parse(readFileSync(join(__dirname, 'data', 'units.json'), 'utf-8'));
const basePersons = JSON.parse(readFileSync(join(__dirname, 'data', 'persons.json'), 'utf-8'));

// Deep clone mutable state
let sensors = JSON.parse(JSON.stringify(baseSensors));
let units = JSON.parse(JSON.stringify(baseUnits));
let alertCounter = 104;

// Impact zone epicenter
const EPICENTER = { lat: 30.405, lng: 79.320 };
const IMPACT_RADIUS_KM = 3.5;

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

function randomWalk(value, step, min, max) {
  return clamp(value + (Math.random() - 0.5) * 2 * step, min, max);
}

function updateSensors() {
  sensors = sensors.map(s => {
    const rainfall = randomWalk(s.rainfall, 2, 0, 200);
    const soilMoisture = randomWalk(s.soilMoisture, 1, 10, 100);
    const tilt = randomWalk(s.tilt, 0.3, 0, 15);
    const alert = rainfall > 130 || soilMoisture > 85;
    return { ...s, rainfall: +rainfall.toFixed(1), soilMoisture: +soilMoisture.toFixed(1), tilt: +tilt.toFixed(2), alert };
  });
  return sensors;
}

function updateUnits() {
  units = units.map(u => {
    if (u.status !== 'EN ROUTE') return u;

    let idx = u.currentRouteIndex;
    if (idx < u.route.length - 1) {
      idx++;
    }

    const pos = u.route[idx];
    const dest = u.route[u.route.length - 1];
    const dist = haversineKm(pos[1], pos[0], dest[1], dest[0]);

    let status = u.status;
    let eta = u.eta;

    if (dist < 0.5 || idx >= u.route.length - 1) {
      status = 'ON SITE';
      eta = 0;
    } else {
      eta = Math.max(0, (u.eta || 0) - 2);
    }

    return {
      ...u,
      currentRouteIndex: idx,
      currentPosition: pos,
      status,
      eta
    };
  });
  return units;
}

function checkForNewAlert() {
  const triggered = sensors.filter(s => s.alert && s.rainfall > 138);
  if (triggered.length > 0 && Math.random() < 0.05) {
    alertCounter++;
    const src = triggered[Math.floor(Math.random() * triggered.length)];
    return {
      id: `A-${alertCounter}`,
      severity: src.rainfall > 140 ? 'HIGH' : src.rainfall > 130 ? 'MEDIUM' : 'LOW',
      location: src.name + ', Uttarakhand',
      lat: src.lat,
      lng: src.lng,
      trigger: `${src.rainfall}mm rain / 6hrs`,
      confidence: clamp(70 + Math.random() * 25, 70, 98).toFixed(0),
      timestamp: Date.now(),
      sensorId: src.id
    };
  }
  return null;
}

function getPersonStatuses() {
  return basePersons.map(p => {
    const dist = haversineKm(p.lat, p.lng, EPICENTER.lat, EPICENTER.lng);
    return {
      ...p,
      distanceToImpact: +dist.toFixed(2),
      status: dist < IMPACT_RADIUS_KM ? 'IN ZONE' : p.status === 'IN ZONE' ? 'SAFE' : p.status
    };
  });
}

export function startSimulation(io) {
  // Initial alerts
  const initialAlerts = [
    {
      id: 'A-104',
      severity: 'HIGH',
      location: 'Chamoli Ridge A, Uttarakhand',
      lat: 30.400,
      lng: 79.320,
      trigger: '142mm rain / 6hrs',
      confidence: '91',
      timestamp: Date.now() - 720000,
      sensorId: 'SNS-01'
    },
    {
      id: 'A-103',
      severity: 'HIGH',
      location: 'Chamoli Town, Uttarakhand',
      lat: 30.405,
      lng: 79.325,
      trigger: '138mm rain / 6hrs',
      confidence: '88',
      timestamp: Date.now() - 1800000,
      sensorId: 'SNS-15'
    },
    {
      id: 'A-102',
      severity: 'MEDIUM',
      location: 'Reni Village, Uttarakhand',
      lat: 30.415,
      lng: 79.308,
      trigger: '128mm rain / 6hrs',
      confidence: '76',
      timestamp: Date.now() - 3600000,
      sensorId: 'SNS-03'
    }
  ];

  io.on('connection', (socket) => {
    console.log(`Client connected: ${socket.id}`);

    // Send initial state
    socket.emit('init', {
      sensors: sensors,
      units: units.map(u => ({
        ...u,
        currentPosition: u.route[u.currentRouteIndex]
      })),
      persons: getPersonStatuses(),
      alerts: initialAlerts
    });

    socket.on('dispatch:all', () => {
      units = units.map(u =>
        u.status === 'STANDBY' ? { ...u, status: 'EN ROUTE', eta: 1800 + Math.floor(Math.random() * 600) } : u
      );
      io.emit('units:update', units.map(u => ({
        ...u,
        currentPosition: u.route[u.currentRouteIndex]
      })));
    });

    socket.on('notify:all', () => {
      io.emit('notification:sent', { message: 'Emergency SMS sent to all registered persons', count: basePersons.length, timestamp: Date.now() });
    });

    socket.on('disconnect', () => {
      console.log(`Client disconnected: ${socket.id}`);
    });
  });

  // Simulation loop — every 2 seconds
  setInterval(() => {
    const updatedSensors = updateSensors();
    const updatedUnits = updateUnits();
    const newAlert = checkForNewAlert();
    const persons = getPersonStatuses();

    io.emit('sensors:update', updatedSensors);
    io.emit('units:update', updatedUnits.map(u => ({
      ...u,
      currentPosition: u.route[u.currentRouteIndex]
    })));
    io.emit('persons:update', persons);

    if (newAlert) {
      io.emit('alert:new', newAlert);
    }
  }, 2000);
}

export { EPICENTER, IMPACT_RADIUS_KM };
