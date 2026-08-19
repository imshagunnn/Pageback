"""
PageBack AI layer.

Django views must not call an LLM vendor directly. They call services, and
services call this package. Swap providers by implementing AIProvider.
"""
