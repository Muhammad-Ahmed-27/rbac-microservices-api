from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, os

app = FastAPI(title="Product Service")
security = HTTPBearer()
SECRET = os.getenv("JWT_SECRET", "supersecretkey123")

products = [
    {"id": 1, "name": "Laptop", "price": 1200},
    {"id": 2, "name": "Mouse", "price": 25},
]

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(roles: list):
    def checker(payload=Depends(verify_token)):
        if payload["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Access denied for role {payload['role']}")
        return payload
    return checker

@app.get("/products")
def list_products(user=Depends(verify_token)):
    return {"products": products, "accessed_by": user["sub"], "role": user["role"]}

@app.post("/products")
def create_product(name: str, price: float, user=Depends(require_role(["ADMIN", "MANAGER"]))):
    new_id = len(products)+1
    products.append({"id": new_id, "name": name, "price": price})
    return {"message": "Product created", "product": products[-1]}

@app.delete("/products/{pid}")
def delete_product(pid: int, user=Depends(require_role(["ADMIN"]))):
    global products
    products = [p for p in products if p["id"] != pid]
    return {"message": f"Product {pid} deleted by ADMIN {user['sub']}"}

@app.get("/health")
def health():
    return {"status": "product-service OK"}
