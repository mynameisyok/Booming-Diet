# server/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "diet_recommendation_rf_model.joblib"
LE_PATH    = BASE_DIR / "label_encoder.joblib"

app = FastAPI(title="BloomDiet API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # โปรดจำกัดโดเมนจริงในโปรดักชัน
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# โหลดโมเดล/encoder
try:
    print(f"[INFO] Loading model from: {MODEL_PATH}")
    print(f"[INFO] Loading label encoder from: {LE_PATH}")
    inference_model = joblib.load(MODEL_PATH)
    le = joblib.load(LE_PATH)
except Exception as e:
    raise RuntimeError(f"โหลดโมเดลไม่สำเร็จ: {e}")

# พยายามดึงคอลัมน์ input ที่พรีโพรเซสเซอร์คาดหวัง (คือ X.columns ตอนฝึก)
prep = getattr(inference_model, "named_steps", {}).get("prep", None)
expected_cols = list(getattr(prep, "feature_names_in_", [])) if prep is not None else []

# แยกคอลัมน์ตามชนิดจาก ColumnTransformer (cat/num)
cat_cols, num_cols = [], []
if prep is not None and getattr(prep, "transformers", None):
    # transformers = [("cat", ohe/pipe, [cat_cols]), ("num", scaler/pipe, [num_cols])]
    for name, trans, cols in prep.transformers:
        if name == "cat":
            cat_cols = list(cols)
        elif name == "num":
            num_cols = list(cols)

class PredictOneIn(BaseModel):
    data: dict

@app.get("/schema")
def schema():
    """เช็คคอลัมน์ที่ API/โมเดลคาดหวัง และ class labels"""
    return {"expected_columns": expected_cols, "cat_cols": cat_cols, "num_cols": num_cols, "classes": list(le.classes_)}

@app.post("/predict-one")
def predict_one(payload: PredictOneIn):
    try:
        d = payload.data or {}

        # ---- ตรวจสอบฟิลด์บังคับ ----
        required = ["gender", "age", "height_cm", "weight_kg"]
        missing = [k for k in required if not d.get(k)]
        if missing:
            raise HTTPException(status_code=422, detail=f"missing required fields: {', '.join(missing)}")

        # คำนวณ BMI ถ้าไม่ส่งมา
        if (d.get("bmi") is None) and d.get("height_cm") and d.get("weight_kg"):
            h = float(d["height_cm"]) / 100.0
            w = float(d["weight_kg"])
            d["bmi"] = round(w / (h*h), 2)

        # --- สร้าง DataFrame ตามคอลัมน์คาดหวังเหมือนเดิม ---
        if expected_cols:
            df = pd.DataFrame([d]).reindex(columns=expected_cols)
        else:
            df = pd.DataFrame([d])

        # (จะยังคง fill ค่าว่างเฉพาะฟิลด์ "ไม่บังคับ")
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if num_cols:
            df[num_cols] = df[num_cols].fillna(0)

        for c in cat_cols:
            if c in df.columns:
                df[c] = df[c].astype(str)
        if cat_cols:
            df[cat_cols] = df[cat_cols].fillna("")

        # ---- ทำนาย ----
        pred_num = inference_model.predict(df)[0]
        label = le.inverse_transform([pred_num])[0]
        proba = inference_model.predict_proba(df)[0]
        probs = {cls: float(p) for cls, p in zip(le.classes_, proba)}
        return {"prediction": label, "probabilities": probs}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

