import { auth, db } from "../firebase";
import { useState, useEffect } from "react";
import { collection, getDocs, query, where, doc, getDoc } from "firebase/firestore";

function Dashboard() {
	const [userName, setUserName] = useState("");
	const [userRole, setUserRole] = useState("");
	const [applications, setApplications] = useState([]);
	const [loadingApplications, setLoadingApplications] = useState(true);

	useEffect(() => {
	  const unsubscribe = auth.onAuthStateChanged((user) => {
		if (user) {
			setUserName(user.displayName || user.email);
			console.log("Firebase user:", user.email);
			user.getIdTokenResult(true).then((result) => {
				console.log("Firebase claims:", result.claims);
				console.log("Role claim:", result.claims.role);
				console.log("Current user UID:", user.uid);
				console.log("Current project:", db.app.options.projectId);
				if (result.claims.role) {
				  setUserRole(result.claims.role);
				} else {
				  setUserRole("unknown");
				}
			  });
		} else {
		  setUserName("User");
		  setUserRole("");
		}
	  });

	  return unsubscribe;
	}, []);
	useEffect(() => {
	  async function loadApplications() {
		const currentUser = auth.currentUser;

		if (!currentUser || !userRole) {
		  return;
		}

		try {
			const userDocument = await getDoc(doc(db, "users", currentUser.uid));

			console.log("Can read own user document:", userDocument.exists());

			let applicationsQuery;

			if (userRole === "underwriter") {
				applicationsQuery = collection(db, "applications");
			} else if (userRole === "broker") {
				applicationsQuery = query(
				collection(db, "applications"),
				where("brokerId", "==", currentUser.uid)
				);
			} else {
				setApplications([]);
				setLoadingApplications(false);
				return;
			}

			const snapshot = await getDocs(applicationsQuery);

			const applicationList = snapshot.docs.map((document) => ({
				...document.data(),
				id: document.id
			}));

			setApplications(applicationList);
		} catch (error) {
		  console.error("Error loading applications:", error);
		} finally {
		  setLoadingApplications(false);
		}
	  }

	  loadApplications();
	}, [userRole]);
	
  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <h2>Welcome, {userName}!</h2>
        <p>Here is an overview of your lending pipeline.</p>
		<p>Your role: {userRole}</p> {/*Test*/}
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
		  {loadingApplications && (
			<p>Loading applications...</p>
		  )}

		  {!loadingApplications && applications.length === 0 && (
			<p>No applications found.</p>
		  )}

		  {!loadingApplications && applications.length > 0 && (
			<ul>
			  {applications.map((application) => (
				<li key={application.id}>
				  <h4>{application.loanType}</h4>

				  <p>Status: {application.status}</p>

				  <p>
					County: {application.property && application.property.county}
				  </p>

				  <p>
					Asking price: {application.property && application.property.askingPrice}
				  </p>
				</li>
			  ))}
			</ul>
		  )}
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