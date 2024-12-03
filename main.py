from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("TOKEN")

# Configurer la connexion à la bdd
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialiser l'app
app = FastAPI()

# Dépendance 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if credentials.scheme != "Bearer" or credentials.credentials != TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    
@app.get("/")
def read_root():
    return {"message": "Welcome to the Authors API"}

@app.get("/books/categories/", dependencies=[Depends(verify_token)])
def get_books_by_category():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT t.Categories, COUNT(t.BookID) AS NumberOfBooks
                FROM authors_top5_table t
                GROUP BY t.Categories
                ORDER BY NumberOfBooks DESC
            """)
        ).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="No data found")

    return [{"Category": row[0], "NumberOfBooks": row[1]} for row in result]

@app.get("/authors/awards/", dependencies=[Depends(verify_token)])
def get_authors_with_awards():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT ad.Author, ad.BirthDate, aa.AwardName, aa.Year, aa.Work
                FROM authors_date_table ad
                INNER JOIN authors_awards_table aa ON ad.AuthorID = aa.AuthorID
                ORDER BY aa.Year DESC
            """)
        ).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="No data found")

    return [
        {
            "Author": row[0],
            "BirthDate": row[1],
            "AwardName": row[2],
            "Year": row[3],
            "Work": row[4]
        }
        for row in result
    ]
