import { useState } from "react";

function Applications() {
	const [selectedApplication, setSelectedApplication] = useState(null);
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
				<tr>
				  <td>Norm</td>
				  <td>320K</td>
				  <td>Dublin</td>
				  <td>74%</td>
				  <td>Low</td>
				  <td>Review</td>
				  <td><button type="button" onClick={() => setSelectedApplication("Norm")}>View</button></td>
				</tr>

				<tr>
				  <td>Grace</td>
				  <td>400K</td>
				  <td>Cork</td>
				  <td>83%</td>
				  <td>High</td>
				  <td>Approved</td>
				  <td><button type="button" onClick={() => setSelectedApplication("Grace")}>View</button></td>
				</tr>

				<tr>
				  <td>Peter</td>
				  <td>250K</td>
				  <td>Galway</td>
				  <td>68%</td>
				  <td>Medium</td>
				  <td>Review</td>
				  <td><button type="button" onClick={() => setSelectedApplication("Peter")}>View</button></td>
				</tr>

				<tr>
				  <td>Clare</td>
				  <td>380K</td>
				  <td>Dublin</td>
				  <td>79%</td>
				  <td>Medium</td>
				  <td>Review</td>
				  <td><button type="button" onClick={() => setSelectedApplication("Clare")}>View</button></td>
				</tr>
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