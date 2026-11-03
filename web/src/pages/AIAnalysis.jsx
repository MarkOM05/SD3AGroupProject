function AIAnalysis() {
  return (
    <main className="ai-analysis-page">
		<head>
			<title>AL - AI Analysis</title>
		</head>
	
      <header className="page-header">
        <h2>AI Analysis</h2>
        <p>Review AI assessments and lending recommendations</p>
      </header>

      <section className="analysis-selection">
        <label htmlFor="application-select">Select Application</label>
        <select id="application-select">
          <option value="">Select Application</option>
          <option value="norm">Norm</option>
        </select>
      </section>

      <section className="borrower-analysis">
        <h3>Norm:</h3>

        <table>
          <thead>
            <tr>
              <th>LTV</th>
              <th>DTI</th>
              <th>AI Recommendation</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>74%</td>
              <td>31%</td>
              <td>Conditional Approval</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="agent-results">
        <article className="agent-card">
          <h3>Affordability Agent</h3>
          <p>Pass</p>
        </article>

        <article className="agent-card">
          <h3>Valuation Agent</h3>
          <p>Review</p>
        </article>

        <article className="agent-card">
          <h3>Market &amp; Macro Agent</h3>
          <p>Pass</p>
        </article>

        <article className="agent-card">
          <h3>Underwriting Strategist</h3>
          <p>Conditional Approval</p>
        </article>
      </section>

      <section className="analysis-complete">
			<h3>AI Analysis Complete</h3>
			<p>This application has been assessed by all four AI Agents. Final decision remains with the bank underwriter.</p>
      </section>
    </main>
  );
}

export default AIAnalysis;