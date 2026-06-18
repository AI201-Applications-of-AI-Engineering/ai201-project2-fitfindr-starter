"""Pytest bootstrap.

Lives at the project root so its directory is added to sys.path during
collection, letting test modules `import tools` / `import utils` regardless of
how pytest is invoked.
"""
