from fastapi import FastAPI, HTTPException, Depends, Response, status
from pydantic import BaseModel
from typing import Optional
import psycopg
from psycopg.rows import dict_row

app = FastAPI()

# ------
# Models
# ------

class BasePost(BaseModel):
    title: Optional[str] = None
    content: str

class CreatePost(BasePost):
    pass

class UpdatePost(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

# -------------------------
# Dependency: DB connection
# -------------------------

def get_db():
    conn = psycopg.connect(
        host="localhost",
        dbname="fastapitest",
        user="postgres",
        password="password123",
        row_factory=dict_row
    )
    try:
        yield conn
    finally:
        conn.close()

# ------
# Routes
# ------

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/posts")
def get_posts(conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM posts")
        posts = cur.fetchall()
        return {"data": posts}

@app.get("/posts/{id}")
def get_post(id: int, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM posts WHERE id = %s", (id,))
        post = cur.fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"data": post}

@app.post("/posts", status_code=201)
def create_post(payload: CreatePost, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO posts (title, content) VALUES (%s, %s) RETURNING *",
            (payload.title, payload.content)
        )
        new_post = cur.fetchone()
        conn.commit()
        return {"message": "Post created", "data": new_post}

@app.put("/posts/{id}")
def update_post(id: int, payload: CreatePost, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE posts SET title = %s, content = %s WHERE id = %s RETURNING *",
            (payload.title, payload.content, id)
        )
        updated_post = cur.fetchone()
        if not updated_post:
            raise HTTPException(status_code=404, detail="Post not found")
        conn.commit()
        return {"message": "Post updated", "data": updated_post}

@app.patch("/posts/{id}")
def partial_update_post(id: int, payload: UpdatePost, conn = Depends(get_db)):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{key} = %s" for key in updates)
    values = list(updates.values()) + [id]

    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE posts SET {set_clause} WHERE id = %s RETURNING *",
            values
        )
        updated_post = cur.fetchone()
        if not updated_post:
            raise HTTPException(status_code=404, detail="Post not found")
        conn.commit()
        return {"message": "Post partially updated", "data": updated_post}

@app.delete("/posts/{id}", status_code=204)
def delete_post(id: int, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM posts WHERE id = %s RETURNING id", (id,))
        deleted = cur.fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="Post not found")
        conn.commit()
    return Response(status_code=204)
