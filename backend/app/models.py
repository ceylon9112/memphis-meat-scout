from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# ─── Vendor ───────────────────────────────────────────────────────────────────

class VendorBase(BaseModel):
    name: str
    city: str
    state: Literal["TN", "MS"]
    type: Literal["chain", "independent", "specialty", "wholesale"]
    active: bool = True


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[Literal["TN", "MS"]] = None
    type: Optional[Literal["chain", "independent", "specialty", "wholesale"]] = None
    active: Optional[bool] = None


class VendorResponse(VendorBase):
    id: str
    created_at: datetime


# ─── Meat Cut ─────────────────────────────────────────────────────────────────

class MeatCutBase(BaseModel):
    name: str
    category: Literal["beef", "pork", "poultry", "seafood", "other"]
    active: bool = True


class MeatCutCreate(MeatCutBase):
    pass


class MeatCutUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[Literal["beef", "pork", "poultry", "seafood", "other"]] = None
    active: Optional[bool] = None


class MeatCutResponse(MeatCutBase):
    id: str
    created_at: datetime


# ─── Deal ─────────────────────────────────────────────────────────────────────

class DealBase(BaseModel):
    vendor_id: str
    cut_id: str
    price: float
    price_unit: Literal["per_lb", "per_unit", "per_pack"]
    verified_date: str        # YYYY-MM-DD
    sale_end_date: Optional[str] = None   # YYYY-MM-DD
    notes: Optional[str] = None
    active: bool = True


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    vendor_id: Optional[str] = None
    cut_id: Optional[str] = None
    price: Optional[float] = None
    price_unit: Optional[Literal["per_lb", "per_unit", "per_pack"]] = None
    verified_date: Optional[str] = None
    sale_end_date: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class DealResponse(DealBase):
    id: str
    vendor_name: str
    cut_name: str
    category: str
    created_at: datetime
    updated_at: datetime


# ─── Admin Auth ───────────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
