"""API Tests"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_analyze_no_file():
    """Test analyze endpoint without file"""
    response = client.post("/api/v1/analyze")
    assert response.status_code == 422  # Validation error


def test_analyze_invalid_file_type():
    """Test analyze endpoint with invalid file type"""
    files = {"file": ("test.xyz", b"content", "application/octet-stream")}
    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


# Add more tests as needed
