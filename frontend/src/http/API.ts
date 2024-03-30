import { $host } from ".";

export const textPush = async (text: string): Promise<string> => {
  const response = await $host.post("path/to/", { text });
  return response.data;
};
