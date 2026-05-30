"""MHCGED - Gestion Electronique des Documents (GED).

Backend principal: FastAPI + MongoDB + Emergent Object Storage.
"""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from bson import ObjectId
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
import io
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_current_user,
    require_admin,
)
import storage
import reports as reports_mod

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# MongoDB
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="MHCGED API")
api = APIRouter(prefix="/api")

# Constants
ARCHIVE_AFTER_YEARS = 5


# ===================== Models =====================
class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    is_active: bool
    created_at: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "agent"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None


class FolderOut(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    created_at: str


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[str] = None


class DocumentOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    original_filename: str
    content_type: str
    size: int
    folder_id: Optional[str]
    folder_name: Optional[str] = None
    tags: List[str] = []
    uploaded_by: str
    uploaded_by_name: Optional[str] = None
    is_archived: bool
    archived_at: Optional[str] = None
    created_at: str


class ShareIn(BaseModel):
    user_ids: List[str]


class PasswordResetIn(BaseModel):
    new_password: str


class MessageCreate(BaseModel):
    to_user_id: str
    content: str
    attachment_doc_id: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    expires_at: Optional[str] = None  # ISO date string


# ===================== Helpers =====================
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def user_public(u: dict) -> dict:
    return {
        "id": str(u.get("_id", u.get("id"))),
        "email": u["email"],
        "name": u.get("name", ""),
        "role": u.get("role", "agent"),
        "is_active": u.get("is_active", True),
        "created_at": u.get("created_at", now_iso()),
    }


async def log_activity(user_id: str, user_name: str, action: str, details: str = "", target_type: str = "", target_id: str = ""):
    await db.activity_logs.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "details": details,
        "target_type": target_type,
        "target_id": target_id,
        "timestamp": now_iso(),
    })


async def create_notification(user_id: str, title: str, message: str, link: str = "", actor_name: str = ""):
    """Create an in-app notification for a user."""
    if not user_id:
        return
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "link": link,
        "actor_name": actor_name,
        "is_read": False,
        "created_at": now_iso(),
    })


async def current_user_dep(request: Request) -> dict:
    return await get_current_user(request, db)


# ===================== Auth =====================
@api.post("/auth/login")
async def login(payload: LoginIn, response: Response):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Compte désactivé")
    user_id = str(user["_id"])
    access = create_access_token(user_id, user["email"], user.get("role", "agent"))
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    await log_activity(user_id, user.get("name", email), "login", "Connexion réussie")
    return user_public(user)


@api.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(current_user_dep)):
    clear_auth_cookies(response)
    await log_activity(user["id"], user.get("name", ""), "logout", "Déconnexion")
    return {"message": "Déconnecté"}


@api.get("/auth/me")
async def me(user: dict = Depends(current_user_dep)):
    return user


# ===================== Users (Admin) =====================
@api.get("/users", response_model=List[UserOut])
async def list_users(user: dict = Depends(current_user_dep)):
    require_admin(user)
    cursor = db.users.find({}).sort("created_at", -1)
    out = []
    async for u in cursor:
        out.append(user_public(u))
    return out


@api.post("/users", response_model=UserOut)
async def create_user(body: UserCreate, user: dict = Depends(current_user_dep)):
    require_admin(user)
    email = body.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    if body.role not in ("admin", "agent"):
        raise HTTPException(status_code=400, detail="Rôle invalide")
    doc = {
        "email": email,
        "password_hash": hash_password(body.password),
        "name": body.name,
        "role": body.role,
        "is_active": True,
        "created_at": now_iso(),
    }
    res = await db.users.insert_one(doc)
    doc["_id"] = res.inserted_id
    await log_activity(user["id"], user["name"], "user_created", f"Agent créé: {email}", "user", str(res.inserted_id))
    return user_public(doc)


