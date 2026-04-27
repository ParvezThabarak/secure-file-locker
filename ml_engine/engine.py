"""
ML Engine for Secure File Locker v2
====================================
Three models working together:
  1. Random Forest Classifier   — predicts file category from extension/size/type
  2. Isolation Forest           — detects anomalous upload/access behaviour
  3. Threat Scorer              — combines signals into a 0-1 risk score
"""
import os, joblib, numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import LabelEncoder

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

RF_PATH  = os.path.join(MODEL_DIR, 'file_classifier.pkl')
ISO_PATH = os.path.join(MODEL_DIR, 'anomaly_detector.pkl')
ENC_PATH = os.path.join(MODEL_DIR, 'label_encoder.pkl')

# ── Extension → numeric mapping ──────────────────────────────────────────────
EXT_MAP = {
    '.txt':0, '.md':0, '.csv':0, '.log':0,        # document
    '.pdf':1, '.docx':1, '.xlsx':1, '.pptx':1,    # office
    '.jpg':2, '.jpeg':2, '.png':2, '.gif':2,       # image
    '.mp4':3, '.mp3':3, '.wav':3, '.avi':3,        # media
    '.zip':4, '.tar':4, '.gz':4, '.rar':4,         # archive
    '.py':5, '.js':5, '.html':5, '.css':5,         # code
    '.exe':6, '.sh':6, '.bat':6, '.dll':6,         # executable
}
CATEGORY_LABELS = ['document','office','image','media','archive','code','executable','other']


def _ext_to_num(ext: str) -> int:
    return EXT_MAP.get(ext.lower(), 7)


def _build_rf_training_data():
    """Synthetic training data for the Random Forest file classifier."""
    rng = np.random.default_rng(42)
    X, y = [], []
    for ext_num, label_idx in [
        (0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)
    ]:
        for _ in range(120):
            size_kb = rng.uniform(1, 50000)
            hour    = rng.integers(0, 24)
            X.append([ext_num, size_kb, hour, label_idx])
            y.append(label_idx)
    # Executables tend to be larger
    for _ in range(60):
        size_kb = rng.uniform(500, 100000)
        hour    = rng.integers(0, 24)
        X.append([6, size_kb, hour, 6])
        y.append(6)
    return np.array(X), np.array(y)


def _build_iso_training_data():
    """Normal usage data for Isolation Forest (anomaly = outlier)."""
    rng = np.random.default_rng(42)
    n = 1000
    # Normal: daytime uploads (8-20h), moderate file sizes, extension 0-5
    hours    = rng.integers(8, 20, n)
    sizes    = rng.exponential(500, n)            # KB, typically small-medium
    exts     = rng.integers(0, 6, n)
    day_of_w = rng.integers(0, 5, n)              # weekdays
    X = np.column_stack([hours, sizes, exts, day_of_w])
    return X


# ── Train and persist models ──────────────────────────────────────────────────
def train_models(force=False):
    """Train both models if not already saved (or force=True)."""
    if not force and os.path.exists(RF_PATH) and os.path.exists(ISO_PATH):
        return  # Already trained

    # Random Forest classifier
    X_rf, y_rf = _build_rf_training_data()
    le = LabelEncoder()
    le.fit(CATEGORY_LABELS)
    rf = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_rf[:, :3], y_rf)   # features: ext_num, size_kb, upload_hour
    joblib.dump(rf, RF_PATH)
    joblib.dump(le, ENC_PATH)

    # Isolation Forest anomaly detector
    X_iso = _build_iso_training_data()
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.05,   # expect 5% anomalies
        random_state=42,
        n_jobs=-1
    )
    iso.fit(X_iso)
    joblib.dump(iso, ISO_PATH)


def _load_models():
    train_models()
    rf  = joblib.load(RF_PATH)
    iso = joblib.load(ISO_PATH)
    le  = joblib.load(ENC_PATH)
    return rf, iso, le


# ── Public API ────────────────────────────────────────────────────────────────
def classify_file(filename: str, file_size_bytes: int) -> dict:
    """
    Predict file category using Random Forest.
    Returns: { category, confidence, label_index }
    """
    ext      = os.path.splitext(filename)[1].lower()
    ext_num  = _ext_to_num(ext)
    size_kb  = file_size_bytes / 1024
    hour     = datetime.now().hour
    features = np.array([[ext_num, size_kb, hour]])

    rf, _, le = _load_models()
    label_idx  = int(rf.predict(features)[0])
    proba      = rf.predict_proba(features)[0]
    confidence = float(proba[label_idx])
    category   = CATEGORY_LABELS[label_idx] if label_idx < len(CATEGORY_LABELS) else 'other'

    return {
        'category':   category,
        'confidence': round(confidence, 3),
        'label_index': label_idx
    }


