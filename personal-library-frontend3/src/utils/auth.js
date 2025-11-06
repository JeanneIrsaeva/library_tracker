const API_BASE_URL = 'http://localhost:8000';

export const saveTokens = (accessToken, refreshToken) => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

export const getTokens = () => {
  return {
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token')
  };
};

export const removeTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const refreshAccessToken = async () => {
  const { refreshToken } = getTokens();
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      }),
    });

    if (response.ok) {
      const data = await response.json();
      saveTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } else {
      removeTokens();
      throw new Error('Failed to refresh token');
    }
  } catch (error) {
    removeTokens();
    throw error;
  }
};

export const isTokenExpired = (token) => {
  if (!token) return true;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; 
    return Date.now() >= exp;
  } catch (error) {
    return true;
  }
};

export const authFetch = async (url, options = {}) => {
  let { accessToken } = getTokens();
  
  if (isTokenExpired(accessToken)) {
    try {
      accessToken = await refreshAccessToken();
    } catch (error) {
      removeTokens();
      window.location.href = '/login';
      throw error;
    }
  }

  const headers = {
    'Authorization': `Bearer ${accessToken}`,
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
  };

  let response = await fetch(url, config);

  if (response.status === 401) {
    try {
      accessToken = await refreshAccessToken();
      headers['Authorization'] = `Bearer ${accessToken}`;
      response = await fetch(url, config);
    } catch (error) {
      removeTokens();
      window.location.href = '/login';
      throw error;
    }
  }

  return response;
};