# ==== diet_model_rf_weka_summary_full.py ====
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline as SkPipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report, confusion_matrix,
    precision_recall_fscore_support, cohen_kappa_score
)
import joblib, os

# ---------- 1) หาไฟล์ CSV อัตโนมัติ ----------
ROOT_DIRS = [Path.cwd(), Path(r"C:\Users\ACER\OneDrive\Desktop\s3")]
PATTERNS = ["*data*set*is*.csv", "*dataset*is*.csv", "*.csv"]

def find_csv(roots, patterns):
    for root in roots:
        if not root.exists(): continue
        for pat in patterns:
            for p in root.glob(pat):
                if p.is_file(): return p.resolve()
    return None

csv_path = find_csv(ROOT_DIRS, PATTERNS)
if not csv_path:
    raise FileNotFoundError("ไม่พบไฟล์ CSV — วางไฟล์ไว้โฟลเดอร์เดียวกับสคริปต์หรือแก้ ROOT_DIRS")
print(f"✅ ใช้ไฟล์: {csv_path}")

# ---------- 2) อ่านข้อมูล (กันพังหลาย encoding/sep) ----------
read_ok, last_err = False, None
for sep in [None, ",", ";", "\t", "|"]:
    for enc in ["utf-8-sig", "utf-8", "cp874", "latin-1"]:
        try:
            df = pd.read_csv(csv_path, sep=sep, encoding=enc, engine="python")
            read_ok = True
            print(f"   → อ่านสำเร็จด้วย sep={repr(sep)}, encoding='{enc}'")
            break
        except Exception as e:
            last_err = e
    if read_ok: break
if not read_ok:
    raise RuntimeError(f"อ่านไฟล์ไม่สำเร็จ: {last_err}")

# ---------- 3) Target / Features ----------
POSSIBLE_TARGETS = ["Diet_Recommendation", "diet_recommendation", "Target"]
target_col = next((c for c in POSSIBLE_TARGETS if c in df.columns), None)
if not target_col:
    raise KeyError(f"ไม่พบคอลัมน์ Target ใน {list(df.columns)}")

y_text = df[target_col]
X = df.drop(columns=[target_col])

print("🎯 ตัวอย่าง Target:", y_text.unique()[:5])
print("📊 สัดส่วนคลาส:\n", y_text.value_counts(normalize=True).round(3))

# ---------- 4) เข้ารหัสเป้าหมาย + แยกชนิดคอลัมน์ ----------
le = LabelEncoder()
y = le.fit_transform(y_text)
categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
numeric_cols     = X.select_dtypes(include=[np.number]).columns.tolist()
print("🔖 Target mapping:", {cls: int(i) for i, cls in enumerate(le.classes_)})

# ---------- 5) Train/Test split ----------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)

# ---------- 6) Preprocessor ----------
try:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)  # sklearn >=1.2
except TypeError:
    ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)         # sklearn <1.2

preprocessor = ColumnTransformer(
    [("cat", ohe, categorical_cols),
     ("num", StandardScaler(), numeric_cols)],
    remainder="drop"
)

# ---------- 7) Pipeline + (optional) SMOTE ----------
use_smote = False
try:
    from imblearn.over_sampling import SMOTE
    from imblearn.pipeline import Pipeline as ImbPipeline
    smote = SMOTE(random_state=42)
    use_smote = True
    print("🔄 จะใช้ SMOTE ระหว่างฝึก (พบ imbalanced-learn)")
except Exception:
    smote = None
    print("ℹ️ ไม่พบ imbalanced-learn → ข้าม SMOTE")

rf = RandomForestClassifier(
    random_state=42, class_weight="balanced", n_jobs=-1
)

if use_smote:
    train_pipe = ImbPipeline([("prep", preprocessor), ("smote", smote), ("model", rf)])
else:
    train_pipe = SkPipeline([("prep", preprocessor), ("model", rf)])

