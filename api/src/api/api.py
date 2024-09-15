from fastapi import FastAPI, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from asyncmy import connect
from asyncmy.cursors import DictCursor
import os
import json
import uuid
import bcrypt
import secrets
import datetime
from typing import Annotated

from request_models import LoginRequestModel, CheckSessionRequestModel
from sql_query_manager import SQLQueryManager

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# TODO: Changes made from another client on the database
# from another client aren't reflected on the api for some reason

class Database:
    async def init(self):
        self.conn = await connect(
            host=os.getenv("MARIADB_HOST", "localhost"),
            port=int(os.getenv("MARIADB_PORT", 3306)),
            user=os.getenv("MARIADB_USER", "root"),
            password=os.getenv("MARIADB_PASSWORD", "password"),
            database=os.getenv("MARIADB_DATABASE", "test"),
            autocommit=True
        )


db = Database()

SQM = SQLQueryManager()
SQM.load_dir("./src/api/sql")

async def first_time_setup():
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw("admin".encode(), salt)

    async with db.conn.cursor(cursor=DictCursor) as cursor:
        await SQM.execute("InitializeTables", cursor)
        await SQM.execute("CreateUser", cursor, (uuid.uuid4().hex, "admin", hashed_password, "admin@example.com", None, None, None, "admin"))
        await db.conn.commit()

    with open("config.json", "r+") as f:
        config = json.load(f)
        config["installed"] = True
        f.seek(0)
        json.dump(config, f)
        f.truncate()

async def verify_session(session_id, session_token):
    async with db.conn.cursor(cursor=DictCursor) as cursor:
        await SQM.execute("GetSessionById", cursor, (session_id,))
        session = await cursor.fetchone()

        if session is None:
            return False
        
        if bcrypt.checkpw(session_token.encode(), session["SessionToken"]):
            if datetime.datetime.now() < session["Expiry"]:
                return True
            else:
                await SQM.execute("DeleteSession", cursor, (session_id,))
                await db.conn.commit()
                return False
        else:
            return False


@app.on_event("startup")
async def startup():
    await db.init()

    SQM.set_connection(db.conn)

    with open("config.json", "r") as f:
        config = json.load(f)

    if not config["installed"]:
        await first_time_setup()


@app.post("/user/login")
async def login(request: LoginRequestModel):
    async with db.conn.cursor(cursor=DictCursor) as cursor:
        await SQM.execute("GetUserByEmail", cursor, (request.email,))
        user = await cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if bcrypt.checkpw(request.password.encode(), user["Password"]):
            session_id = uuid.uuid4().hex
            session_token = secrets.token_hex(16)
            session_expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

            token_hash = bcrypt.hashpw(session_token.encode(), bcrypt.gensalt())

            await SQM.execute("CreateSession", cursor, (user["Id"], session_id, token_hash, session_expiry))
            await db.conn.commit()

            return {
                "session_id": session_id,
                "session_token": session_token,
                "session_expiry": session_expiry
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )


@app.post("/user/check_session")
async def check_session(request: CheckSessionRequestModel):
    if await verify_session(request.session_id, request.session_token):
        return {"valid": True}
    else:
        return {"valid": False}


@app.post("/user/renew_session")
async def renew_session(request: CheckSessionRequestModel):
    if await verify_session(request.session_id, request.session_token):
        async with db.conn.cursor(cursor=DictCursor) as cursor:
            session_token = secrets.token_hex(16)
            session_expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

            token_hash = bcrypt.hashpw(session_token.encode(), bcrypt.gensalt())

            await SQM.execute("UpdateSession", cursor, (token_hash, session_expiry, request.session_id))
            await db.conn.commit()

            return {
                "session_token": session_token,
                "session_expiry": session_expiry
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )


@app.post("/user/logout")
async def logout(request: CheckSessionRequestModel):
    if await verify_session(request.session_id, request.session_token):
        async with db.conn.cursor(cursor=DictCursor) as cursor:
            await SQM.execute("DeleteSession", cursor, (request.session_id,))
            await db.conn.commit()

            return {"success": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

@app.get("/user/@me")
async def get_user(Authorization: Annotated[str | None, Header()]):
    if Authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    session_id, session_token = Authorization.removeprefix("Bearer ").split(":")

    if await verify_session(session_id, session_token):
        async with db.conn.cursor(cursor=DictCursor) as cursor:
            await SQM.execute("GetSessionById", cursor, (session_id,))
            session = await cursor.fetchone()

            await SQM.execute("GetUserById", cursor, (session["UserId"],))
            user = await cursor.fetchone()

            return {
                "created_at": user["Created"],
                "user_id": user["UserId"],
                "username": user["Username"],
                "email": user["Email"],
                "first_name": user["FirstName"],
                "last_name": user["LastName"],
                "role_id": user["RoleId"],
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )



def main():
    if not os.path.exists("config.json"):
        with open("config.json", "w") as f:
            json.dump({"installed": False}, f)
    else:
        with open("config.json", "r") as f:
            if f.read() == "":
                with open("config.json", "w") as f:
                    json.dump({"installed": False}, f)

    import uvicorn
    uvicorn.run(
        "api:app",
        host=os.getenv("API_HOST", "localhost"),
        port=int(os.getenv("API_PORT", 8000))
    )


if __name__ == "__main__":
    main()

    db.conn.close()
