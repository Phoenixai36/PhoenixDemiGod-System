import { configureStore } from '@reduxjs/toolkit'
import appConfigReducer from './appConfigSlice'

export const store = configureStore({
  reducer: {
    appConfig: appConfigReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch