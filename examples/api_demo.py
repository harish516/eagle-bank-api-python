"""Example script demonstrating API usage with authentication."""

import asyncio
import httpx
import json
from typing import Dict, Any


class EagleBankAPIClient:
    """Client for interacting with Eagle Bank API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: str = None
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token
        self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        response = await self.client.post("/v1/users", json=user_data)
        response.raise_for_status()
        return response.json()
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID."""
        response = await self.client.get(f"/v1/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    async def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account."""
        response = await self.client.post("/v1/accounts", json=account_data)
        response.raise_for_status()
        return response.json()
    
    async def list_accounts(self) -> Dict[str, Any]:
        """List all accounts."""
        response = await self.client.get("/v1/accounts")
        response.raise_for_status()
        return response.json()
    
    async def get_account(self, account_number: str) -> Dict[str, Any]:
        """Get account by number."""
        response = await self.client.get(f"/v1/accounts/{account_number}")
        response.raise_for_status()
        return response.json()
    
    async def create_transaction(
        self, 
        account_number: str, 
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a transaction."""
        response = await self.client.post(
            f"/v1/accounts/{account_number}/transactions",
            json=transaction_data
        )
        response.raise_for_status()
        return response.json()
    
    async def list_transactions(self, account_number: str) -> Dict[str, Any]:
        """List transactions for an account."""
        response = await self.client.get(f"/v1/accounts/{account_number}/transactions")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()


async def main():
    """Example usage of the API client."""
    
    # Sample data
    user_data = {
        "name": "Alice Johnson",
        "address": {
            "line1": "456 Oak Street",
            "town": "Manchester",
            "county": "Greater Manchester", 
            "postcode": "M1 1AA"
        },
        "phone_number": "+447700900456",
        "email": "alice.johnson@example.com"
    }
    
    account_data = {
        "name": "Alice's Personal Account",
        "account_type": "personal"
    }
    
    transaction_data = {
        "amount": 500.00,
        "currency": "GBP",
        "type": "deposit",
        "reference": "Initial deposit"
    }
    
    async with EagleBankAPIClient() as client:
        try:
            # Check API health
            print("🏥 Checking API health...")
            health = await client.health_check()
            print(f"Health status: {health['status']}")
            
            # For demo purposes, we'll skip actual authentication
            # In real usage, you would:
            # 1. Authenticate with Keycloak
            # 2. Get JWT token
            # 3. Set token in client
            
            # Mock token for demonstration
            mock_token = "mock-jwt-token-for-demo"
            client.set_token(mock_token)
            
            print("\n👤 Creating user...")
            try:
                user = await client.create_user(user_data)
                print(f"User created: {user['id']} - {user['name']}")
                user_id = user['id']
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    print("❌ Authentication required. Please set up Keycloak and get a valid token.")
                    return
                else:
                    print(f"❌ Failed to create user: {e}")
                    return
            
            print("\n🏦 Creating account...")
            try:
                account = await client.create_account(account_data)
                print(f"Account created: {account['account_number']} - {account['name']}")
                print(f"Initial balance: £{account['balance']}")
                account_number = account['account_number']
            except httpx.HTTPStatusError as e:
                print(f"❌ Failed to create account: {e}")
                return
            
            print("\n💰 Creating transaction...")
            try:
                transaction = await client.create_transaction(account_number, transaction_data)
                print(f"Transaction created: {transaction['id']}")
                print(f"Amount: £{transaction['amount']} ({transaction['type']})")
            except httpx.HTTPStatusError as e:
                print(f"❌ Failed to create transaction: {e}")
                return
            
            print("\n📋 Listing accounts...")
            try:
                accounts = await client.list_accounts()
                print(f"Found {len(accounts['accounts'])} accounts")
                for acc in accounts['accounts']:
                    print(f"  - {acc['account_number']}: £{acc['balance']}")
            except httpx.HTTPStatusError as e:
                print(f"❌ Failed to list accounts: {e}")
            
            print("\n📊 Listing transactions...")
            try:
                transactions = await client.list_transactions(account_number)
                print(f"Found {len(transactions['transactions'])} transactions")
                for tx in transactions['transactions']:
                    print(f"  - {tx['id']}: £{tx['amount']} ({tx['type']})")
            except httpx.HTTPStatusError as e:
                print(f"❌ Failed to list transactions: {e}")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


def demonstrate_concurrent_requests():
    """Demonstrate concurrent API requests."""
    
    async def make_concurrent_requests():
        """Make multiple concurrent requests."""
        async with EagleBankAPIClient() as client:
            # Make multiple health checks concurrently
            tasks = [client.health_check() for _ in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            print("🚀 Concurrent health checks results:")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"  Request {i+1}: ❌ {result}")
                else:
                    print(f"  Request {i+1}: ✅ {result['status']}")
    
    print("\n🔄 Testing concurrent requests...")
    asyncio.run(make_concurrent_requests())


if __name__ == "__main__":
    print("🦅 Eagle Bank API Demo")
    print("=" * 50)
    
    # Run main demo
    asyncio.run(main())
    
    # Demonstrate concurrency
    demonstrate_concurrent_requests()
    
    print("\n✅ Demo completed!")
    print("\nTo run this demo with a real API:")
    print("1. Start the API: uvicorn app.main:app --reload")
    print("2. Set up Keycloak authentication")
    print("3. Replace mock token with real JWT token")
    print("4. Run this script: python examples/api_demo.py")
