"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Ludo game schemas

class Room(BaseModel):
    """
    Ludo room schema
    Collection name: "room"
    """
    room_code: str = Field(..., description="Short code to join the room")
    created_by: str = Field(..., description="Player ID of the creator")
    status: str = Field("waiting", description="waiting | playing | finished")
    players: List[str] = Field(default_factory=list, description="List of player IDs in join order")
    max_players: int = Field(4, ge=2, le=4)
    created_at: Optional[datetime] = None

class Move(BaseModel):
    """
    Ludo move schema
    Collection name: "move"
    """
    room_code: str
    player_id: str
    piece: str = Field(..., description="Which piece was moved (e.g., R1, G2)")
    from_pos: int = Field(..., ge=-1, le=57, description="-1 for home, 0-57 board index")
    to_pos: int = Field(..., ge=0, le=57)
    dice: int = Field(..., ge=1, le=6)
    created_at: Optional[datetime] = None

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
