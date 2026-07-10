import { create } from 'zustand';
import { HardwareInfo } from '../api/commands';

interface HardwareState {
  backends: HardwareInfo[];
  selectedBackend: string;
  setBackends: (backends: HardwareInfo[]) => void;
  selectBackend: (name: string) => void;
}

export const useHardwareStore = create<HardwareState>((set) => ({
  backends: [],
  selectedBackend: 'AbirQu Simulator',
  setBackends: (backends) => set({ backends }),
  selectBackend: (name) => set({ selectedBackend: name }),
}));
