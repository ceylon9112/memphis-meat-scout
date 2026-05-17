import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Attach JWT for admin requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mms_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ─── Public ──────────────────────────────────────────────────────────────────

export const getDeals = (params = {}) => api.get('/deals', { params }).then(r => r.data)
export const flagDeal = (id) => api.post(`/deals/${id}/flag`).then(r => r.data)
export const getCuts = () => api.get('/cuts').then(r => r.data)
export const getCutPrices = (id) => api.get(`/cuts/${id}/prices`).then(r => r.data)
export const getVendors = (params = {}) => api.get('/vendors', { params }).then(r => r.data)
export const getWeather = () => api.get('/weather').then(r => r.data)

// ─── Admin auth ───────────────────────────────────────────────────────────────

export const adminLogin = (username, password) =>
  api.post('/admin/auth/login', { username, password }).then(r => r.data)

// ─── Admin dashboard ─────────────────────────────────────────────────────────

export const getDashboard = () => api.get('/admin/dashboard').then(r => r.data)

// ─── Admin deals ─────────────────────────────────────────────────────────────

export const adminGetDeals = (params = {}) => api.get('/admin/deals', { params }).then(r => r.data)
export const adminCreateDeal = (data) => api.post('/admin/deals', data).then(r => r.data)
export const adminUpdateDeal = (id, data) => api.put(`/admin/deals/${id}`, data).then(r => r.data)
export const adminDeleteDeal = (id) => api.delete(`/admin/deals/${id}`)
export const adminExpireDeal = (id) => adminUpdateDeal(id, { active: false })

// ─── Admin vendors ────────────────────────────────────────────────────────────

export const adminGetVendors = () => api.get('/admin/vendors').then(r => r.data)
export const adminCreateVendor = (data) => api.post('/admin/vendors', data).then(r => r.data)
export const adminUpdateVendor = (id, data) => api.put(`/admin/vendors/${id}`, data).then(r => r.data)
export const adminDeactivateVendor = (id) => adminUpdateVendor(id, { active: false })

// ─── Admin cuts ───────────────────────────────────────────────────────────────

export const adminGetCuts = () => api.get('/admin/cuts').then(r => r.data)
export const adminCreateCut = (data) => api.post('/admin/cuts', data).then(r => r.data)
export const adminUpdateCut = (id, data) => api.put(`/admin/cuts/${id}`, data).then(r => r.data)
export const adminDeactivateCut = (id) => adminUpdateCut(id, { active: false })

// ─── Admin staging ────────────────────────────────────────────────────────────

export const getStagingStatus = () => api.get('/admin/staging/status').then(r => r.data)
export const getStagedDeals = (status = 'pending', params = {}) =>
  api.get('/admin/staging', { params: { status, ...params } }).then(r => r.data)
export const runDiscovery = () => api.post('/admin/staging/run').then(r => r.data)
export const approveStaged = (id, data) => api.post(`/admin/staging/${id}/approve`, data).then(r => r.data)
export const dismissStaged = (id) => api.post(`/admin/staging/${id}/dismiss`)
export const bulkDismiss = (body) => api.post('/admin/staging/bulk-dismiss', body).then(r => r.data)
export const clearDismissed = () => api.delete('/admin/staging/dismissed').then(r => r.data)
export const autoApprove = () => api.post('/admin/staging/auto-approve').then(r => r.data)

// New-stores (vendor stub) flow
export const getNewStores = () => api.get('/admin/staging/new-stores').then(r => r.data)
export const activateVendorStub = (data) => api.post('/admin/staging/activate-vendor', data).then(r => r.data)
export const dismissVendorStub = (id) => api.delete(`/admin/staging/new-stores/${id}`).then(r => r.data)
