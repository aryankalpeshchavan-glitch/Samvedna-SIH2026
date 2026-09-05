import { create } from 'zustand';

const useStore = create((set, get) => ({
  // Connection
  connected: false,
  setConnected: (connected) => set({ connected }),

  // Alerts
  alerts: [],
  setAlerts: (alerts) => set({ alerts }),
  addAlert: (alert) => set((s) => ({ alerts: [alert, ...s.alerts].slice(0, 50) })),

  // Sensors
  sensors: [],
  setSensors: (sensors) => set({ sensors }),
  sensorHistory: {},
  updateSensors: (sensors) => set((s) => {
    const history = { ...s.sensorHistory };
    sensors.forEach((sensor) => {
      if (!history[sensor.id]) history[sensor.id] = [];
      history[sensor.id] = [...history[sensor.id].slice(-9), {
        rainfall: sensor.rainfall,
        soilMoisture: sensor.soilMoisture,
        tilt: sensor.tilt
      }];
    });
    return { sensors, sensorHistory: history };
  }),

  // Persons
  persons: [],
  setPersons: (persons) => set({ persons }),

  // Units
  units: [],
  setUnits: (units) => set({ units }),

  // Selections (for map flyTo)
  selectedAlert: null,
  selectAlert: (alert) => set({ selectedAlert: alert, selectedPerson: null, selectedUnit: null }),

  selectedPerson: null,
  selectPerson: (person) => set({ selectedPerson: person, selectedAlert: null, selectedUnit: null }),

  selectedUnit: null,
  selectUnit: (unit) => set({ selectedUnit: unit, selectedAlert: null, selectedPerson: null }),

  clearSelection: () => set({ selectedAlert: null, selectedPerson: null, selectedUnit: null }),

  // Map layers
  layers: {
    riskHeatmap: true,
    impactZone: true,
    sensors: true,
    dispatchUnits: true,
    persons: true
  },
  toggleLayer: (layer) => set((s) => ({
    layers: { ...s.layers, [layer]: !s.layers[layer] }
  })),

  // Prediction card
  showPrediction: false,
  setShowPrediction: (show) => set({ showPrediction: show }),

  // Panel collapse
  leftCollapsed: false,
  rightCollapsed: false,
  toggleLeft: () => set((s) => ({ leftCollapsed: !s.leftCollapsed })),
  toggleRight: () => set((s) => ({ rightCollapsed: !s.rightCollapsed })),

  // Toasts
  toasts: [],
  addToast: (message) => {
    const id = Date.now();
    set((s) => ({ toasts: [...s.toasts, { id, message }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  }
}));

export default useStore;