@api.put("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, body: UserUpdate, user: dict = Depends(current_user_dep)):
    require_admin(user)
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    existing = await db.users.find_one({"_id": oid})
    if not existing:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.role is not None:
        if body.role not in ("admin", "agent"):
            raise HTTPException(status_code=400, detail="Rôle invalide")
        updates["role"] = body.role
    if body.password:
        updates["password_hash"] = hash_password(body.password)
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if updates:
        await db.users.update_one({"_id": oid}, {"$set": updates})
    u = await db.users.find_one({"_id": oid})
    await log_activity(user["id"], user["name"], "user_updated", f"Agent modifié: {u['email']}", "user", user_id)
    return user_public(u)


@api.delete("/users/{user_id}")
async def delete_user(user_id: str, user: dict = Depends(current_user_dep)):
    require_admin(user)
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous supprimer")
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    u = await db.users.find_one({"_id": oid})
    if not u:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    await db.users.delete_one({"_id": oid})
    await log_activity(user["id"], user["name"], "user_deleted", f"Agent supprimé: {u['email']}", "user", user_id)
    return {"message": "Agent supprimé"}


# ===================== Folders =====================
@api.get("/folders", response_model=List[FolderOut])
async def list_folders(user: dict = Depends(current_user_dep)):
    # Agents see only their own folders; admin sees everything
    q = {} if user.get("role") == "admin" else {"created_by": user["id"]}
    cursor = db.folders.find(q, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(length=1000)


@api.post("/folders", response_model=FolderOut)
async def create_folder(body: FolderCreate, user: dict = Depends(current_user_dep)):
    if body.parent_id:
        parent = await db.folders.find_one({"id": body.parent_id})
        if not parent:
            raise HTTPException(status_code=400, detail="Dossier parent invalide")
    doc = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "parent_id": body.parent_id,
        "description": body.description,
        "created_by": user["id"],
        "created_by_name": user.get("name", ""),
        "created_at": now_iso(),
    }
    await db.folders.insert_one(doc)
    await log_activity(user["id"], user["name"], "folder_created", f"Dossier créé: {body.name}", "folder", doc["id"])
    doc.pop("_id", None)
    return doc


@api.put("/folders/{folder_id}", response_model=FolderOut)
async def update_folder(folder_id: str, body: FolderUpdate, user: dict = Depends(current_user_dep)):
    folder = await db.folders.find_one({"id": folder_id})
    if not folder:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    if not _can_modify_folder(folder, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut modifier un dossier")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if updates:
        await db.folders.update_one({"id": folder_id}, {"$set": updates})
    folder = await db.folders.find_one({"id": folder_id}, {"_id": 0})
    await log_activity(user["id"], user["name"], "folder_updated", f"Dossier modifié: {folder['name']}", "folder", folder_id)
    return folder


@api.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, user: dict = Depends(current_user_dep)):
    folder = await db.folders.find_one({"id": folder_id})
    if not folder:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    if not _can_modify_folder(folder, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut supprimer un dossier")
    # Detach documents from the folder rather than deleting them
    await db.documents.update_many({"folder_id": folder_id}, {"$set": {"folder_id": None}})
    await db.folders.delete_one({"id": folder_id})
    await log_activity(user["id"], user["name"], "folder_deleted", f"Dossier supprimé: {folder['name']}", "folder", folder_id)
    return {"message": "Dossier supprimé"}


# ===================== Documents =====================
async def _enrich_doc(d: dict) -> dict:
    d.pop("_id", None)
    d.pop("storage_path", None)
    if d.get("folder_id"):
        folder = await db.folders.find_one({"id": d["folder_id"]}, {"_id": 0, "name": 1})
        d["folder_name"] = folder["name"] if folder else None
    else:
        d["folder_name"] = None
    return d


def _has_access(doc: dict, user: dict) -> bool:
    if user.get("role") == "admin":
        return True
    if doc.get("uploaded_by") == user["id"]:
        return True
    if user["id"] in doc.get("shared_with", []):
        return True
    return False


def _can_modify_doc(doc: dict, user: dict) -> bool:
    """Only admins can modify/delete/share/archive documents."""
    return user.get("role") == "admin"


def _can_modify_folder(folder: dict, user: dict) -> bool:
    """Only admins can modify/delete folders."""
    return user.get("role") == "admin"


@api.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    folder_id: Optional[str] = Form(None),
    tags: str = Form(""),  # comma-separated
    user: dict = Depends(current_user_dep),
):
    data = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    storage_path = f"{os.environ.get('APP_NAME', 'mhcged')}/documents/{user['id']}/{uuid.uuid4()}.{ext}"
    content_type = file.content_type or "application/octet-stream"
    try:
        result = storage.put_object(storage_path, data, content_type)
    except Exception as e:
        logger.exception("Upload storage error")
        raise HTTPException(status_code=500, detail=f"Erreur stockage: {e}")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    doc = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "original_filename": file.filename,
        "content_type": content_type,
        "size": result.get("size", len(data)),
        "storage_path": result["path"],
        "folder_id": folder_id or None,
        "tags": tag_list,
        "uploaded_by": user["id"],
        "uploaded_by_name": user.get("name", ""),
        "shared_with": [],
        "is_archived": False,
        "archived_at": None,
        "is_deleted": False,
        "created_at": now_iso(),
    }
    await db.documents.insert_one(doc)
    await log_activity(user["id"], user["name"], "document_uploaded", f"Document téléversé: {title}", "document", doc["id"])
    return await _enrich_doc(dict(doc))


