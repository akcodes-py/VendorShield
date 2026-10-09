import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { AuthProvider } from './context/AuthContext.jsx'

// WHY: AuthProvider at root so every page sees role without prop-drilling.
ReactDOM.createRoot(document.getElementById('root')).render(
  <AuthProvider><App /></AuthProvider>
)
