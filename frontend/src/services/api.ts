import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

api.interceptors.response.use(
  res => res,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Request failed';
    console.error('[API Error]', msg);
    return Promise.reject(err);
  }
);

export const createJob = (title: string, description: string) => {
  const form = new FormData();
  form.append('title', title);
  form.append('description', description);
  return api.post('/jobs/', form);
};

export const listJobs = () => api.get('/jobs/');
export const getJob = (id: number) => api.get(`/jobs/${id}`);

export const uploadCandidates = (jobId: number, file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post(`/jobs/${jobId}/upload-candidates`, form);
};

export const uploadResumes = (jobId: number, files: File[]) => {
  const form = new FormData();
  files.forEach(f => form.append('files', f));
  return api.post(`/jobs/${jobId}/upload-resumes`, form);
};

export const uploadTestResults = (jobId: number, file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post(`/jobs/${jobId}/upload-test-results`, form);
};

export const processResumes = (jobId: number) => api.post(`/pipeline/${jobId}/process-resumes`);
export const analyzeGithub = (jobId: number) => api.post(`/pipeline/${jobId}/analyze-github`);
export const evaluateCandidates = (jobId: number) => api.post(`/pipeline/${jobId}/evaluate`);
export const shortlistCandidates = (jobId: number, topN: number, minScore: number) =>
  api.post(`/pipeline/${jobId}/shortlist`, { top_n: topN, min_score: minScore });
export const sendTestLinks = (jobId: number, testLink: string) =>
  api.post(`/pipeline/${jobId}/send-test-links`, { test_link: testLink });
export const scoreTests = (jobId: number, minTestScore: number) =>
  api.post(`/pipeline/${jobId}/score-tests`, { min_test_score: minTestScore });
export const scheduleInterviews = (jobId: number, topN: number, startDate?: string) =>
  api.post(`/pipeline/${jobId}/schedule-interviews`, { top_n: topN, start_date: startDate });
export const runFullPipeline = (jobId: number, topN: number, minScore: number) =>
  api.post(`/pipeline/${jobId}/run-full-pipeline`, { top_n: topN, min_score: minScore });

export default api;
