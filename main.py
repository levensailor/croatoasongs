import sqlite3
import logging
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Set up logging
log_dir = Path("log_archive")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)

# Configure rotating file handler
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    log_dir / "app.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=3
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

# Initialize FastAPI app
app = FastAPI(title="Song Lyrics Manager", version="1.0.0")

# Database setup
DATABASE_NAME = "songs.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with songs table"""
    logger.info("Initializing database")
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            lyrics TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Pydantic models
class SongCreate(BaseModel):
    title: str
    lyrics: str = ""

class SongUpdate(BaseModel):
    title: Optional[str] = None
    lyrics: Optional[str] = None

class Song(BaseModel):
    id: int
    title: str
    lyrics: str
    created_at: str
    updated_at: str

# API Routes
@app.get("/api/v1/songs", response_model=List[Song])
def get_songs():
    """Get all songs"""
    logger.info("Fetching all songs")
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs ORDER BY title")
    songs = cursor.fetchall()
    conn.close()
    
    song_list = [dict(song) for song in songs]
    logger.info(f"Retrieved {len(song_list)} songs")
    return song_list

@app.get("/api/v1/songs/{song_id}", response_model=Song)
def get_song(song_id: int):
    """Get a specific song by ID"""
    logger.info(f"Fetching song with ID: {song_id}")
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    conn.close()
    
    if not song:
        logger.warning(f"Song with ID {song_id} not found")
        raise HTTPException(status_code=404, detail="Song not found")
    
    return dict(song)

@app.post("/api/v1/songs", response_model=Song)
def create_song(song: SongCreate):
    """Create a new song"""
    logger.info(f"Creating new song: {song.title}")
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO songs (title, lyrics) VALUES (?, ?)",
            (song.title, song.lyrics)
        )
        song_id = cursor.lastrowid
        conn.commit()
        
        # Get the created song
        cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
        created_song = cursor.fetchone()
        conn.close()
        
        logger.info(f"Successfully created song with ID: {song_id}")
        return dict(created_song)
    
    except sqlite3.IntegrityError:
        conn.close()
        logger.error(f"Song with title '{song.title}' already exists")
        raise HTTPException(status_code=400, detail="Song with this title already exists")

@app.put("/api/v1/songs/{song_id}", response_model=Song)
def update_song(song_id: int, song_update: SongUpdate):
    """Update an existing song"""
    logger.info(f"Updating song with ID: {song_id}")
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if song exists
    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    existing_song = cursor.fetchone()
    
    if not existing_song:
        conn.close()
        logger.warning(f"Song with ID {song_id} not found for update")
        raise HTTPException(status_code=404, detail="Song not found")
    
    # Update fields
    update_fields = []
    update_values = []
    
    if song_update.title is not None:
        update_fields.append("title = ?")
        update_values.append(song_update.title)
    
    if song_update.lyrics is not None:
        update_fields.append("lyrics = ?")
        update_values.append(song_update.lyrics)
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(song_id)
        
        query = f"UPDATE songs SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            cursor.execute(query, update_values)
            conn.commit()
            
            # Get updated song
            cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
            updated_song = cursor.fetchone()
            conn.close()
            
            logger.info(f"Successfully updated song with ID: {song_id}")
            return dict(updated_song)
        
        except sqlite3.IntegrityError:
            conn.close()
            logger.error(f"Song with title '{song_update.title}' already exists")
            raise HTTPException(status_code=400, detail="Song with this title already exists")
    
    conn.close()
    return dict(existing_song)

@app.delete("/api/v1/songs/{song_id}")
def delete_song(song_id: int):
    """Delete a song"""
    logger.info(f"Deleting song with ID: {song_id}")
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    
    if not song:
        conn.close()
        logger.warning(f"Song with ID {song_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Song not found")
    
    cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    conn.commit()
    conn.close()
    
    logger.info(f"Successfully deleted song with ID: {song_id}")
    return {"message": "Song deleted successfully"}

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
