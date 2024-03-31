import { $host } from ".";

interface Msg {
  msg: string;
}

export const textPush = async (
  text: string,
  federalLaw: string
): Promise<Msg> => {
  const response = await $host.post("/bot", { text, federalLaw });
  return response.data;
};
