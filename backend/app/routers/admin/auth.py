from fastapi import APIRouter, HTTPException, status
from ...database import get_db
from ...models import AdminLoginRequest, Token
from ...services.auth import verify_password, create_access_token

router = APIRouter()


@router.post("/auth/login", response_model=Token)
async def login(body: AdminLoginRequest):
    db = get_db()
    user = await db.admin_users.find_one({"username": body.username})
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(body.username)
    return {"access_token": token, "token_type": "bearer"}
