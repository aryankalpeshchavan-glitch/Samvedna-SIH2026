import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import useStore from '../store/useStore';

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:3001';

export default function useSocket() {
  const socketRef = useRef(null);
  const {
    setConnected, setAlerts, addAlert,
    updateSensors, setPersons, setUnits, addToast
  } = useStore();

  useEffect(() => {
    const socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('🟢 Connected to server');
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('🔴 Disconnected from server');
      setConnected(false);
    });

    socket.on('init', (data) => {
      if (data.alerts) setAlerts(data.alerts);
      if (data.sensors) updateSensors(data.sensors);
      if (data.persons) setPersons(data.persons);
      if (data.units) setUnits(data.units);
    });

    socket.on('sensors:update', (sensors) => {
      updateSensors(sensors);
    });

    socket.on('units:update', (units) => {
      setUnits(units);
    });

    socket.on('persons:update', (persons) => {
      setPersons(persons);
    });

    socket.on('alert:new', (alert) => {
      addAlert(alert);
    });

    socket.on('notification:sent', (data) => {
      addToast(`✓ ${data.message} (${data.count} people)`);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return socketRef;
}
