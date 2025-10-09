const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const opts = Object.assign({ headers: { 'Content-Type': 'application/json' } }, options);
  if (opts.body && typeof opts.body !== 'string' && !(opts.body instanceof FormData)) {
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, opts);
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch (e) {
    return text;
  }
}

export async function getHealth() {
  return request('/api/health');
}

export async function register(user) {
  return request('/api/register', { method: 'POST', body: user });
}

export async function login(credentials) {
  return request('/api/login', { method: 'POST', body: credentials });
}

export async function predict(symptoms) {
  return request('/api/predict', { method: 'POST', body: { symptoms } });
}

export async function imagePredict(formData) {
  const url = (process.env.REACT_APP_API_URL || 'http://localhost:5000') + '/api/image-predict';
  const res = await fetch(url, { method: 'POST', body: formData });
  return res.json();
}

export default { getHealth, register, login, predict, imagePredict };
