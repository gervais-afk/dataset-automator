import { initializeApp } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';

process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080';
initializeApp({ projectId: 'demo-no-project' });

const db = getFirestore();

async function test() {
  console.log("Fetching jobs from Firestore Emulator...");
  const snapshot = await db.collection('ml_jobs').orderBy('started_at', 'desc').limit(1).get();
  if (snapshot.empty) {
    console.log("No jobs found in database.");
    return;
  }
  
  const job = snapshot.docs[0];
  if (!job) {
    console.log("No job available.");
    return;
  }
  console.log("Latest Job ID:", job.id);
  console.log("Job Data:", JSON.stringify(job.data(), null, 2));
}

test().catch(console.error);
