import { auth } from "../firebase";
import { useState, useEffect } from "react";

function Dashboard() {
	const [userName, setUserName] = useState("");

	useEffect(() => {
	  const unsubscribe = auth.onAuthStateChanged((user) => {
		if (user) {
		  setUserName(user.displayName || user.email);
		} else {
		  setUserName("User");
		}
	  });

	  return unsubscribe;
	}, []);
  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <h2>Welcome, {userName}!</h2>
        <p>Here is an overview of your lending pipeline.</p>
      </header>

      <section className="stats-container">

        <article className="stat-card">
          <h3>Processing</h3>
          <p>24</p>
        </article>

        <article className="stat-card">
          <h3>Pending</h3>
          <p>7</p>
        </article>

        <article className="stat-card">
          <h3>AI Approved</h3>
          <p>12</p>
        </article>

        <article className="stat-card">
          <h3>Loan Value</h3>
          <p>4.2m</p>
        </article>

      </section>

      <section className="dashboard-grid">

        <article className="dashboard-panel">
          <h3>Loan Applications</h3>
          <p>Preview of Applications</p>
        </article>

        <article className="dashboard-panel">
          <h3>AI Committee</h3>
          <p>Preview of AI Analysis</p>
        </article>

        <article className="dashboard-panel">
          <h3>Property Valuation</h3>
          <p>Preview of Property Valuation</p>
        </article>

        <article className="dashboard-panel">
          <h3>Blockchain</h3>
          <p>Preview of Blockchain</p>
        </article>

      </section>

    </main>
  );
}

export default Dashboard;