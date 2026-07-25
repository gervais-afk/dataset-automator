import pandas as pd
import numpy as np

class DataContract:
    def __init__(self, target_col=None, task_type="regression", date_col=None, expected_columns=None, max_missing_pct=0.5):
        self.target_col = target_col
        self.task_type = task_type
        self.date_col = date_col
        self.expected_columns = expected_columns or []
        self.max_missing_pct = max_missing_pct

    def validate(self, df: pd.DataFrame) -> dict:
        """
        Valide le dataframe par rapport au contrat.
        Retourne un dictionnaire avec le statut de validation et les anomalies détectées.
        """
        anomalies = []
        status = "PASSED"
        
        # 1. Vérification des colonnes attendues
        if self.expected_columns:
            missing_cols = set(self.expected_columns) - set(df.columns)
            if missing_cols:
                status = "FAILED"
                anomalies.append({
                    "type": "missing_columns",
                    "severity": "CRITICAL",
                    "message": f"Colonnes attendues manquantes : {missing_cols}"
                })
        
        # 2. Vérification de la cible
        if self.target_col:
            if self.target_col not in df.columns:
                status = "FAILED"
                anomalies.append({
                    "type": "missing_target",
                    "severity": "CRITICAL",
                    "message": f"La colonne cible '{self.target_col}' est absente du dataset."
                })
            else:
                # La cible ne doit pas être totalement vide
                null_pct = df[self.target_col].isnull().mean()
                if null_pct == 1.0:
                    status = "FAILED"
                    anomalies.append({
                        "type": "empty_target",
                        "severity": "CRITICAL",
                        "message": "La colonne cible ne contient que des valeurs nulles."
                    })
                elif null_pct > 0.1:
                    anomalies.append({
                        "type": "high_target_missingness",
                        "severity": "MEDIUM",
                        "message": f"La colonne cible contient {null_pct:.1%} de valeurs manquantes."
                    })
        
        # 3. Vérification de la colonne de date pour les séries temporelles
        if self.task_type == "timeseries" or self.date_col:
            d_col = self.date_col or "Date"
            if d_col not in df.columns:
                status = "FAILED"
                anomalies.append({
                    "type": "missing_date_column",
                    "severity": "CRITICAL",
                    "message": f"La colonne temporelle '{d_col}' requise est absente."
                })
            else:
                # Vérifier que les dates peuvent être converties
                try:
                    converted = pd.to_datetime(df[d_col], errors='coerce')
                    invalid_dates = converted.isnull().sum()
                    if invalid_dates > 0:
                        anomalies.append({
                            "type": "invalid_dates",
                            "severity": "MEDIUM",
                            "message": f"Présence de {invalid_dates} dates invalides dans '{d_col}'."
                        })
                    
                    # Vérifier l'unicité des dates
                    if converted.duplicated().any():
                        anomalies.append({
                            "type": "duplicate_timestamps",
                            "severity": "MEDIUM",
                            "message": "Le dataset contient des horodatages (timestamps) doublons."
                        })
                except Exception as e:
                    status = "FAILED"
                    anomalies.append({
                        "type": "date_parsing_error",
                        "severity": "CRITICAL",
                        "message": f"Impossible de parser la colonne de dates : {e}"
                    })
        
        # 4. Vérification générale du taux de valeurs manquantes par colonne
        for col in df.columns:
            missing_pct = df[col].isnull().mean()
            if missing_pct > self.max_missing_pct:
                anomalies.append({
                    "type": "excessive_missingness",
                    "severity": "MEDIUM",
                    "message": f"La colonne '{col}' dépasse le taux maximal autorisé avec {missing_pct:.1%} de valeurs manquantes."
                })

        return {
            "status": status,
            "anomalies": anomalies,
            "rows": len(df),
            "columns": len(df.columns)
        }
