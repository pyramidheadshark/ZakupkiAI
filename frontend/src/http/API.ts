import { $host } from ".";

export const textPush = async (text: string): Promise<string> => {
  const response = await $host.post("/bot", { text });
  return response.data;
};
