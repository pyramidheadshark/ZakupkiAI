import axios from "axios";

const $host = axios.create({
  baseURL: "http://localhost/",
});

export { $host };
