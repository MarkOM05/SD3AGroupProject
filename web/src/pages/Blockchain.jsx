import { useState } from "react";

function Blockchain() {
  const [selectedLoan, setSelectedLoan] = useState(null);

  const loans = [
    {
      loan: "AL-0042",
      amount: "€320,000",
      status: "Minted",
      tokenId: "#AL-0042"
    },
    {
      loan: "AL-0041",
      amount: "€250,000",
      status: "Pending",
      tokenId: "#AL-0041"
    }
  ];

  return (
    <main className="blockchain-page">
      <header className="page-header">
        <h2>Blockchain</h2>
        <p>On-chain loan records and audit history</p>
      </header>

      <section className="blockchain-stats">
        <article className="stat-card">
          <h3>Tokenised Loans</h3>
          <p>12</p>
        </article>

        <article className="stat-card">
          <h3>Audit Records</h3>
          <p>12</p>
        </article>

        <article className="stat-card">
          <h3>Network</h3>
          <p>Local Anvil</p>
        </article>
      </section>

      <section className="blockchain-records">
        <h3>Recent blockchain records</h3>

        <table>
          <thead>
            <tr>
              <th>Loan</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Token ID</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {loans.map((loan) => (
              <tr key={loan.loan}>
                <td>{loan.loan}</td>
                <td>{loan.amount}</td>
                <td>{loan.status}</td>
                <td>{loan.tokenId}</td>
                <td>
                  <button
                    type="button"
                    onClick={() => setSelectedLoan(loan)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {selectedLoan && (
        <section className="loan-popup">
          <article className="loan-popup-content">
            <h2>Selected Loan: {selectedLoan.loan}</h2>

            <button type="button" onClick={() => setSelectedLoan(null)}>Close </button>
          </article>
        </section>
      )}
    </main>
  );
}

export default Blockchain;