# ---------- 8) RandomizedSearch + CV ----------
param_dist = {
    "model__n_estimators": [150, 250, 400, 600],
    "model__max_depth": [None, 8, 12, 20],
    "model__min_samples_split": [2, 5, 10],
    "model__min_samples_leaf": [1, 2, 4],
    "model__max_features": ["sqrt", "log2", None],
}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
search = RandomizedSearchCV(
    estimator=train_pipe, param_distributions=param_dist,
    n_iter=12, scoring="f1_macro", cv=cv, n_jobs=-1, random_state=42, verbose=1
)
search.fit(X_train, y_train)
print(f"\n🏆 Best CV F1_macro: {search.best_score_:.4f}")
print("🔧 Best params:", search.best_params_)

best_model = search.best_estimator_

# ---------- 9) Inference model (ตัด SMOTE ตอนทำนาย) ----------
if "smote" in best_model.named_steps:
    prep_fitted  = best_model.named_steps["prep"]
    model_fitted = best_model.named_steps["model"]
    inference_model = SkPipeline([("prep", prep_fitted), ("model", model_fitted)])
else:
    inference_model = best_model

# ---------- 10) ทำนายพื้นฐาน ----------
y_pred_num = inference_model.predict(X_test)
y_pred_lbl = le.inverse_transform(y_pred_num)
y_test_lbl = le.inverse_transform(y_test)

print("\n📈 Test Accuracy :", round(accuracy_score(y_test_lbl, y_pred_lbl), 4))
print("🎯 Test F1_macro :", round(f1_score(y_test_lbl, y_pred_lbl, average='macro'), 4))
print("\n📋 Classification report:\n", classification_report(y_test_lbl, y_pred_lbl, target_names=le.classes_))
print("🧩 Confusion Matrix (เลขดิบ):\n", confusion_matrix(y_test_lbl, y_pred_lbl, labels=le.classes_))

