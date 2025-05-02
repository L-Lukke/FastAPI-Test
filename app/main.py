from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Data models
class BasePost(BaseModel):
    title: Optional[str] = None
    content: str

class CreatePost(BasePost):
    pass

class UpdatePost(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

# Data store
myPosts = [
    {"title": "title1", "content": "content1", "id": 1},
    {"title": "title2", "content": "content2", "id": 2},
]

# Helper
def find_post_index_by_id(id: int):
    for i, post in enumerate(myPosts):
        if post["id"] == id:
            return i
    return None

# Routes
@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/posts")
def get_posts():
    return {"data": myPosts}

@app.get("/posts/{id}")
def get_post(id: int):
    for post in myPosts:
        if post["id"] == id:
            return {"data": post}
    raise HTTPException(status_code=404, detail="Post not found")

@app.post("/posts", status_code=201)
def create_post(payload: CreatePost):
    new_id = max([p["id"] for p in myPosts]) + 1 if myPosts else 1
    post = payload.model_dump()
    post["id"] = new_id
    myPosts.append(post)
    return {"message": "Post created", "data": post}

@app.put("/posts/{id}")
def update_post(id: int, payload: CreatePost):
    index = find_post_index_by_id(id)
    if index is None:
        raise HTTPException(status_code=404, detail="Post not found")
    myPosts[index] = {**payload.model_dump(), "id": id}
    return {"message": "Post updated", "data": myPosts[index]}

@app.patch("/posts/{id}")
def partial_update_post(id: int, payload: UpdatePost):
    index = find_post_index_by_id(id)
    if index is None:
        raise HTTPException(status_code=404, detail="Post not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        myPosts[index][key] = value
    return {"message": "Post partially updated", "data": myPosts[index]}

@app.delete("/posts/{id}", status_code=204)
def delete_post(id: int):
    index = find_post_index_by_id(id)
    if index is None:
        raise HTTPException(status_code=404, detail="Post not found")
    myPosts.pop(index)
    return Response(status_code=204)