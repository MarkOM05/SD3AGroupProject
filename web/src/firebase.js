import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your group's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBTEI7vj2MQcvoDaQAE7NsZHHk8wY5hi4E",
  authDomain: "alagenticlender.firebaseapp.com",
  projectId: "alagenticlender",
  storageBucket: "alagenticlender.firebasestorage.app",
  messagingSenderId: "731024494474",
  appId: "1:731024494474:web:82d0c227f4681532298273",
  measurementId: "G-4X5DW8DZCT"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);

export default app;