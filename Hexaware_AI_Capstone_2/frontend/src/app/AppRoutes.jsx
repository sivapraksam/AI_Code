import { Navigate, Route, Routes } from 'react-router-dom';
import SignupPage from '../features/signup/SignupPage.jsx';
import SignupSuccessPage from '../pages/SignupSuccessPage.jsx';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/signup/success" element={<SignupSuccessPage />} />
      <Route path="*" element={<Navigate to="/signup" replace />} />
    </Routes>
  );
}
