from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import get_connection, init_db

import sqlite3
import pandas as pd
import hashlib
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# -----------------------------
# HELPERS
# -----------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_data():
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(BASE_DIR, "data", "agroconnect.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM retailers", conn)
    conn.close()
    return df


# -----------------------------
# MODELS
# -----------------------------

class Farmer(BaseModel):
    name: str
    phone: str
    password: str

class SearchRecord(BaseModel):
    phone: str
    district: str
    product: str
    results_count: int


# -----------------------------
# ROUTES
# -----------------------------

@app.get("/")
def home():
    return {"message": "AgroConnect API Running"}


@app.get("/search")
def search(product: str, district: str):
    df = load_data()
    result = df[
        (df["product name"].str.lower().str.contains(product.lower()))
        &
        (df["district name"].str.lower().str.contains(district.lower()))
    ]
    return result.to_dict(orient="records")


# -----------------------------
# REGISTER
# -----------------------------

@app.post("/register")
def register_farmer(farmer: Farmer):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed = hash_password(farmer.password)
        cursor.execute(
            "INSERT INTO farmers (name, phone, password) VALUES (?, ?, ?)",
            (farmer.name, farmer.phone, hashed)
        )
        conn.commit()
        return {"message": "Registration successful"}
    except sqlite3.IntegrityError:
        return {"message": "Phone number already registered"}
    except Exception as e:
        return {"message": str(e)}
    finally:
        conn.close()


# -----------------------------
# LOGIN
# -----------------------------

@app.post("/login")
def login_farmer(farmer: Farmer):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed = hash_password(farmer.password)
        cursor.execute(
            "SELECT id, name, phone FROM farmers WHERE phone = ? AND password = ?",
            (farmer.phone, hashed)
        )
        user = cursor.fetchone()
        if user:
            return {
                "message": "Login successful",
                "name": user["name"],
                "phone": user["phone"]
            }
        return {"message": "Invalid credentials"}
    except Exception as e:
        return {"message": str(e)}
    finally:
        conn.close()


# -----------------------------
# SAVE SEARCH HISTORY
# -----------------------------

@app.post("/history/save")
def save_history(record: SearchRecord):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO search_history
            (phone, district, product, results_count, searched_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record.phone,
                record.district,
                record.product,
                record.results_count,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        return {"message": "Saved"}
    except Exception as e:
        return {"message": str(e)}
    finally:
        conn.close()


# -----------------------------
# GET SEARCH HISTORY
# -----------------------------

@app.get("/history/{phone}")
def get_history(phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT district, product, results_count, searched_at
            FROM search_history
            WHERE phone = ?
            ORDER BY searched_at DESC
            LIMIT 20
            """,
            (phone,)
        )
        rows = cursor.fetchall()
        return [
            {
                "district": row["district"],
                "product": row["product"],
                "results_count": row["results_count"],
                "searched_at": row["searched_at"]
            }
            for row in rows
        ]
    except Exception as e:
        return []
    finally:
        conn.close()


# -----------------------------
# CLEAR SEARCH HISTORY
# -----------------------------

@app.delete("/history/{phone}")
def clear_history(phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM search_history WHERE phone = ?",
            (phone,)
        )
        conn.commit()
        return {"message": "History cleared"}
    except Exception as e:
        return {"message": str(e)}
    finally:
        conn.close()