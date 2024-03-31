import { combineReducers } from "redux";
import chatSlice from "./chatSlice";

const rootReducer = combineReducers({
  chat: chatSlice,
});

export default rootReducer;
