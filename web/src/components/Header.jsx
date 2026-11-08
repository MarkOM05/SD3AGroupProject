import { NavLink, Link, useNavigate } from "react-router-dom";
import { signOut } from "firebase/auth";
import { auth } from "../firebase";

function Header() {
  const navigate = useNavigate();

  async function handleSignOut() {
    try {
      await signOut(auth);
      navigate("/auth");
    } catch (error) {
      console.log("Error signing out:", error);
    }
  }

  return (
    <header className="main-header">

      <Link to="/dashboard" className="site-logo">
        Agentic Lender
      </Link>

      <nav className="main-navigation">
        <ul id="navigation">
          <li><NavLink to="/dashboard">Dashboard</NavLink></li>
          <li><NavLink to="/applications">Applications</NavLink></li>
          <li><NavLink to="/ai-analysis">AI Analysis</NavLink></li>
          <li><NavLink to="/blockchain">Blockchain</NavLink></li>
        </ul>
      </nav>

      <nav className="authentication-navigation">
        <ul id="authentication">
          <li>
            <button id="SignOutBtn" onClick={handleSignOut}>
              Sign Out
            </button>
          </li>
        </ul>
      </nav>

    </header>
  );
}

export default Header;