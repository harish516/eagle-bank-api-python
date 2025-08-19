"""Example demonstrating service-to-service communication with authentication."""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional


class ServiceAuthentication:
    """Handle service-to-service authentication."""
    
    def __init__(self, keycloak_url: str, realm: str, client_id: str, client_secret: str):
        self.keycloak_url = keycloak_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
    
    async def get_service_token(self) -> str:
        """Get service-to-service authentication token."""
        import time
        
        # Check if current token is still valid
        if self.token and self.token_expires_at and time.time() < self.token_expires_at - 60:
            return self.token
        
        # Request new token using client credentials flow
        token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data["access_token"]
            self.token_expires_at = time.time() + token_data.get("expires_in", 300)
            
            return self.token


class BankingService:
    """Example external banking service that calls Eagle Bank API."""
    
    def __init__(self, api_base_url: str, auth: ServiceAuthentication):
        self.api_base_url = api_base_url
        self.auth = auth
    
    async def _make_authenticated_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> httpx.Response:
        """Make authenticated request to Eagle Bank API."""
        token = await self.auth.get_service_token()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-Type"] = "application/json"
        kwargs["headers"] = headers
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, f"{self.api_base_url}{endpoint}", **kwargs)
            return response
    
    async def create_customer_account(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete customer setup (user + account)."""
        print(f"🏭 Service: Creating customer account for {customer_data['email']}")
        
        try:
            # Step 1: Create user
            user_response = await self._make_authenticated_request(
                "POST", "/v1/users", json=customer_data
            )
            
            if user_response.status_code != 201:
                raise Exception(f"Failed to create user: {user_response.text}")
            
            user = user_response.json()
            print(f"✅ User created: {user['id']}")
            
            # Step 2: Create account
            account_data = {
                "name": f"{customer_data['name']}'s Account",
                "account_type": "personal"
            }
            
            account_response = await self._make_authenticated_request(
                "POST", "/v1/accounts", json=account_data
            )
            
            if account_response.status_code != 201:
                raise Exception(f"Failed to create account: {account_response.text}")
            
            account = account_response.json()
            print(f"✅ Account created: {account['account_number']}")
            
            return {
                "user": user,
                "account": account,
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Service error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_bulk_transactions(
        self, 
        account_number: str, 
        transactions: list
    ) -> Dict[str, Any]:
        """Process multiple transactions for an account."""
        print(f"🏭 Service: Processing {len(transactions)} transactions")
        
        results = []
        
        for i, tx_data in enumerate(transactions):
            try:
                response = await self._make_authenticated_request(
                    "POST", 
                    f"/v1/accounts/{account_number}/transactions",
                    json=tx_data
                )
                
                if response.status_code == 201:
                    transaction = response.json()
                    results.append({
                        "index": i,
                        "status": "success",
                        "transaction_id": transaction["id"]
                    })
                    print(f"✅ Transaction {i+1}: £{tx_data['amount']} {tx_data['type']}")
                else:
                    results.append({
                        "index": i,
                        "status": "error",
                        "message": response.text
                    })
                    print(f"❌ Transaction {i+1} failed: {response.text}")
                
            except Exception as e:
                results.append({
                    "index": i,
                    "status": "error", 
                    "message": str(e)
                })
                print(f"❌ Transaction {i+1} error: {e}")
        
        successful = len([r for r in results if r["status"] == "success"])
        print(f"📊 Processed: {successful}/{len(transactions)} successful")
        
        return {
            "total": len(transactions),
            "successful": successful,
            "failed": len(transactions) - successful,
            "results": results
        }
    
    async def get_account_summary(self, account_number: str) -> Dict[str, Any]:
        """Get comprehensive account summary."""
        print(f"🏭 Service: Getting account summary for {account_number}")
        
        try:
            # Get account details and transactions concurrently
            account_task = self._make_authenticated_request(
                "GET", f"/v1/accounts/{account_number}"
            )
            transactions_task = self._make_authenticated_request(
                "GET", f"/v1/accounts/{account_number}/transactions"
            )
            
            account_response, transactions_response = await asyncio.gather(
                account_task, transactions_task
            )
            
            if account_response.status_code != 200:
                raise Exception(f"Failed to get account: {account_response.text}")
            
            if transactions_response.status_code != 200:
                raise Exception(f"Failed to get transactions: {transactions_response.text}")
            
            account = account_response.json()
            transactions = transactions_response.json()["transactions"]
            
            # Calculate summary statistics
            total_deposits = sum(
                tx["amount"] for tx in transactions 
                if tx["type"] == "deposit"
            )
            total_withdrawals = sum(
                tx["amount"] for tx in transactions 
                if tx["type"] == "withdrawal"
            )
            
            summary = {
                "account": account,
                "transaction_count": len(transactions),
                "total_deposits": total_deposits,
                "total_withdrawals": total_withdrawals,
                "current_balance": account["balance"],
                "recent_transactions": transactions[:5]  # Last 5 transactions
            }
            
            print(f"✅ Summary generated for account {account_number}")
            return summary
            
        except Exception as e:
            print(f"❌ Failed to get account summary: {e}")
            return {"status": "error", "message": str(e)}


async def demonstrate_service_integration():
    """Demonstrate service-to-service integration."""
    
    print("🔗 Eagle Bank Service-to-Service Integration Demo")
    print("=" * 60)
    
    # Mock authentication (in real scenario, use actual Keycloak credentials)
    auth = ServiceAuthentication(
        keycloak_url="http://localhost:8080",
        realm="eagle-bank",
        client_id="eagle-bank-service",
        client_secret="service-secret"
    )
    
    # Initialize banking service
    banking_service = BankingService("http://localhost:8000", auth)
    
    # Customer data
    customer_data = {
        "name": "Bob Wilson",
        "address": {
            "line1": "789 Pine Avenue",
            "town": "Birmingham",
            "county": "West Midlands",
            "postcode": "B1 1AA"
        },
        "phone_number": "+447700900789",
        "email": "bob.wilson@example.com"
    }
    
    # Sample transactions
    transactions = [
        {
            "amount": 1000.00,
            "currency": "GBP", 
            "type": "deposit",
            "reference": "Initial deposit"
        },
        {
            "amount": 50.00,
            "currency": "GBP",
            "type": "withdrawal",
            "reference": "ATM withdrawal"
        },
        {
            "amount": 200.00,
            "currency": "GBP",
            "type": "deposit", 
            "reference": "Salary"
        }
    ]
    
    try:
        # Step 1: Create customer account
        print("\n🎯 Step 1: Creating customer account...")
        result = await banking_service.create_customer_account(customer_data)
        
        if result["status"] != "success":
            print(f"❌ Failed to create customer: {result.get('message')}")
            return
        
        account_number = result["account"]["account_number"]
        
        # Step 2: Process transactions
        print(f"\n🎯 Step 2: Processing transactions for {account_number}...")
        tx_result = await banking_service.process_bulk_transactions(
            account_number, transactions
        )
        
        # Step 3: Get account summary
        print(f"\n🎯 Step 3: Getting account summary...")
        summary = await banking_service.get_account_summary(account_number)
        
        if "account" in summary:
            print(f"\n📈 Account Summary:")
            print(f"  Account: {summary['account']['account_number']}")
            print(f"  Balance: £{summary['current_balance']}")
            print(f"  Transactions: {summary['transaction_count']}")
            print(f"  Total Deposits: £{summary['total_deposits']}")
            print(f"  Total Withdrawals: £{summary['total_withdrawals']}")
        
        print("\n✅ Service integration demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def demonstrate_concurrent_service_calls():
    """Demonstrate concurrent service calls."""
    
    print("\n🚀 Concurrent Service Calls Demo")
    print("-" * 40)
    
    auth = ServiceAuthentication(
        keycloak_url="http://localhost:8080",
        realm="eagle-bank", 
        client_id="eagle-bank-service",
        client_secret="service-secret"
    )
    
    banking_service = BankingService("http://localhost:8000", auth)
    
    # Simulate multiple concurrent account summaries
    account_numbers = ["01234567", "01234568", "01234569"]
    
    print(f"🔄 Making concurrent calls for {len(account_numbers)} accounts...")
    
    start_time = asyncio.get_event_loop().time()
    
    # Make concurrent requests
    tasks = [
        banking_service.get_account_summary(acc_num) 
        for acc_num in account_numbers
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = asyncio.get_event_loop().time()
    
    print(f"⏱️  Completed {len(account_numbers)} calls in {end_time - start_time:.2f} seconds")
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  Account {account_numbers[i]}: ❌ {result}")
        else:
            status = "✅" if "account" in result else "❌"
            print(f"  Account {account_numbers[i]}: {status}")


if __name__ == "__main__":
    # Run the service integration demo
    asyncio.run(demonstrate_service_integration())
    
    # Run concurrent calls demo
    asyncio.run(demonstrate_concurrent_service_calls())
    
    print("\n" + "=" * 60)
    print("🔧 To run with real services:")
    print("1. Start Eagle Bank API")
    print("2. Configure Keycloak with service client")
    print("3. Update authentication credentials")
    print("4. Run: python examples/service_integration.py")
