from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import get_connection, init_db

import sqlite3
import pandas as pd
import hashlib
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# INIT DATABASE ON STARTUP
init_db()


# -----------------------------
# HELPERS
# -----------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def load_data():
    BASE_DIR = os.path.dirname(
        os.path.dirname(__file__)
    )
    db_path = os.path.join(
        BASE_DIR, "data", "agroconnect.db"
    )
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(
        "SELECT * FROM retailers", conn
    )
    conn.close()
    return df


# -----------------------------
# AUTH MODELS
# -----------------------------

class Farmer(BaseModel):
    name: str
    phone: str
    password: str


# -----------------------------
# ROUTES
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "AgroConnect API Running"
    }


@app.get("/search")
def search(product: str, district: str):
    df = load_data()
    result = df[
        (
            df["product name"]
            .str.lower()
            .str.contains(product.lower())
        )
        &
        (
            df["district name"]
            .str.lower()
            .str.contains(district.lower())
        )
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
            """
            INSERT INTO farmers
            (name, phone, password)
            VALUES (?, ?, ?)
            """,
            (farmer.name, farmer.phone, hashed)
        )

        conn.commit()

        return {
            "message": "Registration successful"
        }

    except sqlite3.IntegrityError:
        return {
            "message": "Phone number already registered"
        }

    except Exception as e:
        return {
            "message": str(e)
        }

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
            """
            SELECT id, name, phone
            FROM farmers
            WHERE phone = ?
            AND password = ?
            """,
            (farmer.phone, hashed)
        )

        user = cursor.fetchone()

        if user:
            return {
                "message": "Login successful",
                "name": user["name"],
                "phone": user["phone"]
            }

        return {
            "message": "Invalid credentials"
        }

    except Exception as e:
        return {
            "message": str(e)
        }

    finally:
        conn.close()