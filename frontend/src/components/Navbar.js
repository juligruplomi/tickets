import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/dashboard" className="navbar-brand">
          Tickets GrupLomi
        </Link>
        
        <ul className="navbar-nav">
          <li>
            <Link 
              to="/dashboard" 
              className={isActive('/dashboard') ? 'active' : ''}
            >
              Dashboard
            </Link>
          </li>
          <li>
            <Link 
              to="/tickets" 
              className={isActive('/tickets') ? 'active' : ''}
            >
              Tickets
            </Link>
          </li>
          <li>
            <Link 
              to="/users" 
              className={isActive('/users') ? 'active' : ''}
            >
              Usuarios
            </Link>
          </li>
        </ul>
        
        <div className="navbar-user">
          <span>Hola, {user?.first_name || user?.email}</span>
          <button className="button button-secondary" onClick={logout}>
            Cerrar Sesión
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;