@api.get("/documents")
async def list_documents(
    archived: Optional[bool] = Query(None),
    folder_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    user: dict = Depends(current_user_dep),
):
    q: dict = {"is_deleted": False}
    if archived is not None:
        q["is_archived"] = archived
    if folder_id:
        q["folder_id"] = folder_id
    if tag:
        q["tags"] = tag
    if search:
        q["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"original_filename": {"$regex": search, "$options": "i"}},
        ]
    # Role-based filter: agents see only their own + shared
    if user.get("role") != "admin":
        q["$and"] = q.get("$and", []) + [{"$or": [
            {"uploaded_by": user["id"]},
            {"shared_with": user["id"]},
        ]}]
    cursor = db.documents.find(q).sort("created_at", -1)
    out = []
    async for d in cursor:
        out.append(await _enrich_doc(d))
    return out


@api.get("/documents/{doc_id}")
async def get_document(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return await _enrich_doc(d)


@api.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
    try:
        data, ct = storage.get_object(d["storage_path"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur téléchargement: {e}")
    await log_activity(user["id"], user["name"], "document_downloaded", f"Téléchargement: {d['title']}", "document", doc_id)
    return StreamingResponse(
        io.BytesIO(data),
        media_type=d.get("content_type") or ct,
        headers={"Content-Disposition": f'attachment; filename="{d["original_filename"]}"'},
    )


@api.put("/documents/{doc_id}")
async def update_document(doc_id: str, body: DocumentUpdate, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _can_modify_doc(d, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut modifier un document")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if updates:
        await db.documents.update_one({"id": doc_id}, {"$set": updates})
    d = await db.documents.find_one({"id": doc_id})
    await log_activity(user["id"], user["name"], "document_updated", f"Document modifié: {d['title']}", "document", doc_id)
    return await _enrich_doc(d)


@api.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _can_modify_doc(d, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut supprimer un document")
    await db.documents.update_one({"id": doc_id}, {"$set": {"is_deleted": True, "deleted_at": now_iso()}})
    await log_activity(user["id"], user["name"], "document_deleted", f"Document supprimé: {d['title']}", "document", doc_id)
    return {"message": "Document supprimé"}


@api.post("/documents/{doc_id}/archive")
async def archive_document(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _can_modify_doc(d, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut archiver un document")
    await db.documents.update_one(
        {"id": doc_id},
        {"$set": {"is_archived": True, "archived_at": now_iso()}},
    )
    await log_activity(user["id"], user["name"], "document_archived", f"Document archivé: {d['title']}", "document", doc_id)
    return {"message": "Document archivé"}


@api.post("/documents/{doc_id}/unarchive")
async def unarchive_document(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _can_modify_doc(d, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut désarchiver un document")
    await db.documents.update_one(
        {"id": doc_id},
        {"$set": {"is_archived": False, "archived_at": None}},
    )
    await log_activity(user["id"], user["name"], "document_unarchived", f"Document désarchivé: {d['title']}", "document", doc_id)
    return {"message": "Document désarchivé"}


@api.post("/documents/{doc_id}/share")
async def share_document(doc_id: str, body: ShareIn, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _can_modify_doc(d, user):
        raise HTTPException(status_code=403, detail="Seul l'administrateur peut partager un document")
    prev = set(d.get("shared_with", []))
    new_ids = set(body.user_ids)
    added = new_ids - prev
    await db.documents.update_many({"id": doc_id}, {"$set": {"shared_with": body.user_ids}})
    # Notify newly added users
    for uid in added:
        await create_notification(
            user_id=uid,
            title="Document partagé avec vous",
            message=f"{user.get('name', 'Un agent')} vous a partagé « {d['title']} »",
            link="/inbox",
            actor_name=user.get("name", ""),
        )
    await log_activity(user["id"], user["name"], "document_shared", f"Document partagé: {d['title']}", "document", doc_id)
    return {"message": "Document partagé", "shared_with": body.user_ids}


    await log_activity(user["id"], user["name"], "document_shared", f"Document partagé: {d['title']}", "document", doc_id)
    return {"message": "Document partagé", "shared_with": body.user_ids}


# ===================== Settings (logo / hero image) =====================
DEFAULT_LOGO_URL = "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/dmk2iip2_Photo%201.jpeg"
DEFAULT_HERO_URL = "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/15pprz55_Photo%202.jpeg"


async def _get_settings_doc() -> dict:
    doc = await db.settings.find_one({"_id": "app"})
    if not doc:
        return {"logo_url": DEFAULT_LOGO_URL, "hero_url": DEFAULT_HERO_URL}
    return {
        "logo_url": doc.get("logo_url") or DEFAULT_LOGO_URL,
        "hero_url": doc.get("hero_url") or DEFAULT_HERO_URL,
    }


@api.get("/settings")
async def get_settings():
    """Public endpoint so the login screen can fetch the logo + hero."""
    return await _get_settings_doc()


@api.post("/settings/logo")
async def update_logo(file: UploadFile = File(...), user: dict = Depends(current_user_dep)):
    require_admin(user)
    data = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "png"
    path = f"{os.environ.get('APP_NAME', 'mhcged')}/settings/logo-{uuid.uuid4()}.{ext}"
    content_type = file.content_type or "image/png"
    try:
        result = storage.put_object(path, data, content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {e}")
    public_url = f"/api/settings/file/{result['path']}"
    await db.settings.update_one(
        {"_id": "app"},
        {"$set": {"logo_url": public_url, "logo_path": result["path"], "updated_at": now_iso()}},
        upsert=True,
    )
    await log_activity(user["id"], user["name"], "logo_updated", "Logo mis à jour", "settings", "logo")
    return await _get_settings_doc()


@api.post("/settings/hero")
async def update_hero(file: UploadFile = File(...), user: dict = Depends(current_user_dep)):
    require_admin(user)
    data = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "png"
    path = f"{os.environ.get('APP_NAME', 'mhcged')}/settings/hero-{uuid.uuid4()}.{ext}"
    content_type = file.content_type or "image/png"
    try:
        result = storage.put_object(path, data, content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {e}")
    public_url = f"/api/settings/file/{result['path']}"
    await db.settings.update_one(
        {"_id": "app"},
        {"$set": {"hero_url": public_url, "hero_path": result["path"], "updated_at": now_iso()}},
        upsert=True,
    )
    await log_activity(user["id"], user["name"], "hero_updated", "Image d'accueil mise à jour", "settings", "hero")
    return await _get_settings_doc()


@api.get("/settings/file/{path:path}")
async def settings_file(path: str):
    """Serve the uploaded logo/hero images publicly (no auth required for login screen)."""
    try:
        data, ct = storage.get_object(path)
    except Exception:
        raise HTTPException(status_code=404, detail="Image introuvable")
    return Response(content=data, media_type=ct)


# ===================== Tags =====================
@api.get("/tags")
async def list_tags(user: dict = Depends(current_user_dep)):
    tags = await db.documents.distinct("tags", {"is_deleted": False})
    return sorted([t for t in tags if t])


# ===================== Dashboard =====================
@api.get("/dashboard/stats")
async def dashboard_stats(user: dict = Depends(current_user_dep)):
    base = {"is_deleted": False}
    if user.get("role") != "admin":
        base["$or"] = [{"uploaded_by": user["id"]}, {"shared_with": user["id"]}]
    total_docs = await db.documents.count_documents({**base, "is_archived": False})
    total_archived = await db.documents.count_documents({**base, "is_archived": True})
    total_folders = await db.folders.count_documents({})
    total_agents = await db.users.count_documents({}) if user.get("role") == "admin" else 0

    # Recent documents
    recents_cursor = db.documents.find(base).sort("created_at", -1).limit(5)
    recents = []
    async for d in recents_cursor:
        recents.append(await _enrich_doc(d))

    # Storage size
    pipeline = [
        {"$match": base},
        {"$group": {"_id": None, "total": {"$sum": "$size"}}},
    ]
    size_doc = await db.documents.aggregate(pipeline).to_list(1)
    total_size = size_doc[0]["total"] if size_doc else 0

    return {
        "total_documents": total_docs,
        "total_archived": total_archived,
        "total_folders": total_folders,
        "total_agents": total_agents,
        "total_size": total_size,
        "recent_documents": recents,
    }


# ===================== Activity =====================
@api.get("/activity")
async def list_activity(limit: int = 100, user: dict = Depends(current_user_dep)):
    q = {} if user.get("role") == "admin" else {"user_id": user["id"]}
    cursor = db.activity_logs.find(q, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ===================== Notifications =====================
@api.get("/notifications")
async def list_notifications(limit: int = 30, user: dict = Depends(current_user_dep)):
    cursor = db.notifications.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    unread = await db.notifications.count_documents({"user_id": user["id"], "is_read": False})
    return {"items": items, "unread_count": unread}


@api.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user: dict = Depends(current_user_dep)):
    await db.notifications.update_one(
        {"id": notif_id, "user_id": user["id"]},
        {"$set": {"is_read": True}},
    )
    return {"message": "ok"}


@api.post("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(current_user_dep)):
    await db.notifications.update_many(
        {"user_id": user["id"], "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"message": "ok"}


# ===================== Admin password reset =====================
@api.post("/users/{user_id}/reset-password")
async def admin_reset_password(user_id: str, body: PasswordResetIn, user: dict = Depends(current_user_dep)):
    require_admin(user)
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mot de passe trop court (min 6 caractères)")
    await db.users.update_one({"_id": oid}, {"$set": {"password_hash": hash_password(body.new_password)}})
    await log_activity(user["id"], user["name"], "password_reset", f"Mot de passe réinitialisé pour: {target['email']}", "user", user_id)
    await create_notification(
        user_id=str(oid),
        title="Mot de passe réinitialisé",
        message=f"Votre mot de passe a été réinitialisé par {user.get('name', 'un administrateur')}.",
        link="/profile",
        actor_name=user.get("name", ""),
    )
    return {"message": "Mot de passe réinitialisé"}


# ===================== Reports =====================
async def _build_report_data(year: int, month: int, agent_id: Optional[str]):
    """Compute top documents and top agents for the given month + optional agent filter."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mois invalide")
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    start_iso = start.isoformat()
    end_iso = end.isoformat()

    # Activity logs filter for the month
    activity_match = {"timestamp": {"$gte": start_iso, "$lt": end_iso}}
    if agent_id:
        activity_match["user_id"] = agent_id

    # Top documents (most downloaded)
    download_match = {**activity_match, "action": "document_downloaded", "target_id": {"$ne": ""}}
    top_docs_raw = await db.activity_logs.aggregate([
        {"$match": download_match},
        {"$group": {"_id": "$target_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]).to_list(length=5)

    top_docs = []
    for entry in top_docs_raw:
        d = await db.documents.find_one({"id": entry["_id"]}, {"_id": 0, "title": 1})
        title = d["title"] if d else f"Document {entry['_id'][:8]}"
        top_docs.append({"id": entry["_id"], "title": title, "count": entry["count"]})

    # Top agents (most actions) - only meaningful when looking at all agents
    top_agents_raw = await db.activity_logs.aggregate([
        {"$match": activity_match},
        {"$group": {"_id": "$user_id", "name": {"$first": "$user_name"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]).to_list(length=5)
    top_agents = [
        {"id": a["_id"], "name": a.get("name") or "—", "count": a["count"]}
        for a in top_agents_raw
    ]

    # Scope label for header
    if agent_id:
        agent_doc = None
        try:
            agent_doc = await db.users.find_one({"_id": ObjectId(agent_id)}, {"_id": 0, "name": 1, "email": 1})
        except Exception:
            agent_doc = None
        scope_label = f"Agent : {agent_doc['name'] if agent_doc else agent_id}"
    else:
        scope_label = "Tous les agents"

    return {
        "top_docs": top_docs,
        "top_agents": top_agents,
        "scope_label": scope_label,
    }


@api.get("/reports/monthly")
async def report_monthly_preview(
    year: int = Query(..., ge=2000, le=3000),
    month: int = Query(..., ge=1, le=12),
    agent_id: Optional[str] = Query(None),
    user: dict = Depends(current_user_dep),
):
    """Return the report data as JSON (preview before PDF download)."""
    require_admin(user)
    data = await _build_report_data(year, month, agent_id)
    return data


@api.get("/reports/monthly/pdf")
async def report_monthly_pdf(
    year: int = Query(..., ge=2000, le=3000),
    month: int = Query(..., ge=1, le=12),
    agent_id: Optional[str] = Query(None),
    user: dict = Depends(current_user_dep),
):
    """Generate and stream the monthly PDF report."""
    require_admin(user)
    data = await _build_report_data(year, month, agent_id)
    pdf_bytes = reports_mod.build_monthly_report_pdf(
        year=year,
        month=month,
        scope_label=data["scope_label"],
        top_docs=data["top_docs"],
        top_agents=data["top_agents"],
        signed_by_name=user.get("name") or "Administrateur",
        signed_by_role="Administrateur · MHCGED",
    )
    await log_activity(
        user["id"], user.get("name", ""),
        "report_generated",
        f"Rapport mensuel généré: {month:02d}/{year}" + (f" (agent {agent_id})" if agent_id else ""),
        "report",
        f"{year}-{month:02d}",
    )
    filename = f"rapport-mhcged-{year}-{month:02d}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ===================== Messages =====================
async def _user_lite(uid: str) -> dict:
    try:
        u = await db.users.find_one({"_id": ObjectId(uid)}, {"_id": 0, "name": 1, "email": 1, "role": 1})
    except Exception:
        u = None
    return {
        "id": uid,
        "name": (u or {}).get("name", "Utilisateur"),
        "email": (u or {}).get("email", ""),
        "role": (u or {}).get("role", "agent"),
    }


@api.post("/messages")
async def send_message(body: MessageCreate, user: dict = Depends(current_user_dep)):
    if not body.content.strip() and not body.attachment_doc_id:
        raise HTTPException(status_code=400, detail="Message vide")
    try:
        ObjectId(body.to_user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Destinataire invalide")
    target = await db.users.find_one({"_id": ObjectId(body.to_user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="Destinataire introuvable")
    if body.to_user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous envoyer un message")

    attachment = None
    if body.attachment_doc_id:
        d = await db.documents.find_one(
            {"id": body.attachment_doc_id, "is_deleted": False},
            {"_id": 0, "id": 1, "title": 1, "original_filename": 1},
        )
        if d:
            attachment = d
    msg = {
        "id": str(uuid.uuid4()),
        "from_user_id": user["id"],
        "from_user_name": user.get("name", ""),
        "to_user_id": body.to_user_id,
        "to_user_name": target.get("name", ""),
        "content": body.content,
        "attachment": attachment,
        "is_read": False,
        "created_at": now_iso(),
    }
    await db.messages.insert_one(msg)
    await create_notification(
        user_id=body.to_user_id,
        title="Nouveau message",
        message=f"{user.get('name', 'Un agent')} vous a envoyé un message",
        link="/messages",
        actor_name=user.get("name", ""),
    )
    msg.pop("_id", None)
    return msg


@api.get("/messages/conversations")
async def list_conversations(user: dict = Depends(current_user_dep)):
    """Return list of conversations with last message + unread count for current user."""
    pipeline = [
        {"$match": {"$or": [{"from_user_id": user["id"]}, {"to_user_id": user["id"]}]}},
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$eq": ["$from_user_id", user["id"]]},
                        "$to_user_id",
                        "$from_user_id",
                    ]
                },
                "last_message": {"$first": "$$ROOT"},
                "unread_count": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$to_user_id", user["id"]]},
                                {"$eq": ["$is_read", False]},
                            ]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"last_message.created_at": -1}},
    ]
    raw = await db.messages.aggregate(pipeline).to_list(length=200)
    out = []
    for c in raw:
        peer = await _user_lite(c["_id"])
        last = c["last_message"]
        last.pop("_id", None)
        out.append({
            "peer": peer,
            "last_message": last,
            "unread_count": c["unread_count"],
        })
    return out


@api.get("/messages/conversation/{peer_id}")
async def get_conversation(peer_id: str, user: dict = Depends(current_user_dep)):
    cursor = db.messages.find({
        "$or": [
            {"from_user_id": user["id"], "to_user_id": peer_id},
            {"from_user_id": peer_id, "to_user_id": user["id"]},
        ]
    }, {"_id": 0}).sort("created_at", 1)
    msgs = await cursor.to_list(length=1000)
    # Mark as read everything received
    await db.messages.update_many(
        {"to_user_id": user["id"], "from_user_id": peer_id, "is_read": False},
        {"$set": {"is_read": True}},
    )
    peer = await _user_lite(peer_id)
    return {"peer": peer, "messages": msgs}


@api.get("/messages/unread-count")
async def messages_unread_count(user: dict = Depends(current_user_dep)):
    n = await db.messages.count_documents({"to_user_id": user["id"], "is_read": False})
    return {"unread_count": n}


# ===================== Document comments =====================
@api.get("/documents/{doc_id}/comments")
async def list_comments(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
    cursor = db.comments.find({"doc_id": doc_id}, {"_id": 0}).sort("created_at", 1)
    return await cursor.to_list(length=500)


@api.post("/documents/{doc_id}/comments")
async def add_comment(doc_id: str, body: CommentCreate, user: dict = Depends(current_user_dep)):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Commentaire vide")
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
    c = {
        "id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "user_id": user["id"],
        "user_name": user.get("name", ""),
        "content": body.content,
        "created_at": now_iso(),
    }
    await db.comments.insert_one(c)
    # Notify the document owner if it's not the commenter
    if d.get("uploaded_by") and d["uploaded_by"] != user["id"]:
        await create_notification(
            user_id=d["uploaded_by"],
            title="Nouveau commentaire",
            message=f"{user.get('name', 'Un agent')} a commenté « {d['title']} »",
            link="/documents",
            actor_name=user.get("name", ""),
        )
    c.pop("_id", None)
    return c


@api.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user: dict = Depends(current_user_dep)):
    c = await db.comments.find_one({"id": comment_id})
    if not c:
        raise HTTPException(status_code=404, detail="Commentaire introuvable")
    if user.get("role") != "admin" and c["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    await db.comments.delete_one({"id": comment_id})
    return {"message": "Commentaire supprimé"}


# ===================== Inbox =====================
@api.get("/inbox")
async def list_inbox(user: dict = Depends(current_user_dep)):
    """Documents shared WITH the current user (the inbox)."""
    cursor = db.documents.find({
        "is_deleted": False,
        "shared_with": user["id"],
    }).sort("created_at", -1)
    out = []
    reads = await db.inbox_reads.find({"user_id": user["id"]}, {"_id": 0, "doc_id": 1}).to_list(length=2000)
    read_ids = {r["doc_id"] for r in reads}
    async for d in cursor:
        d = await _enrich_doc(d)
        d["is_read"] = d["id"] in read_ids
        out.append(d)
    unread = sum(1 for x in out if not x["is_read"])
    return {"items": out, "unread_count": unread}


@api.post("/inbox/{doc_id}/read")
async def mark_inbox_read(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d or user["id"] not in d.get("shared_with", []):
        raise HTTPException(status_code=404, detail="Élément introuvable")
    await db.inbox_reads.update_one(
        {"user_id": user["id"], "doc_id": doc_id},
        {"$set": {"user_id": user["id"], "doc_id": doc_id, "read_at": now_iso()}},
        upsert=True,
    )
    return {"message": "ok"}


# ===================== Announcements =====================
@api.get("/announcements")
async def list_announcements(user: dict = Depends(current_user_dep)):
    now_str = now_iso()
    cursor = db.announcements.find({
        "$or": [{"expires_at": None}, {"expires_at": {"$gt": now_str}}]
    }, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(length=100)


@api.post("/announcements")
async def create_announcement(body: AnnouncementCreate, user: dict = Depends(current_user_dep)):
    require_admin(user)
    if not body.title.strip() or not body.content.strip():
        raise HTTPException(status_code=400, detail="Titre et contenu requis")
    a = {
        "id": str(uuid.uuid4()),
        "title": body.title,
        "content": body.content,
        "expires_at": body.expires_at,
        "author_id": user["id"],
        "author_name": user.get("name", ""),
        "created_at": now_iso(),
    }
    await db.announcements.insert_one(a)
    # Notify all active users (except the author)
    cursor = db.users.find({"is_active": True}, {"_id": 1, "name": 1})
    async for u in cursor:
        uid = str(u["_id"])
        if uid == user["id"]:
            continue
        await create_notification(
            user_id=uid,
            title="📢 " + body.title,
            message=body.content[:140] + ("…" if len(body.content) > 140 else ""),
            link="/",
            actor_name=user.get("name", ""),
        )
    await log_activity(user["id"], user.get("name", ""), "announcement_created", f"Annonce: {body.title}", "announcement", a["id"])
    a.pop("_id", None)
    return a


@api.delete("/announcements/{ann_id}")
async def delete_announcement(ann_id: str, user: dict = Depends(current_user_dep)):
    require_admin(user)
    a = await db.announcements.find_one({"id": ann_id})
    if not a:
        raise HTTPException(status_code=404, detail="Annonce introuvable")
    await db.announcements.delete_one({"id": ann_id})
    return {"message": "Annonce supprimée"}


# ===================== Startup =====================
@app.on_event("startup")
async def on_startup():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.folders.create_index("id", unique=True)
    await db.documents.create_index("id", unique=True)
    await db.documents.create_index("created_at")
    await db.activity_logs.create_index("timestamp")

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@mhcged.cg").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@2026")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Administrateur MHCGED",
            "role": "admin",
            "is_active": True,
            "created_at": now_iso(),
        })
        logger.info("Admin par défaut créé: %s", admin_email)
    else:
        if not verify_password(admin_password, existing["password_hash"]):
            await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
            logger.info("Mot de passe admin resynchronisé")

    # Initialize object storage
    try:
        storage.init_storage()
    except Exception as e:
        logger.error("Échec init storage: %s", e)

    # Auto-archive old documents (>= ARCHIVE_AFTER_YEARS)
    threshold = (datetime.now(timezone.utc) - timedelta(days=ARCHIVE_AFTER_YEARS * 365)).isoformat()
    res = await db.documents.update_many(
        {"is_archived": False, "is_deleted": False, "created_at": {"$lte": threshold}},
        {"$set": {"is_archived": True, "archived_at": now_iso()}},
    )
    if res.modified_count:
        logger.info("Auto-archivage: %d documents archivés", res.modified_count)


@app.on_event("shutdown")
async def on_shutdown():
    client.close()


# Mount router + CORS
app.include_router(api)

_origins_raw = os.environ.get("CORS_ORIGINS", "*")
_origins = [o.strip() for o in _origins_raw.split(",")] if _origins_raw else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_origins,
    allow_origin_regex=".*",
    allow_methods=["*"],
    allow_headers=["*"],
)
