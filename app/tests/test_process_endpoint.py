from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_process_endpoint():
    html = """
    <html><body>
      <div>12243001000461</div>
      <div>BARENJAGER</div>
      <div>HONEY &amp; PEAR</div>
      <img src="front.png" alt="Label Image: Brand (front) or keg collar">
    </body></html>
    """

    response = client.post(
        "/process",
        files={"file": ("sample.html", html, "text/html")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["application"]["ttb_id"] == "12243001000461"
    assert body["application"]["brand_name"] == "BARENJAGER"