# ---------- 11) WEKA-style Summary (ครบทุกหัวข้อที่ขอ) ----------
def weka_like_summary(y_test_lbl, y_pred_lbl, X_test, le, inference_model,
                      title="WEKA-STYLE EVALUATION", save_dir="eval_output_rf"):
    os.makedirs(save_dir, exist_ok=True)
    txt_path = Path(save_dir, "summary.txt")
    percls_csv = Path(save_dir, "detailed_accuracy_by_class.csv")
    cm_csv = Path(save_dir, "confusion_matrix.csv")

    # Align index + ignore class unknown instances
    y_true_s = pd.Series(y_test_lbl, index=X_test.index)
    y_pred_s = pd.Series(y_pred_lbl, index=X_test.index)
    mask = y_true_s.notna() & y_true_s.isin(le.classes_)  # ignore unknown
    y_true = y_true_s.loc[mask].values
    y_pred = y_pred_s.loc[mask].values
    X_eval = X_test.loc[mask]
    if len(y_true) == 0:
        raise ValueError("ไม่มี instance สำหรับประเมินหลัง ignore class unknown instances")

    classes = list(le.classes_)
    lines = []
    add = lines.append
    add(f"\n========== {title} ==========\n")
    add(f"Total number of instances (after ignore): {len(y_true)}")

    # 1) Detailed accuracy by class
    prec, rec, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=classes, zero_division=0
    )
    per_class_df = pd.DataFrame({
        "Class": classes, "Precision": prec, "Recall": rec, "F1-Score": f1, "Support": support.astype(int)
    })
    add("\n📊 Detailed Accuracy By Class")
    add(per_class_df.to_string(index=False))

    # 2) Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    cm_df = pd.DataFrame(cm, index=[f"true_{c}" for c in classes],
                            columns=[f"pred_{c}" for c in classes])
    add("\n🧩 Confusion Matrix (rows=true, cols=predicted)")
    add(cm_df.to_string())

    # 3) Correct/Incorrect/Total
    correct = int((y_true == y_pred).sum())
    total   = int(len(y_true))
    incorrect = total - correct
    acc_simple = correct / total if total > 0 else float("nan")
    add(f"\n✅ Correctly classified instances:   {correct} / {total}  ({acc_simple*100:.2f}%)")
    add(f"❌ Incorrectly classified instances: {incorrect} / {total}  ({(1-acc_simple)*100:.2f}%)")
    add(f"📦 Total number of instances:        {total}")
    add("🔎 (ignore class unknown instances เปิดใช้งานแล้ว)")

    # 4) Kappa
    y_true_num = le.transform(y_true)
    y_pred_num = le.transform(y_pred)
    kappa = cohen_kappa_score(y_true_num, y_pred_num)
    add(f"\n🤝 Kappa statistic: {kappa:.6f}")

    # 5) MAE/RMSE (probability-based)
    proba = inference_model.predict_proba(X_eval)  # [N, n_classes]
    cls_to_idx = {c:i for i,c in enumerate(classes)}
    y_true_idx = np.array([cls_to_idx[c] for c in y_true])
    y_onehot = np.eye(len(classes))[y_true_idx]
    abs_err = np.abs(y_onehot - proba).sum(axis=1) / 2.0
    mae = abs_err.mean()
    sq_err = ((y_onehot - proba) ** 2).sum(axis=1) / 2.0
    rmse = np.sqrt(sq_err.mean())
    add(f"\n📐 Mean absolute error (MAE): {mae:.6f}")
    add(f"📐 Root mean squared error (RMSE): {rmse:.6f}")

    # 6) RAE/RRSE เทียบ baseline (prior distribution)
    prior_counts = pd.Series(y_true).value_counts().reindex(classes, fill_value=0).values
    prior_dist = prior_counts / prior_counts.sum()
    abs_err_base = np.abs(y_onehot - prior_dist).sum(axis=1) / 2.0
    mae_base = abs_err_base.mean()
    sq_err_base = ((y_onehot - prior_dist) ** 2).sum(axis=1) / 2.0
    rmse_base = np.sqrt(sq_err_base.mean())
    rae  = (mae / mae_base) * 100.0 if mae_base > 0 else float("inf")
    rrse = (rmse / rmse_base) * 100.0 if rmse_base > 0 else float("inf")
    add(f"📏 Relative absolute error (RAE): {rae:.2f}%")
    add(f"📏 Root relative squared error (RRSE): {rrse:.2f}%")

    # print ครบ
    print("\n".join(lines))
    # save รายงาน/ตาราง
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    per_class_df.to_csv(percls_csv, index=False, encoding="utf-8-sig")
    cm_df.to_csv(cm_csv, encoding="utf-8-sig")
    print(f"\n💾 Saved report: {txt_path}")
    print(f"💾 Saved per-class metrics: {percls_csv}")
    print(f"💾 Saved confusion matrix: {cm_csv}")

    return {
        "per_class": per_class_df, "confusion_matrix": cm_df,
        "correct": correct, "incorrect": incorrect, "total": total,
        "kappa": kappa, "mae": mae, "rmse": rmse, "rae_pct": rae, "rrse_pct": rrse
    }

# เรียกสรุปผลแบบ WEKA‑style (ครบทั้งหมดที่ขอ)
_ = weka_like_summary(
    y_test_lbl=y_test_lbl,
    y_pred_lbl=y_pred_lbl,
    X_test=X_test,
    le=le,
    inference_model=inference_model,
    title="WEKA-STYLE EVALUATION (Random Forest)"
)

# ---------- 12) เซฟโมเดล + LabelEncoder ----------
joblib.dump(inference_model, "diet_recommendation_rf_model.joblib")
joblib.dump(le, "label_encoder.joblib")
print("\n💾 Saved: diet_recommendation_rf_model.joblib, label_encoder.joblib")

# ---------- 13) ฟังก์ชันทำนาย 1 รายการ ----------
def predict_one(sample_dict: dict):
    sample_df = pd.DataFrame([sample_dict]).reindex(columns=X.columns)
    for col in numeric_cols:
        sample_df[col] = pd.to_numeric(sample_df[col], errors="coerce")
    for col in categorical_cols:
        sample_df[col] = sample_df[col].astype(str)
    pred_num = inference_model.predict(sample_df)[0]
    pred_lbl = le.inverse_transform([pred_num])[0]
    proba = inference_model.predict_proba(sample_df)[0]
    return pred_lbl, dict(zip(le.classes_, map(float, proba)))

# ---- Demo ----
ex = X.iloc[0].to_dict()
lbl, pro = predict_one(ex)
print("\n🧪 Example prediction:", lbl, pro)
