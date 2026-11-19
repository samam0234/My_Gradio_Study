"""이 학습 서비스가 지키는 게시판 API의 OpenAPI 일부."""

from __future__ import annotations


def board_openapi() -> dict:
    error = {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "fields": {"type": "object"},
                    "requestId": {"type": "string"},
                },
            }
        },
    }
    return {
        "openapi": "3.0.3",
        "info": {"title": "Board API", "version": "1.0.0"},
        "paths": {
            "/health": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/api/posts": {
                "get": {
                    "parameters": [
                        {"name": "q", "in": "query", "schema": {"type": "string"}},
                        {"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "maximum": 50}},
                        {"name": "sort", "in": "query", "schema": {"type": "string"}},
                    ],
                    "responses": {"200": {"description": "data + meta"}, "400": {"description": "error", "content": {"application/json": {"schema": error}}}},
                },
                "post": {"responses": {"201": {"description": "created"}, "400": {"description": "validation"}, "401": {"description": "login"}}},
            },
            "/api/posts/{id}": {
                "get": {"responses": {"200": {"description": "detail"}, "404": {"description": "missing"}}},
                "patch": {"responses": {"200": {"description": "updated"}, "403": {"description": "not author"}}},
                "delete": {"responses": {"204": {"description": "deleted"}}},
            },
        },
    }
