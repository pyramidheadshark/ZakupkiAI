import { $host } from ".";

export const textPush = async (
  text: string,
  federalLaw: string
): Promise<string> => {
  console.log(text);
  const response = await $host.post("/bot", { text, federalLaw });
  return response.data.msg;
};
