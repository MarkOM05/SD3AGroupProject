import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
	createUserWithEmailAndPassword,
	signInWithEmailAndPassword,
	updateProfile
} from "firebase/auth";
import { auth } from "../firebase";
//import { doc, setDoc } from "firebase/firestore";

function Auth() {
	const [isSignUp, setIsSignUp] = useState(false);
	const [name, setName] = useState("");
	const [role, setRole] = useState("borrower");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState("");
	const [message, setMessage] = useState("");
	const [loading, setLoading] = useState(false);

	const navigate = useNavigate();

	async function handleSubmit(event) {
		event.preventDefault();
		setError("");
		setMessage("");
		setLoading(true);

		try {
		  if (isSignUp) {
			const userCredential =
			  await createUserWithEmailAndPassword(auth, email, password);

			await updateProfile(userCredential.user, {
			  displayName: name
			});

			/*await setDoc(doc(db, "demoProfiles", userCredential.user.uid), {
			  name: name,
			  email: email,
			  selectedRole: role,
			  createdAt: new Date()
			});*/
		  } else {
			await signInWithEmailAndPassword(auth, email, password);
		  }
		  navigate("/dashboard");

		} catch (error) {
		  setError(error.message);

		} finally {
		  setLoading(false);
		}
	  }

	  let pageHeading = "Sign In";
	  let submitButtonText = "Sign In";
	  let accountMessage = "Don't have an account?";
	  let switchButtonText = "Sign Up";

	  if (isSignUp) {
		pageHeading = "Create an Account";
		submitButtonText = "Sign Up";
		accountMessage = "Already have an account?";
		switchButtonText = "Sign In";
	  }

	  let submitButtonContent = submitButtonText;

	  if (loading) {
		submitButtonContent = "Please wait...";
	  }

	  return (
		<main>
		  <h1>Agentic Lender</h1>

		  <h2>{pageHeading}</h2>

		  <form onSubmit={handleSubmit}>
			{isSignUp && (
			  <>
				<div>
				  <label htmlFor="name">Full Name</label>
				  <input
					id="name"
					type="text"
					value={name}
					onChange={(event) => setName(event.target.value)}
					required
				  />
				</div>

				<div>
				  <label htmlFor="role">Select Your Role</label>
				  <select
					id="role"
					value={role}
					onChange={(event) => setRole(event.target.value)}
					required
				  >
					<option value="broker">Broker</option>
					<option value="underwriter">Underwriter</option>
				  </select>
				</div>
			  </>
			)}

			<div>
			  <label htmlFor="email">Email Address</label>
			  <input
				id="email"
				type="email"
				value={email}
				onChange={(event) => setEmail(event.target.value)}
				required
			  />
			</div>

			<div>
			  <label htmlFor="password">Password</label>
			  <input
				id="password"
				type="password"
				value={password}
				onChange={(event) => setPassword(event.target.value)}
				minLength={6}
				required
			  />
			</div>

			{error && <p role="alert">{error}</p>}
			{message && <p>{message}</p>}

			<button type="submit" disabled={loading}>
			  {submitButtonContent}
			</button>
		  </form>

		  <p>
			{accountMessage}

			{" "}

			<button
			  type="button"
			  onClick={() => {
				if (isSignUp) {
				  setIsSignUp(false);
				} else {
				  setIsSignUp(true);
				}

				setError("");
				setMessage("");
			  }}
			>
			  {switchButtonText}
			</button>
		  </p>
		</main>
	  );
}

export default Auth;