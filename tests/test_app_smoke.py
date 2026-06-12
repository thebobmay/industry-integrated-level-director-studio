"""Smoke test for the Gradio app.

Building the Blocks exercises all the component construction and event wiring
without launching a server or constructing any service (services are built lazily
per engine), so this needs no API key and no models.
"""

from __future__ import annotations

import gradio as gr

import app


def test_build_app_constructs_blocks():
    demo = app.build_app()
    assert isinstance(demo, gr.Blocks)


def test_engine_services_are_lazy():
    # Building the app must not eagerly construct any service.
    app._services.clear()
    app.build_app()
    assert app._services == {}
