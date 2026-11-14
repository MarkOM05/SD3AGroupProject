import { useState, useEffect } from "react";
import { auth, db } from "../firebase";
import { collection, getDocs, query, where, doc, getDoc } from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";
const API_BASE_URL = "https://sd3agroupproject.onrender.com";

function Applications() {
	const [selectedApplication, setSelectedApplication] = useState(null);
	const [applications, setApplications] = useState([]);
	const [loading, setLoading] = useState(true);
	const [searchTerm, setSearchTerm] = useState("");
	const [userRole, setUserRole] = useState("");
	const [aprPercent, setAprPercent] = useState("");
	const [creditMemo, setCreditMemo] = useState("");
	const [approving, setApproving] = useState(false);
	const [approvalMessage, setApprovalMessage] = useState("");
	
	async function handleApprove() {
		if (!selectedApplication) {
			return;
		}

		const user = auth.currentUser;

		if (!user) {
			setApprovalMessage("Please sign in again.");
			return;
		}

		if (aprPercent === "" || isNaN(Number(aprPercent)) || Number(aprPercent) < 0 || Number(aprPercent) > 100) {
			setApprovalMessage("Please enter an APR between 0 and 100.");
			return;
		}

		if (creditMemo.trim() === "") {
			setApprovalMessage("Please enter a reason for approval.");
			return;
		}

		setApproving(true);
		setApprovalMessage("");

		try {
			const token = await user.getIdToken();

			const response = await fetch(
				API_BASE_URL + "/applications/" + selectedApplication.id + "/approve",
				{
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						"Authorization": "Bearer " + token
					},
					body: JSON.stringify({
						aprPercent: Number(aprPercent),
						creditMemo: creditMemo.trim()
					})
				}
			);

			const result = await response.json();

			if (!response.ok) {
				throw new Error(result.detail || "Approval failed.");
			}

			setApprovalMessage("Application approved successfully!");
			setSelectedApplication({
				...selectedApplication,
				status: result.status
			});

			setApplications((currentApplications) =>
				currentApplications.map((application) => {
					if (application.id === selectedApplication.id) {
						return { ...application, status: result.status };
					}

					return application;
				})
			);

		} catch (error) {
			console.error("Approval error:", error);
			setApprovalMessage(error.message);
		} finally {
			setApproving(false);
		}
	}

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
				setUserRole(role);
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
				const applicationList = await Promise.all(
					snapshot.docs.map(async (document) => {
						const application = document.data();

						const userDocument = await getDoc(
							doc(db, "users", application.borrowerId)
						);

						let applicantName = "Unknown Applicant";

						if (userDocument.exists()) {
							applicantName = userDocument.data().name;
						}

						return {
							...application,
							id: document.id,
							applicantName: applicantName
						};
					})
				);

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
	let buttonText = "Approve Application";

	if (approving === true) { buttonText = "Approving...";}
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


		  {/* Applications table*/}
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
						<td>{application.applicantName}</td> {/* All Applicants share the same name as all Borrower IDs are the same*/}
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

					<p><strong>Applicant:</strong> {selectedApplication.applicantName}</p>
					<p><strong>Loan amount:</strong> {selectedApplication.property && selectedApplication.property.askingPrice}</p>
					<p><strong>County:</strong> {selectedApplication.property && selectedApplication.property.county}</p>
					<p><strong>Status:</strong> {selectedApplication.status}</p>
					<p>POP UP IS WORKING!</p>
					{userRole === "underwriter" && (
						<section className="approval-form">
							<h3>Underwriter Sign-Off</h3>

							<label htmlFor="apr-percent">APR (%)</label>
							<input
								id="apr-percent"
								type="number"
								min="0"
								max="100"
								step="0.01"
								value={aprPercent}
								onChange={(event) => setAprPercent(event.target.value)}
							/>

							<label htmlFor="credit-memo">Credit Memo</label>
							<textarea
								id="credit-memo"
								value={creditMemo}
								onChange={(event) => setCreditMemo(event.target.value)}
								placeholder="Enter your reason for approving this application..."
							/>
							
							<button type="button" onClick={handleApprove} disabled={approving} >
								{buttonText}
							</button>
							<p>{approvalMessage}</p>
						</section>
					)}
					<button type="button" onClick={() => setSelectedApplication(null)}>Close</button>
				</article>
			</section>
		)}

		</main>
	);
}

export default Applications;