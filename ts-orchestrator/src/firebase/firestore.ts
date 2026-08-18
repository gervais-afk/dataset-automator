import { initializeApp, getApps } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import pino from 'pino';

const logger = pino({
  transport: {
    target: 'pino-pretty'
  }
});

// Configured for local emulator by default
if (!getApps().length) {
    // By default, if FIRESTORE_EMULATOR_HOST is not set,
    // we force it to facilitate local testing for the user.
    if (!process.env.FIRESTORE_EMULATOR_HOST) {
        process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080';
    }
    
    logger.info(`🔥 Firebase Admin initialized via Local Emulator (${process.env.FIRESTORE_EMULATOR_HOST})`);
    initializeApp({
        projectId: 'demo-no-project',
    });
}

const db = getFirestore();

export interface MLJob {
    job_id: string;
    dataset_name: string;
    status: 'initialized' | 'adversarial_check' | 'cleaning' | 'evaluating' | 'training_optuna' | 'explainability_audit' | 'generating_notebook' | 'completed' | 'failed' | 'awaiting_human_review' | 'rejected_by_human';
    progress_percent: number;
    current_message: string;
    started_at: string;
    updated_at: string;
    
    // Self-Healing Tracking
    retries_count?: number;
    last_zod_error?: string;
    strategy_source?: 'human_validated' | 'self_healing' | 'fallback';
    last_heartbeat?: string | number;
    
    // New Agents
    adversarial_validation?: any;
    explainability_audit?: any;
    
    artifacts: {
        pca_url?: string;
        confusion_matrix_url?: string;
        notebook_url?: string;
    };
}

export class FirestoreService {
    static async createJob(datasetName: string): Promise<string> {
        const jobId = `job_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
        const jobRef = db.collection('ml_jobs').doc(jobId);
        
        const newJob: MLJob = {
            job_id: jobId,
            dataset_name: datasetName,
            status: 'initialized',
            progress_percent: 0,
            current_message: 'Job initialized by TypeScript Orchestrator',
            started_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            artifacts: {}
        };
        
        await jobRef.set(newJob);
        logger.info(`📝 Job created in Firestore: ${jobId}`);
        return jobId;
    }

    static async updateJobStatus(jobId: string, updates: Partial<MLJob>) {
        const jobRef = db.collection('ml_jobs').doc(jobId);
        updates.updated_at = new Date().toISOString();
        try {
            await jobRef.update(updates);
        } catch (error: any) {
            // If the document doesn't exist (e.g., emulator restart), recreate it via set with merge: true
            if (error.code === 5 || error.message.includes('NOT_FOUND') || error.message.includes('no entity to update')) {
                logger.warn(`⚠️ Document ${jobId} not found for update. Recreating via set(..., { merge: true }).`);
                await jobRef.set(updates, { merge: true });
            } else {
                throw error;
            }
        }
    }
    
    static async getJob(jobId: string): Promise<MLJob | null> {
        const doc = await db.collection('ml_jobs').doc(jobId).get();
        if (!doc.exists) return null;
        return doc.data() as MLJob;
    }
}
