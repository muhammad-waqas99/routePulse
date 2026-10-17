import axios from "axios";

const configuredBaseUrl = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const apiClient = axios.create({
  baseURL: configuredBaseUrl.endsWith("/api/v1")
    ? configuredBaseUrl
    : `${configuredBaseUrl}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export default apiClient;
