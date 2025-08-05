import axios from 'axios';

// Supongamos que la URL base de la API se obtiene de una variable de entorno
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api';

const apiService = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir el token de autenticación a cada solicitud
apiService.interceptors.request.use(
  (config) => {
    // En una aplicación real, obtendrías el token de una cookie, localStorage, o del estado de Redux
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta de forma centralizada
apiService.interceptors.response.use(
  (response) => response,
  (error) => {
    // Aquí se pueden manejar errores globales como 401 No Autorizado, 403 Prohibido, etc.
    if (error.response?.status === 401) {
      // Por ejemplo, redirigir a la página de login
      console.error('No autorizado. Redirigiendo al login...');
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiService;