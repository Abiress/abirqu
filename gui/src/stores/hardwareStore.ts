import { create } from 'zustand';
import { HardwareInfo } from '../api/commands';

export interface NoiseConfig {
  depolarizing: number;
  amplitudeDamping: number;
  phaseDamping: number;
  readoutError: number;
  enabled: boolean;
}

interface HardwareState {
  backends: HardwareInfo[];
  selectedBackend: string;
  noiseConfig: NoiseConfig;
  setBackends: (backends: HardwareInfo[]) => void;
  selectBackend: (name: string) => void;
  setNoiseConfig: (config: NoiseConfig) => void;
}

export const useHardwareStore = create<HardwareState>((set) => ({
  backends: [],
  selectedBackend: 'AbirQu Simulator',
  noiseConfig: { depolarizing: 0, amplitudeDamping: 0, phaseDamping: 0, readoutError: 0, enabled: false },
  setBackends: (backends) => set({ backends }),
  selectBackend: (name) => set({ selectedBackend: name }),
  setNoiseConfig: (config) => set({ noiseConfig: config }),
}));
