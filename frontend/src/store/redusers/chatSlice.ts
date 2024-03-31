import { createSlice } from "@reduxjs/toolkit";
import store from "..";
import { Msg } from "../../Interfaces/Msg";

const inputsStateSlice = createSlice({
  name: "inputsStateSlice",
  initialState: {
    msgs: [] as Msg[],
  },
  reducers: {
    setMsgs(state, actions: { payload: Msg }) {
      state.msgs.push(actions.payload as Msg);
    },
  },
});

export type RootState = ReturnType<typeof store.getState>;
export const { setMsgs } = inputsStateSlice.actions;
export default inputsStateSlice.reducer;
