import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import {
  getAuth,
  connectAuthEmulator,
  type Auth,
} from "firebase/auth";
import { getFirestore, connectFirestoreEmulator, type Firestore } from "firebase/firestore";
import { getStorage, connectStorageEmulator, type FirebaseStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN ?? "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET ?? "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ?? "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID ?? "",
};

/** True se la config Firebase è utilizzabile (no key vuota/dummy di build). */
function hasFirebaseConfig(): boolean {
  const key = firebaseConfig.apiKey;
  return Boolean(key && key !== "dummy-key" && key.length > 10);
}

let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;
let _db: Firestore | null = null;
let _storage: FirebaseStorage | null = null;

function ensureApp(): FirebaseApp {
  if (_app) return _app;
  if (!hasFirebaseConfig()) {
    throw new Error(
      "Firebase non configurato (NEXT_PUBLIC_FIREBASE_API_KEY mancante o dummy)."
    );
  }
  _app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
  return _app;
}

/**
 * Accesso lazy — evita crash in fase di `next build` / prerender quando
 * le NEXT_PUBLIC_* non sono ancora iniettate o sono placeholder.
 */
function requireAuth(): Auth {
  if (!_auth) {
    _auth = getAuth(ensureApp());
    if (
      process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_USE_EMULATOR === "true" &&
      !_auth.emulatorConfig
    ) {
      connectAuthEmulator(_auth, "http://localhost:9099", { disableWarnings: true });
    }
  }
  return _auth;
}

function requireDb(): Firestore {
  if (!_db) {
    _db = getFirestore(ensureApp());
    if (
      process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_USE_EMULATOR === "true"
    ) {
      connectFirestoreEmulator(_db, "localhost", 8080);
    }
  }
  return _db;
}

function requireStorage(): FirebaseStorage {
  if (!_storage) {
    _storage = getStorage(ensureApp());
    if (
      process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_USE_EMULATOR === "true"
    ) {
      connectStorageEmulator(_storage, "localhost", 9199);
    }
  }
  return _storage;
}

// Proxy: `auth.xxx` inizializza solo al primo accesso reale
export const auth: Auth = new Proxy({} as Auth, {
  get(_t, prop) {
    const a = requireAuth();
    const v = Reflect.get(a as object, prop);
    return typeof v === "function" ? (v as (...n: unknown[]) => unknown).bind(a) : v;
  },
});

export const firestoreDb: Firestore = new Proxy({} as Firestore, {
  get(_t, prop) {
    const d = requireDb();
    const v = Reflect.get(d as object, prop);
    return typeof v === "function" ? (v as (...n: unknown[]) => unknown).bind(d) : v;
  },
});

export const storage: FirebaseStorage = new Proxy({} as FirebaseStorage, {
  get(_t, prop) {
    const s = requireStorage();
    const v = Reflect.get(s as object, prop);
    return typeof v === "function" ? (v as (...n: unknown[]) => unknown).bind(s) : v;
  },
});

export { hasFirebaseConfig };
