import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
from pathlib import Path
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class AISAnomalyDetector:
    """
    Machine learning model for detecting anomalous AIS behavior

    Uses unsupervised learning to identify vessels with suspicious patterns:
    - Unusual transmission gaps
    - Abnormal speed/course changes
    - Suspicious spatial patterns
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path

        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def extract_features(self, ais_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from AIS data for anomaly detection

        Features include:
        1. Temporal patterns: transmission frequency, gap statistics
        2. Spatial patterns: speed variance, course changes
        3. Behavioral patterns: nighttime activity, distance from shore
        """
        features_list = []

        # Group by vessel
        for mmsi, vessel_data in ais_df.groupby('mmsi'):
            vessel_data = vessel_data.sort_values('timestamp').reset_index(drop=True)

            if len(vessel_data) < 3:
                continue

            # Calculate time gaps
            vessel_data['time_diff'] = vessel_data['timestamp'].diff().dt.total_seconds() / 3600

            # Temporal features
            avg_gap = vessel_data['time_diff'].mean()
            std_gap = vessel_data['time_diff'].std()
            max_gap = vessel_data['time_diff'].max()
            gap_cv = std_gap / avg_gap if avg_gap > 0 else 0  # Coefficient of variation

            # Spatial features
            speed_mean = vessel_data['speed'].mean() if 'speed' in vessel_data else 0
            speed_std = vessel_data['speed'].std() if 'speed' in vessel_data else 0
            speed_max = vessel_data['speed'].max() if 'speed' in vessel_data else 0

            # Course change (if available)
            if 'course' in vessel_data.columns:
                vessel_data['course_diff'] = vessel_data['course'].diff().abs()
                course_change_mean = vessel_data['course_diff'].mean()
                course_change_max = vessel_data['course_diff'].max()
            else:
                course_change_mean = 0
                course_change_max = 0

            # Distance traveled
            vessel_data['lat_diff'] = vessel_data['lat'].diff()
            vessel_data['lon_diff'] = vessel_data['lon'].diff()
            total_distance = np.sqrt(
                vessel_data['lat_diff']**2 + vessel_data['lon_diff']**2
            ).sum() * 111  # Approx km

            # Behavioral features
            vessel_data['hour'] = vessel_data['timestamp'].dt.hour
            nighttime_ratio = len(vessel_data[
                (vessel_data['hour'] >= 18) | (vessel_data['hour'] <= 6)
            ]) / len(vessel_data)

            # Distance from shore (if available)
            distance_from_shore = vessel_data['distance_from_shore'].mean() if 'distance_from_shore' in vessel_data else 0

            # Compile features
            features = {
                'mmsi': mmsi,
                'avg_gap_hours': avg_gap,
                'std_gap_hours': std_gap,
                'max_gap_hours': max_gap,
                'gap_coefficient_variation': gap_cv,
                'speed_mean': speed_mean,
                'speed_std': speed_std,
                'speed_max': speed_max,
                'course_change_mean': course_change_mean,
                'course_change_max': course_change_max,
                'total_distance_km': total_distance,
                'nighttime_activity_ratio': nighttime_ratio,
                'avg_distance_from_shore': distance_from_shore,
                'num_transmissions': len(vessel_data)
            }

            features_list.append(features)

        return pd.DataFrame(features_list)

    def train_isolation_forest(
        self,
        features_df: pd.DataFrame,
        contamination: float = 0.1
    ) -> None:
        """
        Train Isolation Forest model for anomaly detection

        Args:
            features_df: DataFrame with extracted features
            contamination: Expected proportion of anomalies (0.1 = 10%)
        """
        logger.info(f"Training Isolation Forest on {len(features_df)} vessels")

        # Select numeric features only
        feature_cols = [col for col in features_df.columns if col != 'mmsi']
        X = features_df[feature_cols].fillna(0)

        # Normalize features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )

        self.model.fit(X_scaled)
        logger.info("Model trained successfully")

    def predict_anomalies(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict anomalies in vessel behavior

        Returns:
            DataFrame with mmsi, anomaly_score, and is_anomaly flag
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train_isolation_forest() first.")

        feature_cols = [col for col in features_df.columns if col != 'mmsi']
        X = features_df[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)

        # Predict
        predictions = self.model.predict(X_scaled)  # -1 for anomaly, 1 for normal
        scores = self.model.score_samples(X_scaled)  # Anomaly score (lower = more anomalous)

        # Normalize scores to 0-1 range (higher = more anomalous)
        anomaly_scores = 1 / (1 + np.exp(scores))  # Sigmoid transformation

        results = features_df[['mmsi']].copy()
        results['anomaly_score'] = anomaly_scores
        results['is_anomaly'] = predictions == -1

        return results

    def cluster_anomalies(
        self,
        features_df: pd.DataFrame,
        eps: float = 0.5,
        min_samples: int = 5
    ) -> pd.DataFrame:
        """
        Use DBSCAN to cluster similar anomalous behaviors

        Helps identify patterns in suspicious activity
        """
        feature_cols = [col for col in features_df.columns if col != 'mmsi']
        X = features_df[feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)

        # DBSCAN clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = clustering.fit_predict(X_scaled)

        results = features_df[['mmsi']].copy()
        results['cluster'] = clusters  # -1 = noise/outlier

        return results

    def save_model(self, filepath: str) -> None:
        """Save trained model and scaler"""
        if self.model is None:
            raise ValueError("No model to save")

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str) -> None:
        """Load pre-trained model"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        logger.info(f"Model loaded from {filepath}")

    def get_feature_importance(self, features_df: pd.DataFrame, top_n: int = 10):
        """
        Get most important features for anomaly detection

        Uses feature contribution to anomaly scores
        """
        if self.model is None:
            raise ValueError("Model not trained")

        feature_cols = [col for col in features_df.columns if col != 'mmsi']
        X = features_df[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)

        # Calculate feature contributions (simplified)
        feature_importance = np.abs(X_scaled).mean(axis=0)

        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)

        return importance_df.head(top_n)
