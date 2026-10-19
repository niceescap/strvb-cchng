"""Focused tests for the authenticated Open WebUI model listing route."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import httpx

_test_db = tempfile.TemporaryDirectory()
os.environ['TESTING'] = '1'
os.environ['DATABASE_URL'] = f"sqlite:///{Path(_test_db.name) / 'openwebui.db'}"
os.environ['SESSION_SECRET'] = 'openwebui-tests-session-secret-0123456789abcdef'
os.environ['DEMO_MODE'] = '1'

from fastapi.testclient import TestClient  # noqa: E402
import app as coach  # noqa: E402


MODELS = [
    {'id': f'model-{index:02}', 'name': f'Test model {index:02}', 'owned_by': 'fixture'}
    for index in range(21)
]


def client_for_authenticated_user():
    coach.app.dependency_overrides[coach.current_user] = lambda: object()
    return TestClient(coach.app)


def test_model_route_filters_allowlist_and_returns_only_id_and_name(monkeypatch):
    monkeypatch.setenv('OPENWEBUI_BASE_URL', 'https://openwebui.example.test/')
    monkeypatch.setenv('OPENWEBUI_API_KEY', 'test-only-secret')
    monkeypatch.setenv('OPENWEBUI_COACH_MODELS', ' model-03, model-17 ')
    request = httpx.Request('GET', 'https://openwebui.example.test/api/models')
    upstream_response = httpx.Response(200, json={'data': MODELS}, request=request)

    with patch.object(coach.httpx, 'get', return_value=upstream_response) as mocked_get:
        with client_for_authenticated_user() as client:
            response = client.get('/api/openwebui/models')

    assert response.status_code == 200
    assert response.json() == [
        {'id': 'model-03', 'name': 'Test model 03'},
        {'id': 'model-17', 'name': 'Test model 17'},
    ]
    assert all(set(model) == {'id', 'name'} for model in response.json())
    mocked_get.assert_called_once()
    assert mocked_get.call_args.kwargs['timeout'] == 15


def test_model_route_returns_empty_list_when_allowlist_is_empty(monkeypatch):
    monkeypatch.setenv('OPENWEBUI_COACH_MODELS', ' ,  ')
    with patch.object(coach.httpx, 'get') as mocked_get:
        with client_for_authenticated_user() as client:
            response = client.get('/api/openwebui/models')

    assert response.status_code == 200
    assert response.json() == []
    mocked_get.assert_not_called()
    coach.app.dependency_overrides.pop(coach.current_user, None)
