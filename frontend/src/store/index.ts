import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./redusers"; // Import your combined reducers

const store = configureStore({
  reducer: rootReducer,
});

export type AppDispatch = typeof store.dispatch;
export default store;
