import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import AdminLayout from './components/AdminLayout'

import HomePage from './pages/HomePage'
import CutsPage from './pages/CutsPage'
import CutDetailPage from './pages/CutDetailPage'
import StoresPage from './pages/StoresPage'

import LoginPage from './pages/admin/LoginPage'
import DashboardPage from './pages/admin/DashboardPage'
import StagingPage from './pages/admin/StagingPage'
import DealsPage from './pages/admin/DealsPage'
import VendorsPage from './pages/admin/VendorsPage'
import CutsAdminPage from './pages/admin/CutsAdminPage'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/admin/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/cuts" element={<CutsPage />} />
            <Route path="/cuts/:id" element={<CutDetailPage />} />
            <Route path="/stores" element={<StoresPage />} />
          </Route>

          <Route path="/admin/login" element={<LoginPage />} />

          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="staging" element={<StagingPage />} />
            <Route path="deals" element={<DealsPage />} />
            <Route path="vendors" element={<VendorsPage />} />
            <Route path="cuts" element={<CutsAdminPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
