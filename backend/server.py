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
    cursor = db.folders.find({}, {"_id": 0}).sort("created_at", -1)
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
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
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
    if user.get("role") != "admin" and d.get("uploaded_by") != user["id"]:
        raise HTTPException(status_code=403, detail="Seul l'auteur ou l'administrateur peut supprimer")
    await db.documents.update_one({"id": doc_id}, {"$set": {"is_deleted": True, "deleted_at": now_iso()}})
    await log_activity(user["id"], user["name"], "document_deleted", f"Document supprimé: {d['title']}", "document", doc_id)
    return {"message": "Document supprimé"}


@api.post("/documents/{doc_id}/archive")
async def archive_document(doc_id: str, user: dict = Depends(current_user_dep)):
    d = await db.documents.find_one({"id": doc_id, "is_deleted": False})
    if not d:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
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
    if not _has_access(d, user):
        raise HTTPException(status_code=403, detail="Accès refusé")
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
    if user.get("role") != "admin" and d.get("uploaded_by") != user["id"]:
        raise HTTPException(status_code=403, detail="Seul l'auteur ou l'admin peut partager")
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
            link=f"/documents",
            actor_name=user.get("name", ""),
        )
    await log_activity(user["id"], user["name"], "document_shared", f"Document partagé: {d['title']}", "document", doc_id)
    return {"message": "Document partagé", "shared_with": body.user_ids}


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
