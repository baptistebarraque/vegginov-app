import { BrowserRouter, Route, Routes } from "react-router";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminUploadPage from "./pages/AdminUploadPage";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<AdminUploadPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
