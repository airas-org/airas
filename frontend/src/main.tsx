// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css"; // ここで globals.css の中身を読み込む
import App from "./App";
import { OpenAPI } from "./lib/api";

OpenAPI.BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
