import asyncio
from websockets.asyncio.server import serve, broadcast
import sys
import json
from datetime import datetime
import aiosqlite
import sqlite3
import traceback
import time


host = "localhost"
port = 8005

user_db = None
msg_db = None

pending_msgs = []

async def init_db():
    global user_db, msg_db
    user_db = await aiosqlite.connect("user.db")
    msg_db = await aiosqlite.connect("messages.db")

    await user_db.execute("PRAGMA journal_mode=WAL;")
    await msg_db.execute("PRAGMA journal_mode=WAL;")
    
    await user_db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
        
    await msg_db.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        body TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );""")
    await user_db.commit()
    await msg_db.commit()
connections = []


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def webhook_handler(websocket):
    print(f"webhook_handler triggered for {id(websocket)}")
    websocket_id = str(id(websocket))[:6]
    websocket.username = "anonymous"

    print(f"Client {websocket_id} has joined >>>")
    if websocket not in connections:
        connections.append(websocket)

    for username, body, timestamp in await get_messages():
        prev_message_data = json.dumps({
            "username" : username,
            "client_id" : "past_msgs",
            "body" : body,
            "date_time" : timestamp
        })
        await websocket.send(prev_message_data)
    try:
        async for message in websocket:

            if await check_commands(message, websocket):
                continue
            
            # await save_message(websocket.username, message)
            
            message_data = json.dumps({
                "username": getattr(websocket, "username", "anonymous"),  
                "client_id": websocket_id,
                "body": message,
                "date_time": datetime.now().isoformat()
            })  

            pending_msgs.append((websocket.username, message, datetime.now().isoformat()))

            broadcast(connections, message_data)
            print(f"{websocket_id}\n{websocket.username}: {message}")
    except Exception as e:
        print(f"Error in message loop: {e}")
        traceback.print_exc()
    finally:
        connections.remove(websocket)
        await websocket.close()


async def check_commands(message, websocket):
    if message.startswith("/nick "):
        new_name = message.split("/nick ", 1)[1].strip()
        websocket.username = new_name
        broadcast(connections, json.dumps({
            "username": "Server",  
            "client_id": "Server",
            "body": f"User changed name to {new_name}",
            "date_time": datetime.now().isoformat()
        }))
        return True
    elif message.startswith("/register "):
        parts = message.split(" ", 2)
        if len(parts) < 3:
            await websocket.send(json.dumps({
                "username": "Server",
                "body": "Usage: /register <username> <password>"
                })
                )
            return True


        _, name, password = parts
        
        if await register_user(name, password):
            await websocket.send(json.dumps({
                "username": "Server",
                "body": f"User: {name} registered succesfully"
                })
                )
            return True
        else:
            await websocket.send(json.dumps({
                "username": "Server",
                "body": f"Username: {name} is already taken"
                })
                )
            return True
 
    elif message.startswith("/login "):
        parts = message.split(" ", 2)
        if len(parts) < 3:
            await websocket.send(json.dumps({
                "username": "Server",
                "body": "Usage: /login <username> <password>"
                })
                )
            return True
        
        _, name, password = parts

        if await login_user(name, password):
            websocket.username = name
            await websocket.send(json.dumps({
                "username": "Server",
                "body": f"login for {name} was succesfull"
                })
                )
        else:
            await websocket.send(json.dumps({"username": "Server", "body": "Invalid credentials"}))
        return True


    else:
        return False

async def flush_msgs_periodically():
    while True:
        await asyncio.sleep(60)
        print("MESSAGES FLUSHED")
        await flush_msgs()

async def flush_msgs():
    global pending_msgs, msg_db

    if not pending_msgs:
        return
    else:
        for username, body, timestamp in pending_msgs:
            await msg_db.execute("INSERT INTO messages (username, body, timestamp) VALUES (?, ?, ?)", (username, body, timestamp))
            await msg_db.commit()
            pending_msgs.clear()

async def register_user(name, password):
    """    try:
        await user_db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (name, password))
        await user_db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False
    """

    try:
        await asyncio.to_thread(sync_register_user, name, password)
        return True
    except sqlite3.IntegrityError:
        return False

def sync_register_user(name: str, password: str):
    conn = sqlite3.connect("user.db")
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (name, password)
        )
        conn.commit()
    finally:
        conn.close()


async def login_user(username, password):
    global user_db
    async with user_db.execute("SELECT password FROM users WHERE username = ?", (username,)) as cursor:
        row = await cursor.fetchone()
        if row and row[0] == password:
            return True
    return False

async def save_message(username, body):
    global msg_db
    timestamp = datetime.now().isoformat()
    await msg_db.execute("INSERT INTO messages (username, body, timestamp) VALUES (?, ?, ?)", (username, body, timestamp))
    await msg_db.commit()
    rows = await get_messages()
    print(f"Messages in DB: {len(rows)}")

async def get_messages(limit=50):
    global msg_db
    cursor = await msg_db.execute("SELECT username, body, timestamp FROM messages ORDER BY id desc LIMIT ?", (limit,))
    rows = await cursor.fetchall()
    await cursor.close()
    return rows


async def broadcast_message(message, exclude=None):
    for conn in connections:
        if conn == exclude:
            continue
        try:
            await conn.send(message)
        except Exception as e:
            print(f"Broadcast error: {e}")
            traceback.print_exc()


async def inspect_schema():
    async with user_db.execute("PRAGMA table_info(users);") as cursor:
        print("Users table schema:")
        for row in await cursor.fetchall():
            print(row)

    async with msg_db.execute("PRAGMA table_info(messages);") as cursor:
        print("Messages table schema:")
        for row in await cursor.fetchall():
            print(row)


async def main():
    await init_db()

    asyncio.create_task(flush_msgs_periodically())

    async with serve(webhook_handler, host, port) as server:
        print(f"Running on: ws://{host}:{port}")
        await server.serve_forever()

asyncio.run(main())
