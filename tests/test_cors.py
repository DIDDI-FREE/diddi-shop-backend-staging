from fastapi.testclient import TestClient

from app_base.main import app


def test_cors_allows_diddifree_subdomains_and_localhost():
    with TestClient(app) as client:
        for origin in ("https://frontend.diddifree.com", "http://localhost:3000"):
            response = client.options(
                "/health",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "authorization",
                },
            )

            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
            assert "GET" in response.headers["access-control-allow-methods"]
            assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_cors_rejects_arbitrary_origins():
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Origin": "https://attacker.example"},
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers

