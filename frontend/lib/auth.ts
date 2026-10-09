import {
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
  getIdToken,
} from "firebase/auth";
import { auth } from "./firebase";

export async function login(email: string, password: string) {
  return signInWithEmailAndPassword(auth, email, password);
}

export async function logout() {
  return signOut(auth);
}

export function onAuthChange(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback);
}

export async function getAuthToken(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  try {
    return await getIdToken(user, false);
  } catch (err: unknown) {
    // Token refresh failed (network error, token revoked, etc.)
    // Sign out so the user is redirected to login on next protected action.
    await signOut(auth).catch(() => {});
    const code = (err as { code?: string }).code ?? "";
    throw new Error(
      code === "auth/network-request-failed" || String(err).includes("ERR_ABORTED")
        ? "Sessione scaduta: controlla la connessione e accedi di nuovo."
        : "Sessione scaduta. Effettua nuovamente il login."
    );
  }
}
