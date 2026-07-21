import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import LandingPage from "./pages/LandingPage";
import SearchResultsPage from "./pages/SearchResultsPage";
import ConversationalSearchPage from "./pages/ConversationalSearchPage";
import BusinessDetailsPage from "./pages/BusinessDetailsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/search" element={<SearchResultsPage />} />
        <Route path="/chat" element={<ConversationalSearchPage />} />
        <Route path="/business/:id" element={<BusinessDetailsPage />} />
      </Route>
    </Routes>
  );
}
