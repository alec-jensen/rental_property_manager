from fastapi import FastAPI, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiomysql
from aiomysql.cursors import DictCursor
import os
import json
import uuid
import bcrypt
import secrets
import datetime
from typing import Annotated

from request_models import LoginRequestModel, CheckSessionRequestModel, UpdateUserRequestModel
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
        self.pool: aiomysql.Pool = await aiomysql.create_pool(
            host=os.getenv("MARIADB_HOST", "localhost"),
            port=int(os.getenv("MARIADB_PORT", 3306)),
            user=os.getenv("MARIADB_USER", "root"),
            password=os.getenv("MARIADB_PASSWORD", "password"),
            db=os.getenv("MARIADB_DATABASE", "test"),
            autocommit=True, cursorclass=DictCursor
        )


db = Database()

SQM = SQLQueryManager()
SQM.load_dir("./src/api/sql")

async def first_time_setup():
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw("admin".encode(), salt)

    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await SQM.execute("InitializeTables", cursor)
            await SQM.execute("CreateUser", cursor, (uuid.uuid4().hex, "admin", hashed_password, "admin@example.com", None, None, None, "admin"))

    with open("config.json", "r+") as f:
        config = json.load(f)
        config["installed"] = True
        f.seek(0)
        json.dump(config, f)
        f.truncate()

async def verify_session(session_id, session_token):
    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await SQM.execute("GetSessionById", cursor, (session_id,))
            session = await cursor.fetchone()

            if session is None:
                return False
            
            if bcrypt.checkpw(session_token.encode(), session["SessionToken"]):
                if datetime.datetime.now() < session["Expiry"]:
                    return True
                else:
                    await SQM.execute("DeleteSession", cursor, (session_id,))
                    return False
            else:
                return False


@app.on_event("startup")
async def startup():
    await db.init()

    with open("config.json", "r") as f:
        config = json.load(f)

    if not config["installed"]:
        await first_time_setup()


@app.post("/user/login")
async def login(request: LoginRequestModel):
    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
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
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                session_token = secrets.token_hex(16)
                session_expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

                token_hash = bcrypt.hashpw(session_token.encode(), bcrypt.gensalt())

                await SQM.execute("UpdateSession", cursor, (token_hash, session_expiry, request.session_id))

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
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await SQM.execute("DeleteSession", cursor, (request.session_id,))
                await conn.commit()

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
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await SQM.execute("GetSessionById", cursor, (session_id,))
                session = await cursor.fetchone()

                await SQM.execute("GetUserById", cursor, (session["UserId"],))
                user = await cursor.fetchone()

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )

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

@app.get("/user/{user_id}")
async def get_user_id(user_id: str, Authorization: Annotated[str | None, Header()]):
    if Authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    session_id, session_token = Authorization.removeprefix("Bearer ").split(":")

    if await verify_session(session_id, session_token):
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await SQM.execute("GetUserByUserId", cursor, (user_id,))
                user = await cursor.fetchone()

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )

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

@app.get("/users")
async def get_users(Authorization: Annotated[str | None, Header()], limit: int = 20, offset: int = 0):
    if Authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    session_id, session_token = Authorization.removeprefix("Bearer ").split(":")

    if await verify_session(session_id, session_token):
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await SQM.execute("GetUsers", cursor, (limit, offset))
                users = await cursor.fetchall()

                new_users = []

                for user in users:
                    new_users.append({
                        "created_at": user["Created"],
                        "user_id": user["UserId"],
                        "username": user["Username"],
                        "email": user["Email"],
                        "first_name": user["FirstName"],
                        "last_name": user["LastName"],
                        "role_id": user["RoleId"],
                    })

                return new_users
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

@app.patch("/user/{user_id}/update")
async def update_user(user_id: str, Authorization: Annotated[str | None, Header()], request: UpdateUserRequestModel):
    if Authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    session_id, session_token = Authorization.removeprefix("Bearer ").split(":")

    if await verify_session(session_id, session_token):
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await SQM.execute("GetUserByUserId", cursor, (user_id,))
                user = await cursor.fetchone()

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                if request.role_id is not None:
                    try:
                        try:
                            role_id = int(request.role_id)
                        except ValueError:
                            if request.role_id == "":
                                role_id = None
                            else:
                                raise ValueError

                        await SQM.execute("UpdateRoleId", cursor, (role_id, user_id))
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid role_id: must be an integer"
                        )
                    
                if request.username is not None:
                    await SQM.execute("UpdateUsername", cursor, (request.username, user_id))
                if request.email is not None:
                    await SQM.execute("UpdateEmail", cursor, (request.email, user_id))
                if request.password is not None:
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(request.password.encode(), salt)
                    await SQM.execute("UpdatePassword", cursor, (hashed_password, user_id))
                if request.first_name is not None:
                    await SQM.execute("UpdateFirstName", cursor, (request.first_name, user_id))
                if request.last_name is not None:
                    await SQM.execute("UpdateLastName", cursor, (request.last_name, user_id))

                return {"success": True}
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

    db.pool.close()
    asyncio.get_event_loop().run_until_complete(db.pool.wait_closed())


if __name__ == "__main__":
    main()
