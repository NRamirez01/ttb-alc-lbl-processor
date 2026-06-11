from app.services.html_parser import parse_application_html


def test_parse_application_html():
    sample = """
    <html><body>
    <div>12243001000461</div>
    <div>BARENJAGER</div>
    <div>HONEY &amp; PEAR</div>
    <div>12MW02</div>
    <div>NY-I-490</div>
    <div>SIDNEY FRANK IMPORTING CO., INC.</div>
    <div>35</div>
    <div>SURRENDERED</div>
    <div>OTHER SPECIALTIES &amp; PROPRIETARIES</div>
    <div>08/30/2012</div>
    <div>09/18/2012</div>
    </body></html>
    """
    result = parse_application_html(sample)
    assert result.ttb_id == "12243001000461"
    assert result.brand_name == "BARENJAGER"
    assert result.fanciful_name == "HONEY & PEAR"