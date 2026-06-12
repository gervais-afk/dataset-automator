import { initializeApp, getApps } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import pino from 'pino';

const logger = pino({
  transport: {
    target: 'pino-pretty'
  }
});

// Configure pour l'émulateur local par défaut
if (!getApps().length) {
    // Par défaut, si l'environnement FIRESTORE_EMULATOR_HOST n'est pas défini, 
    // on le force pour faciliter les tests locaux de l'utilisateur.
    if (!process.env.FIRESTORE_EMULATOR_HOST) {
        process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080';
    }
    
    logger.info(`🔥 Firebase Admin initialisé via l'Émulateur Local (${process.env.FIRESTORE_EMULATOR_HOST})`);
    initializeApp({
        projectId: 'dataset-automator-local',
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
    
    // Nouveaux Agents
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
            current_message: 'Job initialisé par l\'Orchestrateur TypeScript',
            started_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            artifacts: {}
        };
        
        await jobRef.set(newJob);
        logger.info(`📝 Job créé dans Firestore: ${jobId}`);
        return jobId;
    }

    static async updateJobStatus(jobId: string, updates: Partial<MLJob>) {
        const jobRef = db.collection('ml_jobs').doc(jobId);
        updates.updated_at = new Date().toISOString();
        await jobRef.update(updates);
    }
    
    static async getJob(jobId: string): Promise<MLJob | null> {
        const doc = await db.collection('ml_jobs').doc(jobId).get();
        if (!doc.exists) return null;
        return doc.data() as MLJob;
    }
}
