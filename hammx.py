import httpx
import copy


class Hammx(object):
    """Chainable, magical class helps you make async requests to RESTful services"""

    HTTP_METHODS = ['get', 'options', 'head', 'post', 'put', 'patch', 'delete']

    def __init__(self, name=None, parent=None, append_slash=False, **kwargs):
        """Constructor

        Arguments:
            name -- name of node
            parent -- parent node for chaining
            append_slash -- flag if you want a trailing slash in urls
            **kwargs -- `httpx.AsyncClient` be initiated with if any available
        """
        self._name = name
        self._parent = parent
        self._append_slash = append_slash
        self._session = httpx.AsyncClient(**kwargs)

    def _spawn(self, name):
        """Returns a shallow copy of current `Hammx` instance as nested child

        Arguments:
            name -- name of child
        """
        child = copy.copy(self)
        child._name = name
        child._parent = self
        return child

    def __getattr__(self, name):
        """Here comes some magic. Any absent attribute typed within class
        falls here and return a new child `Hammx` instance in the chain.
        """
        # Ignore specials (Otherwise shallow copying causes infinite loops)
        if name.startswith('__'):
            raise AttributeError(name)
        return self._spawn(name)

    def __iter__(self):
        """Iterator implementation which iterates over `Hammx` chain."""
        current = self
        while current:
            if current._name:
                yield current
            current = current._parent

    def _chain(self, *args):
        """This method converts args into chained Hammx instances

        Arguments:
            *args -- array of string representable objects
        """
        chain = self
        for arg in args:
            chain = chain._spawn(str(arg))
        return chain

    async def aclose(self):
        """Closes session if exists"""
        if self._session:
            await self._session.aclose()

    def __call__(self, *args):
        """Here comes second magic. If any `Hammx` instance called it
        returns a new child `Hammx` instance in the chain
        """
        return self._chain(*args)

    def _url(self, *args):
        """Converts current `Hammx` chain into a url string

        Arguments:
            *args -- extra url path components to tail
        """
        path_comps = [mock._name for mock in self._chain(*args)]
        url = "/".join(reversed(path_comps))
        if self._append_slash:
            url = url + "/"
        return url

    def __repr__(self):
        """String representation of current `Hammx` chain"""
        return self._url()

    async def _request(self, method, *args, **kwargs):
        """
        Makes the HTTP request using httpx module
        """
        return await self._session.request(method, self._url(*args), **kwargs)

    async def __aenter__(self):
        """Support for async context manager protocol"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context manager protocol"""
        await self.aclose()


def bind_method(method):
    """Bind `httpx` module HTTP verbs to `Hammx` class as
    async methods."""
    async def aux(hammx, *args, **kwargs):
        return await hammx._request(method, *args, **kwargs)
    return aux

for method in Hammx.HTTP_METHODS:
    setattr(Hammx, method.upper(), bind_method(method))
