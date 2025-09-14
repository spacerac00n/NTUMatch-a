from typing import Optional, Dict, Any
import httpx
import asyncio

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get backend URL 
backend_url = os.getenv("BACKEND_URL")

class NTUMatchAPI:
    def __init__(self, base_url: str = f"{backend_url}"):
        self.base_url = base_url
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[dict]:
        # Create a new user via API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/users/", json=user_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error creating user: {e}")
                return None

    async def get_user_by_telegram_username(self, telegram_username: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/users/telegram/{telegram_username}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error fetching user by Telegram username: {e}")
                return None
    
    async def update_user_by_telegram_username (self, telegram_username: str, user_data: Dict[str, Any]) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(f"{self.base_url}/users/telegram/{telegram_username}", json=user_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error updating user by Telegram username: {e}")
                return None

    async def delete_user_by_telegram_username(self, telegram_username: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{self.base_url}/users/telegram/{telegram_username}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error deleting user by Telegram username: {e}")
                return None