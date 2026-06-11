from app.services.image_extractor import extract_images_from_html


def test_extract_images_from_html():
    sample = """
    <html><body>
      <img src="sig.png" alt="Authorized Signature">
      <img src="front.png" alt="Label Image: Brand (front) or keg collar">
      <img src="back.png" alt="Label Image: Back">
    </body></html>
    """
    result = extract_images_from_html(sample)
    assert len(result) == 3
    assert result[0].image_type == "signature"
    assert result[1].image_type == "front_label"
    assert result[2].image_type == "back_label"