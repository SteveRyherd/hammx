"""
Middleware examples for Hammx

This module demonstrates how to add middleware-like functionality
to Hammx clients without modifying the core implementation.
"""
import time
import asyncio
import json
from functools import wraps
from hammx import Hammx


async def with_logging(client):
    """Add request/response logging to any Hammx client.
    
    This middleware logs:
    - Request method and URL
    - Response status code
    - Request duration
    
    Example:
        client = Hammx('https://api.example.com')
        logged_client = await with_logging(client)
        response = await logged_client.users.GET()
    """
    original_request = client._request
    
    @wraps(original_request)
    async def logged_request(method, *args, **kwargs):
        url = client._url(*args)
        print(f"→ {method} {url}")
        start = time.time()
        response = await original_request(method, *args, **kwargs)
        duration = time.time() - start
        print(f"← {response.status_code} ({duration:.2f}s)")
        return response
        
    client._request = logged_request
    return client


async def with_headers(client, headers):
    """Add custom headers to all requests made by a Hammx client.
    
    Example:
        client = Hammx('https://api.example.com')
        client_with_headers = await with_headers(client, {
            'X-API-Version': '2.0',
            'User-Agent': 'Hammx/0.1.0'
        })
    """
    original_request = client._request
    
    @wraps(original_request)
    async def headers_request(method, *args, **kwargs):
        # Create headers dict if it doesn't exist
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
            
        # Add our custom headers
        for key, value in headers.items():
            if key not in kwargs['headers']:
                kwargs['headers'][key] = value
                
        return await original_request(method, *args, **kwargs)
        
    client._request = headers_request
    return client


async def with_retry(client, max_retries=3, retry_codes=(500, 502, 503, 504), backoff_factor=0.5):
    """Add retry functionality to a Hammx client.
    
    On specified status codes, will retry the request up to max_retries times
    with exponential backoff.
    
    Example:
        client = Hammx('https://api.example.com')
        retry_client = await with_retry(client, max_retries=5)
    """
    original_request = client._request
    
    @wraps(original_request)
    async def retry_request(method, *args, **kwargs):
        retries = 0
        while True:
            response = await original_request(method, *args, **kwargs)
            
            if response.status_code not in retry_codes or retries >= max_retries:
                return response
                
            # Exponential backoff with jitter
            delay = backoff_factor * (2 ** retries)
            print(f"Request failed with status {response.status_code}. "
                  f"Retrying in {delay:.2f}s...")
            await asyncio.sleep(delay)
            retries += 1
        
    client._request = retry_request
    return client


# Demonstrate composing middleware
async def demo():
    # Create a base client
    client = Hammx('https://httpbin.org')
    
    # Apply middleware (order matters!)
    client = await with_retry(client)
    client = await with_headers(client, {'X-Demo': 'True'})
    client = await with_logging(client)
    
    try:
        # Make a request
        response = await client.get.GET()
        data = response.json()
        print(f"Headers sent: {json.dumps(data.get('headers', {}), indent=2)}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(demo())
