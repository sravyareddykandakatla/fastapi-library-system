from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Library Book System")

# --- Fake Databases ---
books = []
users = []
borrows = []

# --- Schemas ---
class Book(BaseModel):
    id: int
    title: str
    author: str
    genre: Optional[str] = None
    available: bool = True

class User(BaseModel):
    id: int
    name: str
    email: str

class Borrow(BaseModel):
    user_id: int
    book_id: int
    status: str = "borrowed"   # borrowed / returned

# --- Routes ---
@app.get("/")
def home():
    return {"message": "Welcome to Library API"}

# -------------------------------
# Book APIs
# -------------------------------
@app.get("/books")
def get_books():
    return {"books": books, "total": len(books)}

@app.get("/books/{id}")
def get_book(id: int):
    for book in books:
        if book.id == id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")

@app.post("/books")
def add_book(book: Book):
    books.append(book)
    return {"message": "Book added successfully", "book": book}

@app.get("/books/summary")
def book_summary():
    total = len(books)
    available = len([b for b in books if b.available])
    unavailable = total - available
    return {
        "total_books": total,
        "available": available,
        "unavailable": unavailable
    }

@app.put("/books/{id}")
def update_book(id: int, title: Optional[str] = None, author: Optional[str] = None, genre: Optional[str] = None, available: Optional[bool] = None):
    for book in books:
        if book.id == id:
            if title is not None:
                book.title = title
            if author is not None:
                book.author = author
            if genre is not None:
                book.genre = genre
            if available is not None:
                book.available = available
            return {"message": "Book updated successfully", "book": book}
    raise HTTPException(status_code=404, detail="Book not found")

@app.delete("/books/{id}")
def delete_book(id: int):
    for book in books:
        if book.id == id:
            books.remove(book)
            return {"message": "Book deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found")

# -------------------------------
# User APIs
# -------------------------------
@app.post("/users")
def add_user(user: User):
    users.append(user)
    return {"message": "User added successfully", "user": user}

@app.get("/users")
def list_users():
    return {"users": users, "total": len(users)}

@app.get("/users/{id}")
def get_user(id: int):
    for user in users:
        if user.id == id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

# -------------------------------
# Borrow / Return Workflow
# -------------------------------
@app.post("/borrow")
def borrow_book(borrow: Borrow):
    # Check user exists
    user = next((u for u in users if u.id == borrow.user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check book exists
    book = next((b for b in books if b.id == borrow.book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.available:
        raise HTTPException(status_code=400, detail="Book not available")

    book.available = False
    borrows.append(borrow)
    return {"message": "Book borrowed successfully", "borrow": borrow}

@app.post("/return")
def return_book(user_id: int, book_id: int):
    for borrow in borrows:
        if borrow.user_id == user_id and borrow.book_id == book_id and borrow.status == "borrowed":
            borrow.status = "returned"
            # Mark book available again
            book = next((b for b in books if b.id == book_id), None)
            if book:
                book.available = True
            return {"message": "Book returned successfully", "borrow": borrow}
    raise HTTPException(status_code=404, detail="Borrow record not found")

@app.get("/history/{user_id}")
def borrow_history(user_id: int):
    history = [b for b in borrows if b.user_id == user_id]
    return {"user_id": user_id, "history": history}

# -------------------------------
# Advanced APIs (Search / Sort / Pagination / Browse)
# -------------------------------
@app.get("/books/search")
def search_books(keyword: str):
    result = [b for b in books if keyword.lower() in b.title.lower()]
    return {"results": result}

@app.get("/books/sort")
def sort_books(sort_by: str = "title", order: str = "asc"):
    reverse = True if order == "desc" else False
    try:
        return sorted(books, key=lambda x: getattr(x, sort_by), reverse=reverse)
    except AttributeError:
        raise HTTPException(status_code=400, detail="Invalid sort field")

@app.get("/books/page")
def paginate_books(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    return {"page": page, "books": books[start:end]}

@app.get("/books/browse")
def browse_books(keyword: Optional[str] = None, sort_by: str = "title", order: str = "asc", page: int = 1, limit: int = 2):
    result = books

    # Search
    if keyword:
        result = [b for b in result if keyword.lower() in b.title.lower()]

    # Sort
    reverse = True if order == "desc" else False
    try:
        result = sorted(result, key=lambda x: getattr(x, sort_by), reverse=reverse)
    except AttributeError:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    # Pagination
    start = (page - 1) * limit
    end = start + limit

    return {
        "total": len(result),
        "page": page,
        "books": result[start:end]
    }
