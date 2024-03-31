import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import store from "..";
import { Msg } from "../../Interfaces/Msg";
import { textPush } from "../../http/API";

export const fetchPush = createAsyncThunk<string, string>(
  "chat/fetchPush",
  async function (federalLaw: string) {
    const response = await textPush("", federalLaw);
    return response;
  }
);
// type Gets = Msg && "";
const inputsStateSlice = createSlice({
  name: "inputsStateSlice",
  initialState: {
    msgs: [] as Msg[],
  },
  reducers: {
    setMsgs(state, actions: { payload: { Msg: Msg; federalLaw: string } }) {
      const msg = actions.payload.Msg;
      state.msgs.push(msg);
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchPush.fulfilled, (state, action) => {
      console.log("dsadasd", state, action.payload);
      const date = new Date(Date.now());
      const time = date.getHours() + ":" + date.getMinutes();

      // state.msgs[len - 1].status = "read";

      state.msgs.forEach((msg) => {
        msg.status = "read";
      });

      state.msgs.push({
        who: "bot",
        msg: action.payload,
        time,
        status: "read",
      });
    });
  },
});

export type RootState = ReturnType<typeof store.getState>;
export const { setMsgs } = inputsStateSlice.actions;
export default inputsStateSlice.reducer;
