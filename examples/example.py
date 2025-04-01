import asyncio
from hammx import Hammx as H

# Using context manager (recommended)
async def with_context_manager():
    async with H('https://httpbin.org') as api:
        response = await api.get.GET()
        print(f"Context Manager Status: {response.status_code}")

# Using without context manager
async def main():
    # Create a simple example using httpbin.org which echoes requests
    api = H('https://httpbin.org')
    
    # Make a GET request
    response = await api.get.GET()
    print(f"GET Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Make a POST request with some data
    response = await api.post.POST(json={"name": "test", "value": 123})
    print(f"POST Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Don't forget to close the client
    await api.aclose()

if __name__ == "__main__":
    # Run the async functions
    asyncio.run(main())
    asyncio.run(with_context_manager())