def detect_anomaly(file_size_bytes: int, ext: str, upload_hour: int = None,
                   day_of_week: int = None) -> dict:
    """
    Isolation Forest anomaly detection.
    Returns: { is_anomaly, anomaly_score, reason }
    """
    if upload_hour is None:
        upload_hour = datetime.now().hour
    if day_of_week is None:
        day_of_week = datetime.now().weekday()

    ext_num  = _ext_to_num(ext)
    size_kb  = file_size_bytes / 1024
    features = np.array([[upload_hour, size_kb, ext_num, day_of_week]])

    _, iso, _ = _load_models()
    prediction     = iso.predict(features)[0]     # -1 = anomaly, 1 = normal
    anomaly_score  = float(-iso.score_samples(features)[0])  # higher = more anomalous
    is_anomaly     = prediction == -1

    reasons = []
    if upload_hour < 2 or upload_hour > 22:
        reasons.append("unusual upload time")
    if size_kb > 30_000:
        reasons.append("very large file")
    if ext in ('.exe', '.bat', '.sh', '.dll'):
        reasons.append("executable file type")
    if day_of_week >= 5:
        reasons.append("weekend upload")

    return {
        'is_anomaly':    is_anomaly,
        'anomaly_score': round(anomaly_score, 4),
        'reason':        ', '.join(reasons) if reasons else 'normal pattern'
    }


def compute_threat_score(filename: str, file_size_bytes: int,
                         user_failed_logins: int = 0,
                         is_new_user: bool = False) -> dict:
    """
    Composite threat scorer combining ML signals + heuristics.
    Returns: { score (0-1), level, breakdown }
    """
    ext = os.path.splitext(filename)[1].lower()

    clf_result = classify_file(filename, file_size_bytes)
    ano_result = detect_anomaly(file_size_bytes, ext)

    # Component scores (0-1 each)
    exec_risk     = 0.8  if ext in ('.exe', '.bat', '.sh', '.dll', '.vbs') else 0.0
    category_risk = 0.6  if clf_result['category'] == 'executable' else 0.05
    anomaly_risk  = min(1.0, ano_result['anomaly_score'] * 1.5) if ano_result['is_anomaly'] else 0.0
    login_risk    = min(0.5, user_failed_logins * 0.1)
    new_user_risk = 0.15 if is_new_user else 0.0
    size_risk     = min(0.3, (file_size_bytes / (50 * 1024 * 1024)) * 0.3)

    # Weighted composite
    score = (
        exec_risk     * 0.45 +
        category_risk * 0.25 +
        anomaly_risk  * 0.15 +
        login_risk    * 0.10 +
        new_user_risk * 0.03 +
        size_risk     * 0.02
    )
    score = round(min(1.0, score), 3)

    if score < 0.3:   level = 'LOW'
    elif score < 0.6: level = 'MEDIUM'
    elif score < 0.8: level = 'HIGH'
    else:             level = 'CRITICAL'

    return {
        'score':      float(score),
        'level':      level,
        'breakdown': {
            'executable_type': float(round(exec_risk, 3)),
            'category_risk':   float(round(category_risk, 3)),
            'anomaly_risk':    float(round(anomaly_risk, 3)),
            'login_risk':      float(round(login_risk, 3)),
            'new_user_risk':   float(round(new_user_risk, 3)),
            'size_risk':       float(round(size_risk, 3)),
        },
        'category':       clf_result['category'],
        'is_anomaly':     bool(ano_result['is_anomaly']),
        'anomaly_reason': ano_result['reason'],
        'confidence':     float(clf_result['confidence']),
    }


def get_ml_stats() -> dict:
    """Return summary stats about ML models for admin dashboard."""
    train_models()
    rf, iso, _ = _load_models()
    return {
        'classifier':      'Random Forest',
        'n_estimators_rf': rf.n_estimators,
        'detector':        'Isolation Forest',
        'n_estimators_iso': iso.n_estimators,
        'contamination':   iso.contamination,
        'model_files':     [os.path.basename(p) for p in [RF_PATH, ISO_PATH, ENC_PATH]],
        'status':          'trained'
    }
