"""Basic test to ensure test suite runs."""

def test_basic():
    """Basic test that always passes."""
    assert True

def test_import():
    """Test that bizy package can be imported."""
    import bizy
    assert bizy.__version__ == "0.1.0"