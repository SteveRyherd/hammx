::

 __   __     ___     __    __   __    __   _    _ 
|  |_|  |   / _ \   |   \/   | |   \/   | |  \/  |
 )  _  (   ) (_) (   )      (   )      (   )    ( 
|__| |__| |__) (__| (__/\/\__) (__/\/\__) |__/\__|
                                     
                                     
                                     
Hammx is a fun module lets you deal with rest APIs by converting them into dead simple programmatic APIs.
It uses the popular ``httpx`` module to provide full-fledged async rest experience.

It is a fork of the original ``hammock`` library, but with async capabilities.

Proof
-----

Let's play with github::

    >>> import asyncio
    >>> from hammx import Hammx as Github

    >>> async def main():
    ...     # Let's create the first chain of hammx using base api url
    ...     github = Github('https://api.github.com')
    ...
    ...     # Ok, let the magic happens, ask github for hammx watchers
    ...     resp = await github.repos('steveryherd', 'hammx').watchers.GET()
    ...
    ...     # now you're ready to take a rest for the rest the of code :)
    ...     for watcher in resp.json(): print(watcher.get('login'))
    ...
    ...     # Don't forget to close the client when done
    ...     await github.aclose()
    ...
    >>> asyncio.run(main())
    steveryherd
    ...
    ..
    .

Not convinced? This is also how you can watch this project to see its future capabilities::

    >>> async def watch_project():
    ...     github = Github('https://api.github.com')
    ...     response = await github.user.watched('steveryherd', 'hammx').PUT(
    ...         auth=('<user>', '<pass>'),
    ...         headers={'content-length': '0'}
    ...     )
    ...     print(response)
    ...     await github.aclose()
    ... 
    >>> asyncio.run(watch_project())
    <Response [204]>

Using as a context manager (recommended)::

    >>> async def using_context_manager():
    ...     # Context managers automatically close the client when the block exits
    ...     async with Github('https://api.github.com') as github:
    ...         resp = await github.repos('steveryherd', 'hammx').watchers.GET()
    ...         for watcher in resp.json():
    ...             print(watcher.get('login'))
    ... 
    >>> asyncio.run(using_context_manager())
    
    # You can also create the context manager first and use it later
    >>> github_api = Github('https://api.github.com')
    >>> async def use_prepared_context():
    ...     async with github_api as client:
    ...         # Client is ready to use and will be automatically closed
    ...         return await client.repos('steveryherd', 'hammx').stargazers.GET()
    ... 
    >>> asyncio.run(use_prepared_context())

How?
----

``Hammx`` is a thin wrapper over ``httpx`` module, you are still with it. But it simplifies your life
by letting you place your variables into URLs naturally by using object notation way. Also you can wrap some
url fragments into objects for improving code re-use. For example;


Take these;

    >>> base_url = 'https://api.github.com'
    >>> user = 'steveryherd'
    >>> repo = 'hammx'

Without ``Hammx``, using pure ``httpx`` module you have to generate your urls by hand using string formatting::

    >>> await httpx.AsyncClient().get("%s/repos/%s/%s/watchers" % (base_url, user, repo))

With ``Hammx``, you don't have to deal with string formatting. You can wrap ``base_url`` for code reuse
and easily map variables to urls. This is just cleaner::

    >>> github = hammx.Hammx(base_url)
    >>> await github.repos(user, repo).watchers.GET()
    >>> await github.user.watched(user, repo).PUT()  # reuse!

Install
-------

The best way to install ``Hammx`` is using pypi repositories via ``pip``::

    $ pip install hammx

Recommended Usage
----------------

Using the async context manager pattern is recommended for proper resource cleanup::

    async with hammx.Hammx('https://api.example.com') as client:
        response = await client.users.GET()
        # Process response here
    # Client is automatically closed when leaving the context

If you need to use the client without a context manager, always close it explicitly::

    client = hammx.Hammx('https://api.example.com')
    try:
        response = await client.users.GET()
        # Process response
    finally:
        # Always close the client to release resources
        await client.aclose()

Documentation
-------------

``Hammx`` is a magical, polymorphic(!), fun and simple class which helps you generate RESTful urls
and lets you request them using ``httpx`` module in an easy and slick way.

Below the all phrases build the same url of 'http://localhost:8000/users/foo/posts/bar/comments'.
Note that all of them are valid but some of them are nonsense in their belonging context::

    >>> import hammx
    >>> api = hammx.Hammx('http://localhost:8000')
    >>> # All these build the same URL:
    >>> api.users('foo').posts('bar').comments
    >>> api.users.foo.posts('bar').comments
    >>> api.users.foo.posts.bar.comments
    >>> api.users('foo', 'posts', 'comments')
    >>> api('users')('foo', 'posts')('bar', 'comments')
    >>> # Any other combinations ...

``Hammx`` class instance provides ``httpx`` module's all http methods binded on itself as uppercased version
while dropping the first arg ``url`` in replacement of ``*args`` to let you to continue appending url components.

Also you can continue providing any keyword argument for corresponding http verb method of ``httpx`` module::

    await Hammx.[GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE](*args, **kwargs)

Return type is the same ``Response`` object ``httpx`` module provides.

Here is some more real world applicable example which uses twitter api::

    >>> import asyncio
    >>> import hammx
    >>> async def get_tweets():
    ...     twitter = hammx.Hammx('https://api.twitter.com/1.1')
    ...     resp = await twitter.statuses('user_timeline.json').GET(
    ...         params={'screen_name':'steveryherd', 'count':'10'}
    ...     )
    ...     tweets = resp.json()
    ...     for tweet in tweets: print(tweet.get('text'))
    ...     await twitter.aclose()
    ... 
    >>> asyncio.run(get_tweets())
    my tweets
    ...
    ..
    .

You might also want to use sessions. Let's take a look at the JIRA example below which maintains basic
auth credentials through several http requests::

    >>> import asyncio
    >>> import hammx

    >>> async def jira_example():
    ...     # You can configure a session by providing keyword args to `Hammx` constructor
    ...     # This sample below shows the use of auth credentials through several requests
    ...     jira = hammx.Hammx('https://jira.atlassian.com/rest/api/latest', 
    ...                         auth=('<user>', '<pass>'))
    ...
    ...     my_issue = 'JRA-9'
    ...
    ...     # Let's get a jira issue. No auth credentials provided explicitly since parent
    ...     # hammx already has a httpx.AsyncClient session configured.
    ...     issue = await jira.issue(my_issue).GET()
    ...
    ...     # Now watch the issue again using with the same session
    ...     watched = await jira.issue(my_issue).watchers.POST(params={'name': '<user>'})
    ...
    ...     print(watched)
    ...     
    ...     # Close the client when done
    ...     await jira.aclose()
    ...
    >>> asyncio.run(jira_example())

Also keep in mind that if you want a trailing slash at the end of URLs generated by ``Hammx``
you should pass ``append_slash`` kewyword argument as ``True`` while constructing ``Hammx``.
For example::

    >>> api = hammx.Hammx('http://localhost:8000', append_slash=True)
    >>> print(api.foo.bar)  # Note that trailing slash
    'http://localhost:8000/foo/bar/'

Contributors
------------

* Original Hammock by Kadir Pekel (@kadirpekel)
* Original contributors to Hammock:
    * Miguel Araujo (@maraujop)
    * Michele Lacchia (@rubik)
* Contributions to Hammx:
    * Steve Ryherd (@steveryherd)

Licence
-------

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
