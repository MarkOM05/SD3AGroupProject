import { useState, useEffect } from "react";
import { auth, db } from "../firebase";
import {collection, getDocs, query, where, doc, getDoc} from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";

const API_BASE_URL = "https://sd3agroupproject.onrender.com";

// Send a request to the backend API
async function requestAssessment(endpoint, token, requestData) {
    const response = await fetch(API_BASE_URL + endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify(requestData)
    });

    const responseText = await response.text();

    if (!response.ok) {
        throw new Error(responseText || "API request failed: " + response.status);
    }

    if (!responseText.trim()) {
        throw new Error("The API returned an empty response.");
    }

    let result;

    try {
        result = JSON.parse(responseText);
    } catch (error) {
        result = responseText;
    }

    if (result === null || result === undefined || result === "string") {
        throw new Error("No usable assessment result was returned.");
    }

    if (typeof result === "object") {
        return JSON.stringify(result, null, 2);
    }

    return String(result);
}

function AIAnalysis() {
    const [applications, setApplications] = useState([]);
    const [selectedApplicationId, setSelectedApplicationId] = useState("");
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");

    // Affordability assessment state
    const [affordabilityStatus, setAffordabilityStatus] = useState("Pending");
    const [affordabilityResult, setAffordabilityResult] = useState("");
    const [affordabilityMessage, setAffordabilityMessage] = useState("");

    // Valuation assessment state
    const [valuationStatus, setValuationStatus] = useState("Pending");
    const [valuationResult, setValuationResult] = useState("");
    const [valuationMessage, setValuationMessage] = useState("");

    // Load applications from Firestore
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (user) => {
            if (!user) {
                setApplications([]);
                setSelectedApplicationId("");
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

                const applicationList = await Promise.all(
                    snapshot.docs.map(async (document) => {
                        const application = document.data();

                        let applicantName = "Unknown Applicant";

                        if (application.borrowerId) {
                            const userDocument = await getDoc(
                                doc(db, "users", application.borrowerId)
                            );

                            if (userDocument.exists()) {
                                applicantName = userDocument.data().name;
                            }
                        }

                        return {
                            ...application,
                            id: document.id,
                            applicantName: applicantName
                        };
                    })
                );

                setApplications(applicationList);

                if (applicationList.length > 0) {
                    setSelectedApplicationId(applicationList[0].id);
                }

            } catch (error) {
                console.error("Error loading AI Analysis applications:", error);
                setErrorMessage("Unable to load applications.");
            } finally {
                setLoading(false);
            }
        });

        return unsubscribe;
    }, []);

    // Find the currently selected application
    let selectedApplication = null;

    applications.forEach((application) => {
        if (application.id === selectedApplicationId) {
            selectedApplication = application;
        }
    });

    // Run assessments whenever the selected applicant changes
    useEffect(() => {
        let ignore = false;

        async function runAssessments() {
            if (!selectedApplication) {
                return;
            }

            setAffordabilityStatus("Running");
            setAffordabilityResult("");
            setAffordabilityMessage("");

            setValuationStatus("Running");
            setValuationResult("");
            setValuationMessage("");

            try {
                const user = auth.currentUser;

                if (!user) {
                    throw new Error("You must be logged in.");
                }

                const token = await user.getIdToken();

                // Run Affordability Agent
                try {
                    const affordabilityData = {
                        income: Number(selectedApplication.income),
                        debts: Number(selectedApplication.debts),
                        deposit: Number(selectedApplication.deposit),
                        propertyValue: Number(
                            selectedApplication.property.askingPrice
                        ),
                        termYears: Number(selectedApplication.termYears)
                    };

                    if (
                        !Number.isFinite(affordabilityData.income) ||
                        !Number.isFinite(affordabilityData.debts) ||
                        !Number.isFinite(affordabilityData.deposit) ||
                        !Number.isFinite(affordabilityData.propertyValue) ||
                        !Number.isFinite(affordabilityData.termYears)
                    ) {
                        throw new Error("Some financial information is missing.");
                    }

                    const result = await requestAssessment(
                        "/affordability",
                        token,
                        affordabilityData
                    );

                    if (!ignore) {
                        setAffordabilityResult(result);
                        setAffordabilityStatus("Complete");
                    }

                } catch (error) {
                    console.error("Affordability API error:", error);

                    if (!ignore) {
                        setAffordabilityStatus("Pending");
                        setAffordabilityMessage(error.message);
                    }
                }

                // Run Valuation Agent
                try {
                    const property = selectedApplication.property;

                    if (!property) {
                        throw new Error("Property information is missing.");
                    }

                    const valuationData = {
                        county: property.county,
                        sizeSqm: Number(property.sizeSqm),
                        bedrooms: Number(property.bedrooms),
                        type: property.type,
                        berRating: property.berRating
                    };

                    if (
                        !valuationData.county ||
                        !Number.isFinite(valuationData.sizeSqm) ||
                        !Number.isFinite(valuationData.bedrooms) ||
                        !valuationData.type ||
                        !valuationData.berRating
                    ) {
                        throw new Error("Some property information is missing.");
                    }

                    const result = await requestAssessment(
                        "/valuation",
                        token,
                        valuationData
                    );

                    if (!ignore) {
                        setValuationResult(result);
                        setValuationStatus("Complete");
                    }

                } catch (error) {
                    console.error("Valuation API error:", error);

                    if (!ignore) {
                        setValuationStatus("Pending");
                        setValuationMessage(error.message);
                    }
                }

            } catch (error) {
                console.error("Unable to start assessments:", error);

                if (!ignore) {
                    setAffordabilityStatus("Pending");
                    setAffordabilityMessage(error.message);

                    setValuationStatus("Pending");
                    setValuationMessage(error.message);
                }
            }
        }

        runAssessments();

        return () => {
            ignore = true;
        };
    }, [selectedApplication]);

    return (
        <main className="ai-analysis-page">
            <header className="page-header">
                <h2>AI Analysis</h2>
                <p>Review AI assessments and lending recommendations</p>
            </header>

            {loading && (
                <p>Loading applications...</p>
            )}

            {errorMessage && (
                <p>{errorMessage}</p>
            )}

            {!loading && applications.length === 0 && (
                <p>No applications are available for AI analysis.</p>
            )}

            {!loading && applications.length > 0 && (
                <>
                    {/* Applicant Selection */}
                    <section className="analysis-selection">
                        <label htmlFor="application-select">
                            Select Applicant
                        </label>

                        <select
                            id="application-select"
                            value={selectedApplicationId}
                            onChange={(event) =>
                                setSelectedApplicationId(event.target.value)
                            }
                        >
                            <option value="">Select an applicant</option>

                            {applications.map((application) => (
                                <option
                                    key={application.id}
                                    value={application.id}
                                >
                                    {application.applicantName}
                                </option>
                            ))}
                        </select>
                    </section>

                    {selectedApplication && (
                        <>
                            {/* Final Decision */}
                            <section className="final-decision">
                                <header className="decision-header">
                                    <div>
                                        <h3>
                                            AI Deliberation: {selectedApplication.applicantName}
                                        </h3>

                                        <p>
                                            Reference: {selectedApplication.id}
                                        </p>
                                    </div>

                                    <button type="button" disabled>
                                        Credit Memo
                                    </button>
                                </header>

                                <div className="decision-result">
                                    <h3>Final Decision: Pending AI Assessment</h3>
                                    <p>Consensus: Awaiting agent results</p>
                                </div>
                            </section>

                            {/* Agent Results */}
                            <section className="agent-results">

                                {/* Affordability Agent */}
                                <article className="agent-row">
                                    <div>
                                        <h3>Affordability Agent</h3>

                                        <p>
                                            {affordabilityResult || affordabilityMessage || "Running affordability assessment..."}
                                        </p>
                                    </div>

                                    <strong className="agent-pending">
                                        {affordabilityStatus}
                                    </strong>
                                </article>

                                {/* Market & Macro Agent */}
                                <article className="agent-row">
                                    <div>
                                        <h3>Market & Macro Agent</h3>
                                        <p>Agent not yet connected to the API.</p>
                                    </div>

                                    <strong className="agent-pending">
                                        Pending
                                    </strong>
                                </article>

                                {/* Valuation Agent */}
                                <article className="agent-row">
                                    <div>
                                        <h3>Valuation Agent</h3>

                                        <p>
                                            {valuationResult || valuationMessage || "Running property valuation..."}
                                        </p>
                                    </div>

                                    <strong className="agent-pending">
                                        {valuationStatus}
                                    </strong>
                                </article>

                                {/* Underwriting Strategist */}
                                <article className="agent-row">
                                    <div>
                                        <h3>Underwriting Strategist</h3>
                                        <p>Awaiting the underwriting API integration.</p>
                                    </div>

                                    <strong className="agent-pending">
                                        Pending
                                    </strong>
                                </article>

                            </section>

                            {/* Agent Reasoning */}
                            <section className="agent-reasoning">
                                <h3>Agent Reasoning</h3>

                                <p>
                                    Assessment explanations will appear here
                                    once the relevant agents return their results.
                                </p>
                            </section>
                        </>
                    )}
                </>
            )}
        </main>
    );
}

export default AIAnalysis;