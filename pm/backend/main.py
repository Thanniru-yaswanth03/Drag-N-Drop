from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any
import os
import secrets
import time

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
import database
import ai
from websocket_manager import ws_manager

from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="Drag N Drop API", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory IP Rate Limiter
LOGIN_ATTEMPTS: Dict[str, List[float]] = {}


def check_rate_limit(client_ip: str) -> bool:
    if client_ip == "testclient" or (os.environ.get("TESTING") == "1" and client_ip in ("127.0.0.1", "localhost", "::1")):
        return True
    now = time.time()
    window = config.RATE_LIMIT_LOGIN_WINDOW_SECONDS
    max_attempts = config.RATE_LIMIT_LOGIN_MAX

    attempts = [t for t in LOGIN_ATTEMPTS.get(client_ip, []) if now - t < window]
    attempts.append(now)
    LOGIN_ATTEMPTS[client_ip] = attempts

    return len(attempts) <= max_attempts



def get_authenticated_user(request: Request) -> str:
    """Derive the authenticated user from a valid session token only.
    Raises HTTP 401 if authentication is missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Session-Token")

    if token:
        sess = database.verify_session_token(token)
        if sess:
            return sess["username"]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def get_optional_authenticated_user(request: Request) -> Optional[str]:
    """Return the authenticated username or None (no exception)."""
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Session-Token")
    if token:
        sess = database.verify_session_token(token)
        if sess:
            return sess["username"]
    return None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
if not STATIC_DIR.exists():
    STATIC_DIR = BASE_DIR.parent / "frontend" / "out"

if STATIC_DIR.exists():
    next_dir = STATIC_DIR / "_next"
    if next_dir.exists():
        app.mount("/_next", StaticFiles(directory=next_dir), name="next_assets")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)


class AddMemberRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    role: str = Field("member", max_length=20)


class CardCreateRequest(BaseModel):
    columnId: str = Field(..., max_length=100)
    cardId: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    details: Optional[str] = Field("", max_length=2000)
    description: Optional[str] = Field("", max_length=2000)
    priority: Optional[str] = Field("medium", max_length=20)
    dueDate: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field([], max_length=20)
    assignee: Optional[str] = Field(None, max_length=50)


class CardMoveRequest(BaseModel):
    columnId: str = Field(..., max_length=100)
    position: Optional[int] = Field(0, ge=0)


class ColumnUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class CardUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    details: Optional[str] = Field(None, max_length=2000)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, max_length=20)
    dueDate: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(None, max_length=20)
    assignee: Optional[str] = Field(None, max_length=50)


class ProjectItem(BaseModel):
    id: str
    name: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ProjectUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ColumnItem(BaseModel):
    id: str = Field(..., max_length=100)
    title: str = Field(..., max_length=100)
    cardIds: List[str] = Field(default_factory=list)


class CardItem(BaseModel):
    id: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    details: Optional[str] = Field("", max_length=2000)
    description: Optional[str] = Field("", max_length=2000)
    priority: Optional[str] = Field("medium", max_length=20)
    dueDate: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field([], max_length=20)
    assignee: Optional[str] = Field(None, max_length=50)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class BoardSaveRequest(BaseModel):
    columns: List[ColumnItem]
    cards: Dict[str, CardItem]


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, max_length=20)
    board: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = Field(None, max_length=100)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "environment": config.ENVIRONMENT,
        "database": database.get_database_diagnostics(),
    }


@app.get("/api/health/db")
@app.get("/api/diagnostics/db")
def database_diagnostics():
    return {
        "status": "ok",
        **database.get_database_diagnostics(),
    }




@app.post("/api/auth/register")
def register(credentials: RegisterRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
    client_ip = client_ip.split(",")[0].strip()
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again in 1 minute.",
        )
    res = database.register_user(credentials.username, credentials.password)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Registration failed"),
        )
    return res


@app.post("/api/auth/login")
def login(credentials: LoginRequest, request: Request):
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
    client_ip = client_ip.split(",")[0].strip()
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again in 1 minute.",
        )
    res = database.authenticate_user(credentials.username, credentials.password)
    if res:
        return res
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
    )


@app.get("/api/auth/me")
def get_me(request: Request):
    auth_user = get_authenticated_user(request)
    return {"user": auth_user, "authenticated": True}


@app.post("/api/auth/logout")
def logout(request: Request):
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Session-Token")
    if token:
        database.revoke_session(token)
    return {"success": True}


# Card CRUD Endpoints
@app.post("/api/cards")
def create_card(payload: CardCreateRequest, request: Request):
    auth_user = get_authenticated_user(request)
    card_id = payload.cardId or f"card-{secrets.token_hex(8)}"
    card = database.add_card(
        user_id=auth_user,
        column_id=payload.columnId,
        card_id=card_id,
        title=payload.title,
        details=payload.details or payload.description or "",
        description=payload.description or payload.details or "",
        priority=payload.priority or "medium",
        due_date=payload.dueDate,
        tags=payload.tags or [],
        assignee=payload.assignee,
    )
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    if isinstance(card, dict) and "error" in card:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=card["error"])
    return {"success": True, "card": card}


@app.put("/api/cards/{card_id}")
def update_card(card_id: str, payload: CardUpdateRequest, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.update_card(card_id, payload.model_dump(exclude_unset=True), user_id=auth_user)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=res["error"])
    return {"success": True, "card": res}


@app.delete("/api/cards/{card_id}")
def delete_card(card_id: str, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.delete_card(card_id, user_id=auth_user)
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=res["error"])
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return {"success": True, "deleted": card_id}


@app.patch("/api/cards/{card_id}/move")
@app.put("/api/cards/{card_id}/move")
async def move_card_endpoint(card_id: str, payload: CardMoveRequest, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.move_card(
        card_id=card_id,
        destination_column_id=payload.columnId,
        position=payload.position or 0,
        user_id=auth_user,
    )
    if not res or (isinstance(res, dict) and "error" in res):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if isinstance(res, dict) and "error" in res else status.HTTP_404_NOT_FOUND,
            detail=res.get("error", "Card or Column not found") if isinstance(res, dict) else "Card not found",
        )
    project_id = res.get("boardId")
    if project_id:
        await ws_manager.broadcast_to_project(project_id, {"type": "BOARD_UPDATED", "projectId": project_id, "board": res})
    return {"success": True, "board": res}


@app.patch("/api/columns/{column_id}")
@app.put("/api/columns/{column_id}")
async def update_column_endpoint(column_id: str, payload: ColumnUpdateRequest, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.update_column(column_id, payload.title, user_id=auth_user)
    if not res or (isinstance(res, dict) and "error" in res):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if isinstance(res, dict) and "error" in res else status.HTTP_404_NOT_FOUND,
            detail=res.get("error", "Column not found") if isinstance(res, dict) else "Column not found",
        )
    return {"success": True, "column": res}


@app.post("/api/columns/{column_id}/clear")
async def clear_column_endpoint(column_id: str, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.clear_column_cards(column_id, user_id=auth_user)
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=res["error"])
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return {"success": True}


# Project Management Endpoints
@app.get("/api/projects", response_model=List[ProjectItem])
def get_projects(request: Request):
    auth_user = get_authenticated_user(request)
    return database.get_projects(auth_user)


@app.post("/api/projects", response_model=ProjectItem)
def create_project(payload: ProjectCreateRequest, request: Request):
    auth_user = get_authenticated_user(request)
    return database.create_project(auth_user, payload.name)


@app.put("/api/projects/{project_id}", response_model=ProjectItem)
def update_project(project_id: str, payload: ProjectUpdateRequest, request: Request):
    auth_user = get_authenticated_user(request)
    if not database.check_user_permission(project_id, auth_user, "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Insufficient permissions to rename project")
    updated = database.update_project(auth_user, project_id, payload.name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or forbidden")
    return updated


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, request: Request):
    auth_user = get_authenticated_user(request)
    if not database.check_user_permission(project_id, auth_user, "owner"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only owners can delete projects")
    deleted = database.delete_project(auth_user, project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or forbidden")
    return {"success": True, "deleted": project_id}


@app.get("/api/board")
def get_board(request: Request, project_id: Optional[str] = None):
    auth_user = get_authenticated_user(request)
    res = database.get_board(user_id=auth_user, project_id=project_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or forbidden")
    return res


@app.put("/api/board")
async def update_board(payload: BoardSaveRequest, request: Request, project_id: Optional[str] = None):
    auth_user = get_authenticated_user(request)
    if not project_id:
        # If not supplied in query, fall back to user's first accessible project
        projects = database.get_projects(auth_user)
        if projects:
            project_id = projects[0]["id"]
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id is required")

    if not database.check_user_permission(project_id, auth_user, "member"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Viewers cannot mutate board state")

    board_dict = payload.model_dump()
    res = database.save_board(user_id=auth_user, project_id=project_id, board_data=board_dict)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or forbidden")
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=res["error"])

    await ws_manager.broadcast_to_project(project_id, {"type": "BOARD_UPDATED", "projectId": project_id, "board": res})
    return res



# AI Endpoints
@app.post("/api/ai/test")
async def ai_test_endpoint():
    return await ai.test_ai_connection()


@app.post("/api/ai/chat")
async def ai_chat_endpoint(payload: AIChatRequest, request: Request):
    auth_user = get_authenticated_user(request)
    if payload.project_id and not database.check_user_permission(payload.project_id, auth_user, "viewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: insufficient permissions for project AI chat")

    current_board = payload.board or database.get_board(auth_user, project_id=payload.project_id)
    result = await ai.chat_with_ai(
        user_message=payload.message,
        history=payload.history or [],
        board_data=current_board,
    )
    return result


# Activity History Endpoints
@app.get("/api/projects/{project_id}/activity")
def get_activity_log(project_id: str, request: Request, limit: int = 50, offset: int = 0):
    auth_user = get_authenticated_user(request)
    safe_limit = min(max(1, limit), 100)
    if not database.check_user_permission(project_id, auth_user, "viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: insufficient permissions for activity log",
        )
    activities = database.get_project_activities(project_id, user_id=auth_user, limit=safe_limit, offset=offset)
    return {"activities": activities}


# Member Management Endpoints
@app.get("/api/projects/{project_id}/members")
def get_members(project_id: str, request: Request):
    auth_user = get_authenticated_user(request)
    if not database.check_user_permission(project_id, auth_user, "viewer"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Insufficient permissions")
    members = database.get_project_members(project_id)
    user_role = database.get_user_role(project_id, auth_user)
    return {"members": members, "userRole": user_role}


@app.post("/api/projects/{project_id}/members")
def add_member(project_id: str, payload: AddMemberRequest, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.add_project_member(project_id, payload.username, payload.role, auth_user)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in res.get("error", "").lower() else status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Failed to add member"),
        )
    return res


@app.delete("/api/projects/{project_id}/members/{target_username}")
def remove_member(project_id: str, target_username: str, request: Request):
    auth_user = get_authenticated_user(request)
    res = database.remove_project_member(project_id, target_username, auth_user)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=res.get("error", "Forbidden"),
        )
    return res


# Real-Time WebSocket Channel
@app.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str, token: Optional[str] = None):
    auth_user = None
    if token:
        sess = database.verify_session_token(token)
        if sess:
            auth_user = sess["username"]

    if not auth_user:
        await websocket.close(code=4001)
        return

    if not database.check_user_permission(project_id, auth_user, "viewer"):
        await websocket.close(code=4003)
        return

    await ws_manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.broadcast_to_project(project_id, data, sender=websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)
    except Exception:
        ws_manager.disconnect(websocket, project_id)


# Notification Endpoints
@app.get("/api/notifications")
def get_notifications(request: Request, limit: int = 50, offset: int = 0):
    auth_user = get_authenticated_user(request)
    return database.get_user_notifications(auth_user, limit=limit, offset=offset)


@app.put("/api/notifications/{notification_id}/read")
def mark_read(notification_id: str, request: Request):
    auth_user = get_authenticated_user(request)
    database.mark_notification_as_read(notification_id, auth_user)
    return {"success": True}


@app.post("/api/notifications/read-all")
def mark_all_read(request: Request):
    auth_user = get_authenticated_user(request)
    database.mark_all_notifications_read(auth_user)
    return {"success": True}


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    if STATIC_DIR.exists():
        try:
            requested_file = (STATIC_DIR / full_path).resolve()
            if requested_file.is_file() and str(requested_file).startswith(str(STATIC_DIR.resolve())):
                return FileResponse(requested_file)
        except Exception:
            pass

        index_file = STATIC_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

    return HTMLResponse(
        """<!DOCTYPE html>
<html>
<head><title>Project Management MVP</title></head>
<body>
<h1>FastAPI Backend Running</h1>
<p>Frontend static build not found. Run npm run build in frontend/.</p>
</body>
</html>"""
    )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8008))
    uvicorn.run(app, host="127.0.0.1", port=port)


