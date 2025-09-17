import React from 'react';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Dashboard</h2>
        </div>
        <div className="card-body">
          <p>Bienvenido al sistema de tickets, {user?.first_name || user?.email}!</p>
          <p>El backend está funcionando correctamente en: <strong>http://localhost:8000</strong></p>
          <div style={{ marginTop: '20px' }}>
            <h3>Próximos pasos:</h3>
            <ul>
              <li>Gestión de tickets</li>
              <li>Administración de usuarios</li>
              <li>Reportes y estadísticas</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;