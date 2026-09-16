import { createContext, createElement, useContext, useReducer, useEffect } from 'react';
import { loginUser } from '../api/auth';

const AuthContext = createContext(null);

function loadInitialState() {
  const token = localStorage.getItem('auth_token');
  const userRaw = localStorage.getItem('auth_user');
  return { token: token || null, user: userRaw ? JSON.parse(userRaw) : null };
}

function authReducer(state, action) {
  switch (action.type) {
    case 'LOGIN':
      return {
        token: action.payload.access_token,
        user: action.payload.user ?? null,
      };
    case 'LOGOUT':
      return { token: null, user: null };
    default:
      return state;
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, undefined, loadInitialState);

  useEffect(() => {
    if (state.token) {
      localStorage.setItem('auth_token', state.token);
      localStorage.setItem('auth_user', JSON.stringify(state.user));
    } else {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
    }
  }, [state.token, state.user]);

  return createElement(AuthContext.Provider, { value: { state, dispatch } }, children);
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  const { state, dispatch } = ctx;

  async function login(credentials) {
    const data = await loginUser(credentials);
    dispatch({ type: 'LOGIN', payload: data });
  }

  function logout() {
    dispatch({ type: 'LOGOUT' });
  }

  return { token: state.token, user: state.user, isAuthenticated: !!state.token, login, logout };
}