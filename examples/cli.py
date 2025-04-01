"""
Simple CLI tool for Hammx

This demonstrates how to build a command-line interface
for making API requests with Hammx.
"""
import sys
import json
import asyncio
import argparse
from hammx import Hammx


async def make_request(method, url, path=None, params=None, data=None, 
                       headers=None, auth=None):
    """Make a request using Hammx."""
    # Create the Hammx client
    client = Hammx(url)
    
    try:
        # Build the request path if provided
        endpoint = client
        if path:
            # Split the path by '/' and chain them
            parts = path.strip('/').split('/')
            for part in parts:
                endpoint = getattr(endpoint, part)
        
        # Get the appropriate HTTP method
        http_method = getattr(endpoint, method.upper())
        
        # Build request kwargs
        kwargs = {}
        if params:
            kwargs['params'] = params
        if data:
            kwargs['json'] = data
        if headers:
            kwargs['headers'] = headers
        if auth:
            if ':' in auth:
                username, password = auth.split(':', 1)
                kwargs['auth'] = (username, password)
            else:
                kwargs['headers'] = kwargs.get('headers', {})
                kwargs['headers']['Authorization'] = f"Bearer {auth}"
        
        # Make the request
        response = await http_method(**kwargs)
        
        # Process the response
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                return response.status_code, response.json()
            except:
                pass
        
        return response.status_code, response.text
    finally:
        await client.aclose()


async def interactive_mode():
    """Run an interactive session with the Hammx CLI."""
    base_url = None
    current_path = []
    
    print("Hammx Interactive CLI")
    print("--------------------")
    print("Commands:")
    print("  base URL          - Set the base URL")
    print("  path SEGMENT      - Add a path segment")
    print("  params KEY=VALUE  - Add query parameters")
    print("  headers KEY=VALUE - Add HTTP headers")
    print("  auth USER:PASS    - Add basic auth")
    print("  auth TOKEN        - Add bearer token auth")
    print("  get, post, put, patch, delete - Execute the request")
    print("  reset            - Reset the current request")
    print("  exit             - Exit the CLI")
    print()
    
    params = {}
    headers = {}
    auth = None
    
    while True:
        # Show current state
        current_url = f"{base_url}/{'/'.join(current_path)}" if base_url else "No URL set"
        prompt = f"hammx [{current_url}]> "
        
        # Get command
        try:
            cmd = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        
        if not cmd:
            continue
            
        # Parse command
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Process command
        if command == "exit":
            break
        elif command == "base":
            base_url = args
            current_path = []
        elif command == "path":
            if not base_url:
                print("Set a base URL first with 'base URL'")
                continue
            # Add path segments
            segments = args.strip('/').split('/')
            current_path.extend(segments)
        elif command == "params":
            if "=" not in args:
                print("Invalid format. Use: params key=value")
                continue
            key, value = args.split('=', 1)
            params[key.strip()] = value.strip()
        elif command == "headers":
            if "=" not in args:
                print("Invalid format. Use: headers key=value")
                continue
            key, value = args.split('=', 1)
            headers[key.strip()] = value.strip()
        elif command == "auth":
            auth = args
        elif command == "reset":
            current_path = []
            params = {}
            headers = {}
            auth = None
            print("Request reset")
        elif command in ("get", "post", "put", "patch", "delete"):
            if not base_url:
                print("Set a base URL first with 'base URL'")
                continue
                
            # Make the request
            try:
                path = '/'.join(current_path) if current_path else None
                data = None
                if command in ("post", "put", "patch") and args:
                    try:
                        data = json.loads(args)
                    except json.JSONDecodeError:
                        print("Invalid JSON data")
                        continue
                
                status, response = await make_request(
                    command, base_url, path, params, data, headers, auth
                )
                
                # Pretty-print the response
                print(f"\nStatus: {status}")
                if isinstance(response, dict) or isinstance(response, list):
                    print(json.dumps(response, indent=2))
                else:
                    print(response)
                print()
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Unknown command: {command}")


async def main():
    """Parse command line arguments and execute requests."""
    parser = argparse.ArgumentParser(description="Command-line HTTP client using Hammx")
    parser.add_argument("method", help="HTTP method (GET, POST, PUT, PATCH, DELETE)")
    parser.add_argument("url", help="URL to request (base URL or full URL)")
    parser.add_argument("--path", "-p", help="API path to append to the base URL")
    parser.add_argument("--params", "-q", action="append", help="Query parameters in key=value format")
    parser.add_argument("--data", "-d", help="JSON data for POST/PUT/PATCH requests")
    parser.add_argument("--headers", "-H", action="append", help="HTTP headers in key=value format")
    parser.add_argument("--auth", "-a", help="Authentication (username:password or token)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        await interactive_mode()
        return
    
    # Process parameters
    params = {}
    if args.params:
        for param in args.params:
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
    
    # Process headers
    headers = {}
    if args.headers:
        for header in args.headers:
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key] = value
    
    # Process JSON data
    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON data: {args.data}")
            return
    
    # Make the request
    try:
        status, response = await make_request(
            args.method, args.url, args.path, params, data, headers, args.auth
        )
        
        # Output the response
        print(f"Status: {status}")
        if isinstance(response, (dict, list)):
            print(json.dumps(response, indent=2))
        else:
            print(response)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
