"""
Initialize the `api` package.

Having an empty __init__.py file tells Python that this directory is a
package. Without it, certain tools and runtime environments may fail
to import modules from `api`, resulting in errors such as
`ModuleNotFoundError: No module named 'api'`. By including this file,
we ensure that the backend code can be imported consistently during
migration jobs and at runtime.
"""
