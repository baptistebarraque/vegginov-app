import { AnimatePresence, motion } from "framer-motion";
import { BrowserRouter, Route, Routes, useLocation } from "react-router";
import AccountPage from "./pages/AccountPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminRecipeDetailPage from "./pages/AdminRecipeDetailPage";
import AdminRecipeListPage from "./pages/AdminRecipeListPage";
import AdminUploadPage from "./pages/AdminUploadPage";
import ConfirmPasswordResetPage from "./pages/ConfirmPasswordResetPage";
import HomePage from "./pages/HomePage";
import LikedRecipesPage from "./pages/LikedRecipesPage";
import LoginPage from "./pages/LoginPage";
import OnboardingPage from "./pages/OnboardingPage";
import ProfilePreferencesPage from "./pages/ProfilePreferencesPage";
import RequestPasswordResetPage from "./pages/RequestPasswordResetPage";
import SignupPage from "./pages/SignupPage";
import WatchlistPage from "./pages/WatchlistPage";
import { DURATION } from "./utils/motion";

// Route transition (docs/FRONTEND.md §6.5): a plain opacity/y fade on the whole
// outlet, keyed by pathname. No slide-across. Under reduced motion the y is
// dropped by the app-wide MotionConfig, leaving an opacity-only fade.
function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: DURATION.base }}
      >
        <Routes location={location}>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/preferences" element={<ProfilePreferencesPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/likes" element={<LikedRecipesPage />} />
          <Route path="/reset-password" element={<RequestPasswordResetPage />} />
          <Route path="/reset-password/confirm" element={<ConfirmPasswordResetPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin" element={<AdminUploadPage />} />
          <Route path="/admin/recipes" element={<AdminRecipeListPage />} />
          <Route path="/admin/recipes/:id" element={<AdminRecipeDetailPage />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  );
}

export default App;
