import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Applications from "./pages/Applications";
import AIAnalysis from "./pages/AIAnalysis";
import Blockchain from "./pages/Blockchain";
import Auth from "./pages/Auth";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
		<div>
			{/*<h1>Welcome to my React Website!</h1>*/}
			<Routes>
				<Route path="/auth" element={<Auth />} />
				<Route path="/" element={<Layout />}>
				  <Route index element={<Navigate to="/dashboard" replace />} />
				  <Route path="dashboard" element={<Dashboard />} />
				  <Route path="applications" element={<Applications />} />
				  <Route path="ai-analysis" element={<AIAnalysis />} />
				  <Route path="blockchain" element={<Blockchain />} />
				</Route>
			</Routes>
	  </div>
    </BrowserRouter>
  );
}

export default App;