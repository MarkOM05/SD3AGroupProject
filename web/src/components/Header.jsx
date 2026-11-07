import { NavLink, Link } from "react-router-dom";

function Header() {
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
          <li><NavLink to="/auth" id="SignInBtn">Sign In</NavLink></li>
          <li><NavLink to="/auth" id="SignUpBtn">Sign Up</NavLink></li>
          <li><button id="SignOutBtn" hidden>Sign Out</button></li>
        </ul>
      </nav>

    </header>
  );
}

export default Header;