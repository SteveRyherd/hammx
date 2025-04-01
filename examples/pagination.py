"""
Pagination helpers for Hammx

This module demonstrates how to implement pagination patterns
with Hammx to simplify working with paginated APIs.
"""
import asyncio
from typing import AsyncIterator, Dict, List, Any, Optional
from hammx import Hammx


async def iter_pages(resource, params: Optional[Dict] = None) -> AsyncIterator[Dict]:
    """Iterate through all pages of a paginated API using page numbers.
    
    This function assumes the API follows these conventions:
    - Uses a 'page' query parameter for pagination
    - Returns an empty array/object when there are no more pages
    
    Example:
        client = Hammx('https://api.example.com')
        async for item in iter_pages(client.users, {'limit': 100}):
            print(item['name'])
    """
    params = params or {}
    page = 1
    
    while True:
        # Update the page parameter
        current_params = {**params, 'page': page}
        
        # Make the request
        response = await resource.GET(params=current_params)
        data = response.json()
        
        # Check if we've reached the end (empty response)
        if not data or (isinstance(data, list) and len(data) == 0):
            break
            
        # For object responses with items/results/data key
        if isinstance(data, dict):
            # Try common keys for paginated results
            for key in ['items', 'results', 'data', 'records']:
                if key in data:
                    items = data[key]
                    if not items:
                        return
                    for item in items:
                        yield item
                    break
            else:
                # If no pagination key found, yield the entire object
                yield data
        # For array responses, yield each item
        elif isinstance(data, list):
            for item in data:
                yield item
                
        # Move to the next page
        page += 1


async def iter_offset(resource, params: Optional[Dict] = None, 
                      limit: int = 100) -> AsyncIterator[Dict]:
    """Iterate through all pages of an API using offset/limit pagination.
    
    This function assumes the API follows these conventions:
    - Uses 'offset' and 'limit' query parameters for pagination
    - Returns an empty array/object when there are no more results
    
    Example:
        client = Hammx('https://api.example.com')
        async for item in iter_offset(client.users, limit=50):
            print(item['name'])
    """
    params = params or {}
    offset = 0
    
    while True:
        # Update the pagination parameters
        current_params = {**params, 'offset': offset, 'limit': limit}
        
        # Make the request
        response = await resource.GET(params=current_params)
        data = response.json()
        
        # Handle various response formats
        items = []
        if isinstance(data, dict):
            # Try common keys for paginated results
            for key in ['items', 'results', 'data', 'records']:
                if key in data:
                    items = data[key]
                    break
        elif isinstance(data, list):
            items = data
            
        # No more results
        if not items:
            break
            
        # Yield each item
        for item in items:
            yield item
            
        # If we received fewer items than the limit, we've reached the end
        if len(items) < limit:
            break
            
        # Move to the next page
        offset += limit


async def iter_cursor(resource, params: Optional[Dict] = None, 
                     cursor_param: str = 'cursor', 
                     cursor_field: str = 'next_cursor') -> AsyncIterator[Dict]:
    """Iterate through all pages of an API using cursor-based pagination.
    
    This function assumes the API follows these conventions:
    - Takes a cursor parameter to get the next page
    - Returns a cursor field in the response for the next page
    - Returns a null/empty cursor when there are no more pages
    
    Example:
        client = Hammx('https://api.example.com')
        async for item in iter_cursor(client.events):
            print(item['name'])
    """
    params = params or {}
    cursor = None
    
    while True:
        # Update the cursor parameter if we have one
        current_params = {**params}
        if cursor:
            current_params[cursor_param] = cursor
        
        # Make the request
        response = await resource.GET(params=current_params)
        data = response.json()
        
        # Extract items based on response format
        items = []
        if isinstance(data, dict):
            # Try to find the cursor for the next page
            next_cursor = data.get(cursor_field)
            
            # Extract items from common response formats
            for key in ['items', 'results', 'data', 'records']:
                if key in data:
                    items = data[key]
                    break
            else:
                # Handle special case: response is metadata + items
                potential_items = {k: v for k, v in data.items() 
                                if k != cursor_field and isinstance(v, list)}
                if len(potential_items) == 1:
                    items = list(potential_items.values())[0]
        elif isinstance(data, list):
            items = data
            next_cursor = None  # No cursor in array responses
            
        # Yield each item
        for item in items:
            yield item
            
        # Stop if no cursor or no items
        if not next_cursor or not items:
            break
            
        # Update cursor for next page
        cursor = next_cursor


# Demonstrate the pagination helpers
async def demo():
    # Create a client
    client = Hammx('https://jsonplaceholder.typicode.com')
    
    try:
        # This API returns arrays, so we'll use a limit to paginate
        # Normally it would return all 100 posts at once
        print("\nFetching posts with offset pagination (10 at a time):")
        count = 0
        async for post in iter_offset(client.posts, limit=10):
            print(f"Post {post['id']}: {post['title'][:30]}...")
            count += 1
            # Just show first 5 for demo
            if count >= 5:
                print(f"... and {95} more posts")
                break
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(demo())
