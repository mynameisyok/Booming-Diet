# === diet_api.py ===
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, EmailStr
import joblib, pandas as pd, io, csv, uuid, time
from typing import Dict, Any, List, Optional
from pathlib import Path

# ------------------------------- Paths / storage
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "Front end"   # <<< ชื่อโฟลเดอร์ต้องตรงนี้
USERS_CSV = BASE_DIR / "users.csv"
SESSIONS_CSV = BASE_DIR / "sessions.csv"

# ------------------------------- Load model + label encoder
model = joblib.load(BASE_DIR / "diet_recommendation_rf_model.joblib")
label_encoder = joblib.load(BASE_DIR / "label_encoder.joblib")

# ------------------------------- App
app = FastAPI(title="Booming Diet API", version="1.0")

# กัน Failed to fetch (Private Network Access)
@app.middleware("http")
async def add_pna_header(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# ------------------------------- CSV utils
USER_FIELDS = [
    "phone", "firstName", "lastName", "email", "address",
    "dob_day", "dob_month", "dob_year", "agree", "marketingOptIn", "createdAt"
]
SESSION_FIELDS = ["token", "phone", "createdAt"]

def ensure_csv(path: Path, headers: List[str]):
    if not path.exists():
        path.write_text(",".join(headers) + "\n", encoding="utf-8")

def read_user_by_phone(phone: str) -> Optional[Dict[str, str]]:
    if not USERS_CSV.exists(): return None
    with USERS_CSV.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("phone") == phone:
                return row
    return None

def write_user(row: Dict[str, Any]):
    ensure_csv(USERS_CSV, USER_FIELDS)
    with USERS_CSV.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=USER_FIELDS).writerow(row)

def create_session(phone: str) -> str:
    ensure_csv(SESSIONS_CSV, SESSION_FIELDS)
    token = uuid.uuid4().hex
    with SESSIONS_CSV.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=SESSION_FIELDS).writerow(
            {"token": token, "phone": phone, "createdAt": int(time.time())}
        )
    return token

def get_phone_from_token(token: str) -> Optional[str]:
    if not SESSIONS_CSV.exists(): return None
    with SESSIONS_CSV.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("token") == token:
                return row.get("phone")
    return None

# ------------------------------- Schemas
class LoginBody(BaseModel):
    phone: str = Field(..., min_length=6)

class DOB(BaseModel):
    day: str; month: str; year: str

class RegisterBody(BaseModel):
    firstName: str; lastName: str; phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    dob: DOB
    agree: bool
    marketingOptIn: bool

class Record(BaseModel):
    data: Dict[str, Any]

class Records(BaseModel):
    records: List[Dict[str, Any]]

# ------------------------------- API (prefix /api/*)
@app.get("/api/health")
def health():
    return {"status": "ok", "classes": list(label_encoder.classes_), "n_classes": len(label_encoder.classes_)}

@app.post("/api/register")
def api_register(payload: RegisterBody):
    if not payload.agree:
        raise HTTPException(status_code=400, detail="You must accept Terms & Privacy.")
    if read_user_by_phone(payload.phone):
        raise HTTPException(status_code=409, detail="Phone already registered.")
    write_user({
        "phone": payload.phone,
        "firstName": payload.firstName,
        "lastName": payload.lastName,
        "email": payload.email or "",
        "address": payload.address or "",
        "dob_day": payload.dob.day, "dob_month": payload.dob.month, "dob_year": payload.dob.year,
        "agree": str(payload.agree).lower(),
        "marketingOptIn": str(payload.marketingOptIn).lower(),
        "createdAt": int(time.time()),
    })
    return {"success": True, "message": "registered"}

@app.post("/api/login")
def api_login(payload: LoginBody):
    user = read_user_by_phone(payload.phone)
    if not user:
        raise HTTPException(status_code=401, detail="Phone not registered.")
    token = create_session(payload.phone)
    return {"token": token}

def _auth(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token.")
    token = authorization.split(" ", 1)[1].strip()
    phone = get_phone_from_token(token)
    if not phone: raise HTTPException(status_code=401, detail="Invalid token.")
    return phone

@app.get("/api/profile")
def api_profile(phone: str = Depends(_auth)):
    user = read_user_by_phone(phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "phone": user["phone"],
        "firstName": user["firstName"],
        "lastName": user["lastName"],
        "email": user.get("email") or None,
        "address": user.get("address") or None,
        "dob": {"day": user.get("dob_day"), "month": user.get("dob_month"), "year": user.get("dob_year")},
    }

@app.post("/api/predict-one")
def predict_one(record: Record):
    df = pd.DataFrame([record.data])
    pred_num = model.predict(df)[0]
    pred_lbl = label_encoder.inverse_transform([pred_num])[0]
    proba = model.predict_proba(df)[0]
    return {"prediction": pred_lbl,
            "probabilities": {str(c): float(proba[i]) for i, c in enumerate(label_encoder.classes_)}}

@app.post("/api/predict")
def predict_many(records: Records):
    df = pd.DataFrame(records.records)
    pred_num = model.predict(df)
    pred_lbl = label_encoder.inverse_transform(pred_num)
    proba = model.predict_proba(df)
    results = []
    for i in range(len(df)):
        results.append({"prediction": pred_lbl[i],
                        "probabilities": {str(c): float(proba[i, j]) for j, c in enumerate(label_encoder.classes_)}})
    return {"count": len(results), "results": results}

@app.post("/api/predict-csv")
def predict_csv(file: UploadFile = File(...)):
    content = file.file.read()
    df = pd.read_csv(io.BytesIO(content))
    pred_num = model.predict(df)
    pred_lbl = label_encoder.inverse_transform(pred_num)
    proba = model.predict_proba(df)
    results = []
    for i in range(len(df)):
        results.append({"prediction": pred_lbl[i],
                        "probabilities": {str(c): float(proba[i, j]) for j, c in enumerate(label_encoder.classes_)}})
    return {"count": len(results), "results": results}

# ------------------------------- Serve Frontend
# เสิร์ฟไฟล์ static ถ้ามี (รูป/JS/CSS) เรียกด้วย /static/...
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# เสิร์ฟหน้าแรก "/"
@app.get("/", response_class=HTMLResponse)
def root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return HTMLResponse(f"<h3>ไม่พบ index.html</h3><p>คาดว่าอยู่ที่: {index_path}</p>", status_code=404)

# กัน 404 ของ favicon
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)
