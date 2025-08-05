import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import apiService from '../services/apiService';
import { AppConfig, NavigationItem } from '../types/api.types';

interface AppConfigState {
  navigation: NavigationItem[];
  userPermissions: string[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: AppConfigState = {
  navigation: [],
  userPermissions: [],
  status: 'idle',
  error: null,
};

/**
 * Thunk asíncrono para obtener la configuración de la aplicación desde la API.
 */
export const fetchAppConfig = createAsyncThunk('app/fetchConfig', async () => {
  const response = await apiService.get<AppConfig>('/config');
  return response.data;
});

const appConfigSlice = createSlice({
  name: 'appConfig',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAppConfig.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchAppConfig.fulfilled, (state, action: PayloadAction<AppConfig>) => {
        state.status = 'succeeded';
        state.navigation = action.payload.navigation;
        state.userPermissions = action.payload.userPermissions;
      })
      .addCase(fetchAppConfig.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'No se pudo obtener la configuración de la aplicación.';
      });
  },
});

export default appConfigSlice.reducer;