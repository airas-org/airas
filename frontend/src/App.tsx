import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/app-layout";

export default function App() {
  return (
    <Routes>
      <Route path="*" element={<AppLayout />} />
    </Routes>
  );
}
