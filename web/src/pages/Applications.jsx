import { useState, useEffect } from "react";
import { auth, db } from "../firebase";
import { collection, getDocs, query, where, doc, getDoc } from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";
const API_BASE_URL = "https://sd3agroupproject.onrender.com";

function formatEuro(value) {
	return new Intl.NumberFormat("en-IE", {
		style: "currency",
		currency: "EUR",
		maximumFractionDigits: 0
	}).format(value);
}

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
	// Values used in the application details popup
	let selectedProperty = {};
	let askingPrice = 0;
	let deposit = 0;
	let estimatedLoanAmount = 0;
	let estimatedLtv = "Pending";
	let annualGrossIncome = 0;
	let monthlyGrossIncome = 0;
	let outstandingDebts = 0;

	if (selectedApplication) {
		if (selectedApplication.property) {
			selectedProperty = selectedApplication.property;
		}

		askingPrice = Number(selectedProperty.askingPrice) || 0;
		deposit = Number(selectedApplication.deposit) || 0;

		estimatedLoanAmount = askingPrice - deposit;

		if (estimatedLoanAmount < 0) {
			estimatedLoanAmount = 0;
		}

		if (askingPrice > 0) {
			estimatedLtv = ((estimatedLoanAmount / askingPrice) * 100).toFixed(2) + "%";
		}

		annualGrossIncome = Number(selectedApplication.income) || 0;
		monthlyGrossIncome = annualGrossIncome / 12;

		outstandingDebts = Number(selectedApplication.debts) || 0;
	}
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
				  <th>County</th>
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

				{/* Popup Header */}
				<header className="popup-header">
					<div>
						<p className="popup-eyebrow">LOAN FILE</p>
						<h2>{selectedApplication.applicantName}</h2>
						<p className="popup-reference">
							Reference: {selectedApplication.id}
						</p>
					</div>

					<span className="popup-status">
						{selectedApplication.status}
					</span>
				</header>

				{/* Borrower and Property / Collateral */}
				<section className="popup-grid">

					<article className="popup-card">
						<h3>Borrower & Property</h3>

						<div className="popup-field">
							<span>Applicant Name</span>
							<strong>{selectedApplication.applicantName}</strong>
						</div>

						<div className="popup-field">
							<span>County</span>
							<strong>{selectedProperty.county || "Not provided"}</strong>
						</div>

						<div className="popup-field">
							<span>Property Type</span>
							<strong>{selectedProperty.type || "Not provided"}</strong>
						</div>

						<div className="popup-field">
							<span>Floor Area</span>
							<strong>
								{selectedProperty.sizeSqm ? selectedProperty.sizeSqm + " m²" : "Not provided"}
							</strong>
						</div>

						<div className="popup-field">
							<span>Bedrooms</span>
							<strong>{selectedProperty.bedrooms || "Not provided"}</strong>
						</div>

						<div className="popup-field">
							<span>BER Rating</span>
							<strong>{selectedProperty.berRating || "Not provided"}</strong>
						</div>

						<div className="popup-field">
							<span>Estimated Loan Amount</span>
							<strong>{formatEuro(estimatedLoanAmount)}</strong>
						</div>

						<div className="popup-field">
							<span>Loan Term</span>
							<strong>
								{selectedApplication.termYears
									? selectedApplication.termYears + " years"
									: "Not provided"}
							</strong>
						</div>
					</article>

					<article className="popup-card">
						<h3>Collateral Assessment</h3>

						<div className="popup-field">
							<span>Asking Price</span>
							<strong>{formatEuro(askingPrice)}</strong>
						</div>

						<div className="popup-field">
							<span>Deposit</span>
							<strong>{formatEuro(deposit)}</strong>
						</div>

						<div className="popup-field">
							<span>ML Valuation</span>
							<strong className="pending-value">Pending</strong>
						</div>

						<div className="popup-field">
							<span>Valuation Difference</span>
							<strong className="pending-value">Pending</strong>
						</div>

						<div className="popup-field">
							<span>Estimated LTV</span>
							<strong>{estimatedLtv}</strong>
						</div>

						<div className="popup-field">
							<span>Valuation Status</span>
							<strong className="pending-value">Pending</strong>
						</div>
					</article>

				</section>

				{/* DTI Breakdown */}
				<section className="popup-card dti-card">
					<h3>DTI Breakdown</h3>

					<div className="dti-grid">

						<div className="popup-field">
							<span>Annual Gross Income</span>
							<strong>{formatEuro(annualGrossIncome)}</strong>
						</div>

						<div className="popup-field">
							<span>Monthly Gross Income</span>
							<strong>{formatEuro(monthlyGrossIncome)}</strong>
						</div>

						<div className="popup-field">
							<span>Total Outstanding Debts</span>
							<strong>{formatEuro(outstandingDebts)}</strong>
						</div>

						<div className="popup-field">
							<span>Mortgage Repayment</span>
							<strong className="pending-value">Pending</strong>
						</div>

						<div className="popup-field">
							<span>Total Monthly Repayments</span>
							<strong className="pending-value">Pending</strong>
						</div>

						<div className="popup-field">
							<span>Debt-to-Income Ratio</span>
							<strong className="pending-value">Pending</strong>
						</div>

					</div>
				</section>

				{/* Underwriter Approval */}
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

						<button
							type="button"
							onClick={handleApprove}
							disabled={approving}
						>
							{buttonText}
						</button>

						<p>{approvalMessage}</p>
					</section>
				)}

				{/* Popup Actions */}
				<footer className="popup-footer">
					<button type="button" disabled>
						AI Analysis
					</button>

					<button
						type="button"
						onClick={() => setSelectedApplication(null)}
					>
						Back to Pipeline
					</button>
				</footer>

			</article>
		</section>
	)}

		</main>
	);
}

export default Applications;