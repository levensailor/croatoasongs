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

@app.get("/share/{song_id}")
def share_song(song_id: int):
    """Serve a shared song page"""
    logger.info(f"Serving shared song with ID: {song_id}")
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    conn.close()
    
    if not song:
        logger.warning(f"Song with ID {song_id} not found for sharing")
        raise HTTPException(status_code=404, detail="Song not found")
    
    song_dict = dict(song)
    
    # Create HTML content for the shared song
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{song_dict['title']} - CROATOA</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --text-accent: #00ff88;
            --border-color: #333;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }}
        
        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        body {{
            background: var(--bg-primary);
            background-image: 
                radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 0, 136, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(0, 136, 255, 0.1) 0%, transparent 50%);
            min-height: 100vh;
            color: var(--text-primary);
            overflow-x: hidden;
        }}
        
        .glass-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        .neon-text {{
            color: var(--text-accent);
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }}
        
        .lyrics-display {{
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            max-height: 70vh;
            overflow-y: auto;
        }}
        
        .header-logo {{
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 900;
            font-size: 2.5rem;
            letter-spacing: -0.05em;
            text-align: center;
            margin-bottom: 2rem;
        }}
        
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
        }}
        
        .btn-secondary:hover {{
            background: rgba(0, 255, 136, 0.1);
            border-color: var(--text-accent);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container mx-auto p-8 max-w-4xl">
        <div class="text-center mb-8">
            <h1 class="header-logo">CROATOA</h1>
            <a href="/" class="btn-secondary">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/>
                </svg>
                Back to Song Manager
            </a>
        </div>
        
        <div class="glass-card p-8">
            <div class="text-center mb-8">
                <h2 class="text-3xl font-bold neon-text mb-2">{song_dict['title']}</h2>
                <p class="text-gray-400">by CROATOA</p>
            </div>
            
            <div class="lyrics-display">
{song_dict['lyrics'] if song_dict['lyrics'] else 'No lyrics available for this song.'}
            </div>
            
            <div class="text-center mt-6 text-sm text-gray-500">
                <p>Created: {song_dict['created_at']}</p>
                {f"<p>Last updated: {song_dict['updated_at']}</p>" if song_dict['updated_at'] != song_dict['created_at'] else ""}
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
