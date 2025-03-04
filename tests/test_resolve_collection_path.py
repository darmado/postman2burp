i@patch('postman2burp.COLLECTIONS_DIR')
def test_resolve_collection_path(self, mock_collections_dir):
    """Test the resolve_collection_path function."""
    # Set up mocks - make sure to set the return_value, not just patch the name
    mock_collections_dir.return_value = self.test_collections_dir
    
    # Test with absolute path
    with patch('os.path.isabs', return_value=True):
        path = resolve_collection_path("/absolute/path/collection.json")
        self.assertEqual(path, "/absolute/path/collection.json")
    
    # Test with existing file
    with patch('os.path.isabs', return_value=False):
        with patch('os.path.exists', return_value=True):
            path = resolve_collection_path("existing_file.json")
            self.assertEqual(path, "existing_file.json")
    
    # Test with file in collections directory - use a more specific approach
    with patch('os.path.isabs', return_value=False):
        with patch('os.path.exists', side_effect=[False, True]):
            with patch('os.path.join', return_value=os.path.join(self.test_collections_dir, "collection_in_dir.json")):
                path = resolve_collection_path("collection_in_dir.json")
                self.assertEqual(path, os.path.join(self.test_collections_dir, "collection_in_dir.json"))
    
    # Test with non-existent file
    with patch('os.path.isabs', return_value=False):
        with patch('os.path.exists', return_value=False):
            path = resolve_collection_path("nonexistent.json")
            self.assertEqual(path, "nonexistent.json")