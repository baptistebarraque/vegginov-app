import { BrowserRouter, Route, Routes } from "react-router";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminRecipeDetailPage from "./pages/AdminRecipeDetailPage";
import AdminRecipeListPage from "./pages/AdminRecipeListPage";
import AdminUploadPage from "./pages/AdminUploadPage";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<AdminUploadPage />} />
        <Route path="/admin/recipes" element={<AdminRecipeListPage />} />
        <Route path="/admin/recipes/:id" element={<AdminRecipeDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
