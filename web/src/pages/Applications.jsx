import { useState, useEffect } from "react";
import { auth, db } from "../firebase";
import { collection, getDocs, query, where } from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";

function Applications() {
	const [selectedApplication, setSelectedApplication] = useState(null);
	const [applications, setApplications] = useState([]);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState("");
	useEffect(() => {
		const unsubscribe = onAuthStateChanged(auth, async (user) => {
			if (!user) {
				setApplications([]);
				setLoading(false);
				return;
			}

			try {
				const tokenResult = await user.getIdTokenResult(true);
				const role = tokenResult.claims.role;
				let applicationsQuery;

				if (role === "underwriter") {
					applicationsQuery = collection(db, "applications");
				} else if (role === "broker") {
					applicationsQuery = query(
						collection(db, "applications"),
						where("brokerId", "==", user.uid)
					);
				} else {
					setApplications([]);
					setLoading(false);
					return;
				}

				const snapshot = await getDocs(applicationsQuery);

				const applicationList = snapshot.docs.map((document) => ({
					...document.data(),
					id: document.id
				}));

				setApplications(applicationList);
				console.log("Applications loaded:", applicationList);

			} catch (error) {
				console.error("Error loading applications:", error);
			} finally {
				setLoading(false);
			}
		});
		return unsubscribe;
	}, []);
	return (
		<main className="applications-page">
		  <header className="page-header">
			<h2>Applications</h2>
			<p>Manage and review your mortgage applications</p>
		  </header>

		  {/* Application summary cards */}

		  <section className="application-stats">

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
			  <h3>Approved</h3>
			  <p>4</p>
			</article>

		  </section>

		  {/* Search and action buttons */}

		  <section className="application-controls">

			<form className="search-form">
			  <label htmlFor="applicant-search">
				Search by name:
			  </label>

			  <input type="text" id="applicant-search" placeholder="Enter..."/>
			  <button type="submit">Search</button>
			  <button type="button">Show All</button>
			  <button type="button">Create</button>
			</form>

		  </section>

		  {/* Applications table */}

		  <section className="applications-table">

			<table>
			  <thead>
				<tr>
				  <th>Applicant</th>
				  <th>Loan</th>
				  <th>City</th>
				  <th>LTV</th>
				  <th>Risk</th>
				  <th>Status</th>
				  <th>Actions</th>
				</tr>
			  </thead>

			  <tbody>
				{loading && (
					<tr>
						<td colSpan="7">Loading applications...</td>
					</tr>
				)}

				{!loading && applications.length === 0 && (
					<tr>
						<td colSpan="7">No applications found.</td>
					</tr>
				)}

				{!loading && applications.map((application) => (
					<tr key={application.id}>
						<td>{application.borrowerId}</td>
						<td>{application.property && application.property.askingPrice}</td>
						<td>{application.property && application.property.county}</td>
						<td>{application.ltv || "N/A"}</td>
						<td>{application.riskTier || "N/A"}</td>
						<td>{application.status}</td>
						<td>
							<button type="button" onClick={() => setSelectedApplication(application)}>View</button>
						</td>
					</tr>
				))}
				</tbody>
			</table>
		  </section>
		  
		{selectedApplication && (
			<section className="application-popup">
				<article className="popup-content">
					<h2>Application Details</h2>

					<p><strong>Applicant:</strong> {selectedApplication}</p>
					<p>POP UP IS WORKING!</p>
					<button type="button" onClick={() => setSelectedApplication(null)}>Close</button>
				</article>
			</section>
		)}

		</main>
	);
}

export default Applications;