import { $host } from ".";

export const textPush = async (
  text: string,
  federalLaw: string
): Promise<string> => {
  const response = await $host.post("/bot", { text, federalLaw });
  return response.data;
};
