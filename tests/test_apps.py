import importlib

import gradio as gr

MODULES = [
    "apps.env_demo",
    "apps.hello",
    "apps.blocks_layout",
    "apps.state_demo",
    "apps.routing_demo",
    "apps.form_demo",
    "apps.midpoint_app",
    "apps.db_demo",
    "apps.theme_demo",
    "apps.external_demo",
    "apps.api_demo",
    "apps.perf_demo",
    "apps.ops_demo",
    "apps.realtime_demo",
    "apps.ai_demo",
    "apps.project_app",
]


def test_every_screen_builds():
    for name in MODULES:
        module = importlib.import_module(name)
        demo = module.build()
        assert isinstance(demo, gr.Blocks)


def test_launch_exposes_share_and_mcp():
    import inspect

    signature = inspect.signature(gr.Blocks.launch)
    assert "share" in signature.parameters
    assert "mcp_server" in signature.parameters
    assert "theme" in signature.parameters
