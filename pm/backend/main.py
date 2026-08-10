from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import ai
import database

# Ensure database and default tables exist
database.init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    database.seed_default_board("user")
    yield


app = FastAPI(title="Drag N Drop API", lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
if not STATIC_DIR.exists():
    STATIC_DIR = BASE_DIR.parent / "frontend" / "out"

if STATIC_DIR.exists():
    next_dir = STATIC_DIR / "_next"
    if next_dir.exists():
        app.mount("/_next", StaticFiles(directory=next_dir), name="next_assets")


class LoginRequest(BaseModel):
    username: str
    password: str


class CardCreateRequest(BaseModel):
    columnId: str
    cardId: Optional[str] = None
    title: str
    details: Optional[str] = ""
    priority: Optional[str] = "medium"


class CardUpdateRequest(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    priority: Optional[str] = None


class ColumnItem(BaseModel):
    id: str
    title: str
    cardIds: List[str]


class CardItem(BaseModel):
    id: str
    title: str
    details: str
    priority: Optional[str] = "medium"


class BoardSaveRequest(BaseModel):
    columns: List[ColumnItem]
    cards: Dict[str, CardItem]


class AIChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    board: Optional[Dict[str, Any]] = None


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(credentials: LoginRequest):
    if credentials.username == "user" and credentials.password == "password":
        return {
            "success": True,
            "user": credentials.username,
            "token": f"token-{credentials.username}-session",
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
    )


@app.post("/api/auth/logout")
def logout():
    return {"success": True}


@app.get("/api/board")
def get_board(username: str = "user"):
    return database.get_board(username)


@app.put("/api/board")
def update_board(payload: BoardSaveRequest, username: str = "user"):
    return database.save_board(username, payload.model_dump())


@app.post("/api/board/reset")
def reset_board(username: str = "user"):
    return database.reset_default_board(username)


@app.post("/api/cards")
def create_card(payload: CardCreateRequest, username: str = "user"):
    card_id = payload.cardId or f"card-{Path().resolve().stat().st_mtime_ns}"
    card = database.add_card(
        user_id=username,
        column_id=payload.columnId,
        card_id=card_id,
        title=payload.title,
        details=payload.details or "",
    )
    return {"success": True, "card": card}


@app.delete("/api/cards/{card_id}")
def delete_card(card_id: str):
    database.delete_card(card_id)
    return {"success": True, "deleted": card_id}


@app.post("/api/ai/test")
async def ai_test_endpoint():
    return await ai.test_ai_connection()


@app.post("/api/ai/chat")
async def ai_chat_endpoint(payload: AIChatRequest, username: str = "user"):
    current_board = payload.board or database.get_board(username)
    result = await ai.chat_with_ai(
        user_message=payload.message,
        history=payload.history or [],
        board_data=current_board,
    )
    
    # If AI returned a board update, automatically persist to SQLite
    if result.get("board_update"):
        updated_board = database.save_board(username, result["board_update"])
        result["board_update"] = updated_board
        
    return result


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
