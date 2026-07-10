import { create } from 'zustand';
import { JobInfo } from '../api/commands';

interface JobState {
  jobs: JobInfo[];
  activeJobId: string | null;
  results: Record<string, any>;

  addJob: (job: JobInfo) => void;
  updateJob: (job: JobInfo) => void;
  setActiveJob: (jobId: string | null) => void;
  setResults: (jobId: string, results: any) => void;
  clearJobs: () => void;
}

export const useJobStore = create<JobState>((set) => ({
  jobs: [],
  activeJobId: null,
  results: {},

  addJob: (job) =>
    set((state) => ({
      jobs: [job, ...state.jobs],
      activeJobId: job.job_id,
    })),

  updateJob: (job) =>
    set((state) => ({
      jobs: state.jobs.map((j) => (j.job_id === job.job_id ? job : j)),
    })),

  setActiveJob: (jobId) => set({ activeJobId: jobId }),

  setResults: (jobId, results) =>
    set((state) => ({
      results: { ...state.results, [jobId]: results },
    })),

  clearJobs: () => set({ jobs: [], activeJobId: null, results: {} }),
}));
