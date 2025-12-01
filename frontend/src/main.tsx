// frontend/src/main.tsx
import React from "react"
import ReactDOM from "react-dom/client"
import "./index.css"      // ここで globals.css の中身を読み込む
import App from "./App"

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
