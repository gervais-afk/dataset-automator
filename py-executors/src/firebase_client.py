import os
import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import threading
import time

def init_firebase():
    if not firebase_admin._apps:
        # Configuration pour l'émulateur local
        if not os.environ.get('FIRESTORE_EMULATOR_HOST'):
            os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8080'
        
        try:
            # S'il y a un fichier serviceAccountKey.json, on l'utilise
            if os.path.exists('serviceAccountKey.json'):
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            else:
                # Sinon on utilise le projet local pour l'émulateur
                firebase_admin.initialize_app(options={'projectId': 'dataset-automator-local'})
        except Exception as e:
            sys.stderr.write(f"⚠️ Erreur initialisation Firebase: {e}\n")

def get_firestore_db():
    init_firebase()
    try:
        return firestore.client()
    except Exception as e:
        sys.stderr.write(f"⚠️ Erreur connexion Firestore: {e}\n")
        return None

def update_job_progress(job_id: str, status: str, progress: int, message: str, artifacts: dict = None):
    """
    Met à jour la progression d'un job dans Firestore (Asynchrone/Non-bloquant).
    """
    if not job_id:
        return
        
    db = get_firestore_db()
    if not db:
        return
        
    try:
        doc_ref = db.collection('ml_jobs').document(job_id)
        updates = {
            'status': status,
            'progress_percent': progress,
            'current_message': message,
            'updated_at': datetime.datetime.utcnow().isoformat() + 'Z'
        }
        if artifacts:
            # Merge with existing artifacts
            doc = doc_ref.get()
            if doc.exists:
                current_artifacts = doc.to_dict().get('artifacts', {})
                current_artifacts.update(artifacts)
                updates['artifacts'] = current_artifacts
            else:
                updates['artifacts'] = artifacts
                
        doc_ref.set(updates, merge=True)
    except Exception as e:
        # On attrape l'erreur silencieusement pour ne pas crasher le pipeline ML
        sys.stderr.write(f"⚠️ Impossible de mettre à jour Firestore: {e}\n")

# ==========================================
# HEARTBEAT MANAGER (Surveillance des crashs)
# ==========================================
class HeartbeatManager:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self.job_id = None
        
    def _heartbeat_loop(self):
        db = get_firestore_db()
        while not self._stop_event.is_set():
            if self.job_id and db:
                try:
                    doc_ref = db.collection('ml_jobs').document(self.job_id)
                    doc_ref.set({
                        'last_heartbeat': datetime.datetime.utcnow().isoformat() + 'Z'
                    }, merge=True)
                except Exception as e:
                    sys.stderr.write(f"⚠️ Erreur Heartbeat: {e}\n")
            
            # Attendre 10 secondes (ou s'arrêter si l'Event est set)
            self._stop_event.wait(10)

    def start(self, job_id: str):
        self.job_id = job_id
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        sys.stderr.write(f"💓 Heartbeat démarré pour le job: {job_id}\n")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            sys.stderr.write("🛑 Heartbeat arrêté.\n")

# Instance globale
_heartbeat_manager = HeartbeatManager()

def start_heartbeat(job_id: str):
    _heartbeat_manager.start(job_id)

def stop_heartbeat():
    _heartbeat_manager.stop()
