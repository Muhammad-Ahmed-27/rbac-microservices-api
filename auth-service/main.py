from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, datetime
from passlib.context import CryptContext
import os

app = FastAPI(title="Auth Service")
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET = os.getenv("JWT_SECRET", "supersecretkey123")

# Fake DB
users_db = {
    "admin@example.com": {"password": pwd_context.hash("admin123"), "role": "ADMIN"},
    "manager@example.com": {"password": pwd_context.hash("manager123"), "role": "MANAGER"},
    "user@example.com": {"password": pwd_context.hash("user123"), "role": "USER"},
}

def create_token(email, role):
    payload = {
        "sub": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(roles: list):
    def checker(payload=Depends(verify_token)):
        if payload["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Role {payload['role']} not authorized. Required: {roles}")
        return payload
    return checker

@app.post("/login")
def login(email: str, password: str):
    user = users_db.get(email)
    if not user or not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(email, user["role"])
    return {"access_token": token, "role": user["role"], "token_type": "Bearer"}

@app.get("/verify")
def verify(payload=Depends(verify_token)):
    return payload

@app.get("/admin-only")
def admin_only(payload=Depends(require_role(["ADMIN"]))):
    return {"message": f"Hello ADMIN {payload['sub']}, secure data accessed"}

@app.get("/manager-or-admin")
def manager_admin(payload=Depends(require_role(["ADMIN", "MANAGER"]))):
    return {"message": f"Hello {payload['role']} {payload['sub']}"}

@app.get("/health")
def health():
    return {"status": "auth-service OK"}
