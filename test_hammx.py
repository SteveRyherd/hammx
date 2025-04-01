import pytest
import respx
import httpx
from hammx import Hammx


@pytest.mark.asyncio
async def test_methods():
    """Test all HTTP methods work correctly"""
    with respx.mock:
        base_url = "http://localhost:8000"
        path = "/sample/path/to/resource"
        url = base_url + path
        
        for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            route = respx.route(method=method, url=url)
            route.mock(return_value=httpx.Response(200))
            
            client = Hammx(base_url)
            request_method = getattr(client, method)
            resp = await request_method('sample', 'path', 'to', 'resource')
            
            assert resp.status_code == 200
            assert route.called
            
            # Verify the actual request method and path
            request = route.calls[0][0]
            assert request.method == method
            assert request.url.path == path
            
            await client.aclose()


@pytest.mark.asyncio
async def test_urls():
    """Test various URL chaining combinations"""
    with respx.mock:
        base_url = "http://localhost:8000"
        path = "/sample/path/to/resource"
        url = base_url + path
        
        route = respx.route(method="GET", url=url)
        route.mock(return_value=httpx.Response(200))
        
        client = Hammx(base_url)
        combs = [
            client.sample.path.to.resource,
            client('sample').path('to').resource,
            client('sample', 'path', 'to', 'resource'),
            client('sample')('path')('to')('resource'),
            client.sample('path')('to', 'resource'),
            client('sample', 'path',).to.resource
        ]

        for comb in combs:
            assert str(comb) == url
            resp = await comb.GET()
            assert resp.status_code == 200
            
            # Verify the path is correct
            request = route.calls[-1][0]  # Get the latest call
            assert request.url.path == path
        
        await client.aclose()


@pytest.mark.asyncio
async def test_append_slash_option():
    """Test that append_slash option works"""
    with respx.mock:
        base_url = "http://localhost:8000"
        path = "/sample/path/to/resource/"
        url = base_url + path
        
        route = respx.route(method="GET", url=url)
        route.mock(return_value=httpx.Response(200))
        
        client = Hammx(base_url, append_slash=True)
        resp = await client.sample.path.to.resource.GET()
        assert resp.status_code == 200
        
        # Verify the path includes trailing slash
        request = route.calls[0][0]
        assert request.url.path == path
        
        await client.aclose()


@pytest.mark.asyncio
async def test_inheritance():
    """Test class inheritance works properly"""
    with respx.mock:
        base_url = "http://localhost:8000"
        path = "/sample/path/to/resource"
        url = base_url + path
        
        route = respx.route(method="GET", url=url)
        route.mock(return_value=httpx.Response(200))
        
        # Define flag to track if custom _url was called
        called = False
        
        class CustomHammx(Hammx):
            def __init__(self, name=None, parent=None, **kwargs):
                if 'testing' in kwargs:
                    self.testing = kwargs.pop('testing')
                super(CustomHammx, self).__init__(name, parent, **kwargs)

            def _url(self, *args):
                nonlocal called
                assert isinstance(self.testing, bool)
                called = True
                return super(CustomHammx, self)._url(*args)

        client = CustomHammx(base_url, testing=True)
        resp = await client.sample.path.to.resource.GET()
        
        assert resp.status_code == 200
        assert called is True
        
        # Verify the request path
        request = route.calls[0][0]
        assert request.url.path == path
        
        await client.aclose()


@pytest.mark.asyncio
async def test_session():
    """Test session maintains headers and authentication"""
    with respx.mock:
        base_url = "http://localhost:8000"
        path = "/sample/path/to/resource"
        url = base_url + path
        
        route = respx.route(method="GET", url=url)
        route.mock(return_value=httpx.Response(200))
        
        ACCEPT_HEADER = 'application/json'
        kwargs = {
            'headers': {'Accept': ACCEPT_HEADER},
            'auth': ('foo', 'bar'),
        }
        client = Hammx(base_url, **kwargs)
        
        # First request
        await client.sample.path.to.resource.GET()
        request = route.calls[0][0]
        assert 'accept' in request.headers
        assert request.headers.get('accept') == ACCEPT_HEADER
        assert 'authorization' in request.headers
        assert 'user-agent' in request.headers  # Check for user agent header
        
        # Second request - verify session is maintained
        await client.sample.path.to.resource.GET()
        request = route.calls[1][0]
        assert 'accept' in request.headers
        assert request.headers.get('accept') == ACCEPT_HEADER
        assert 'authorization' in request.headers
        assert 'user-agent' in request.headers
        
        await client.aclose()


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager functionality"""
    with respx.mock:
        base_url = "http://localhost:8000"
        path = "/sample/path/to/resource"
        url = base_url + path
        
        route = respx.route(method="GET", url=url)
        route.mock(return_value=httpx.Response(200))
        
        async with Hammx(base_url) as client:
            resp = await client.sample.path.to.resource.GET()
            assert resp.status_code == 200
            
            # Verify the request path
            request = route.calls[0][0]
            assert request.url.path == path