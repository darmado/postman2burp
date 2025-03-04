@patch('postman2burp.check_proxy_connection')
def test_detect_running_proxy(self, mock_check_proxy):
    """Test the detect_running_proxy function."""
    # Test successful detection - update to match actual implementation
    # The third proxy in COMMON_PROXIES is localhost:8090
    mock_check_proxy.side_effect = [False, False, True, False]
    host, port = detect_running_proxy()
    self.assertEqual(host, "localhost")
    self.assertEqual(port, 8090)  # Update expected port to 8090
    
    # Test no proxy detected
    mock_check_proxy.side_effect = [False] * 10
    host, port = detect_running_proxy()
    self.assertIsNone(host)
    self.assertIsNone(port)