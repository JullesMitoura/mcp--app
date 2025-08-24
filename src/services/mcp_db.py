from pydantic import BaseModel, Field, EmailStr
from mcp.server.fastmcp import FastMCP
from typing import Optional

import sqlite3
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# defining a mcp instance with name Clients
mcp = FastMCP("Clients")

# database connection
DB_PATH = "/Users/mitoura/Desktop/Repositories/app--mcp/clients.db"
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# create clients table
def create_table(conn: sqlite3.Connection,
                 schema: str):
    cursor = conn.cursor()
    cursor.execute(schema)
    conn.commit()

# execute a query
def execute_query(conn: sqlite3.Connection, query: str, params: tuple = ()):
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    return cursor

def fetch_query(conn: sqlite3.Connection, query: str, params: tuple = ()):
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor

# pydantic models
# base model for a client
class ClientBase(BaseModel):
    name: str = Field(..., min_length=2, 
                      description="Client name")
    email: EmailStr = Field(..., 
                            description="Client email")

# base model for a storage in DB
class ClientDB(ClientBase):
    id: int = Field(..., 
                    description="Client ID. This information must to be unique.")

# base model for a client response
class ClientResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    error: Optional[str] = None

# base model for a list of clients  
class ListClientResponse(BaseModel):
    clients: list[ClientDB]


# defining mcp tools
@mcp.tool()
def create_client(client: ClientBase) -> str:
    """
    This function creates a new client in the database.
    As input, is expected a JSON object with 'name' and 'email' fields.
    Return the data of created client in a JSON format.
    """
    try:
        # start connection
        conn = get_db_connection()

        # create a table if not exists
        create_table(conn, """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
        """)

        cursor = execute_query(conn, 
            "INSERT INTO clients (name, email) VALUES (?, ?)",
            (client.name, client.email)
        )

        client_id = cursor.lastrowid
        response = ClientDB(id=client_id, name=client.name, email=client.email)
        return response.model_dump_json()
    except sqlite3.IntegrityError as e:
        error = ClientResponse(error=str(e)).model_dump_json()
        logging.error(f"Integrity error: {error}")
        return error
    
@mcp.tool()
def get_client(id: int) -> str:
    """
    Function to get information about a client using id to search in database.
    The input id must be an integer.
    This function returns a JSON or an error message.
    """
    try:
        client_id = int(id)
        logging.info(f"Fetching client with ID: {client_id}")
    except ValueError:
        return ClientResponse(error=f"Invalid id: {id}").model_dump_json()

    try:
        conn = get_db_connection()
        cursor = fetch_query(conn, "SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()
        if client:
            response = ClientDB(**dict(client))  # converte Row para dict
            return response.model_dump_json()
        else:
            error = ClientResponse(error="Client not found").model_dump_json()
            logging.error(f"Client not found: {error}")
            return error
    except Exception as e:
        error = ClientResponse(error=str(e)).model_dump_json()
        logging.error(f"Error getting client: {error}")
        return error

@mcp.prompt()
def system_prompt() -> str:
    # return the system prompt
    return """
    You are a helpful assistant called JullesBot. Call tools as needed.
    """

if __name__ == "__main__":
    # mcp.run(transport="streamable-http")
    mcp.run(transport="sse")