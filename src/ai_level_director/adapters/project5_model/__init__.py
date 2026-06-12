"""Vendored Project 5 model architecture and tokenizer.

``model.py`` and ``tokenizer.py`` are verbatim copies of the Project 5 generative
project source. They are vendored unchanged so the trained ``level_generator.pt``
checkpoint loads against the exact architecture and tile vocabulary it was trained
with. The Project 5 generation and sampling code lived in that project's notebook,
not its source, so the autoregressive sampling is implemented in the adapter.
"""
