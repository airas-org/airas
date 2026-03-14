import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css"; // ここで globals.css の中身を読み込む
import "./i18n";
import App from "./App";
import { OpenAPI } from "./lib/api";

OpenAPI.BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

// Attach GitHub session header only to GitHub-related generated API calls
OpenAPI.HEADERS = async (options) => {
  const sessionToken = localStorage.getItem("github_session_token");
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (
    sessionToken &&
    typeof options?.url === "string" &&
    options.url.toLowerCase().includes("github") &&
    headers["x-github-session"] === undefined
  ) {
    headers["x-github-session"] = sessionToken;
  }
  return headers;
};

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
