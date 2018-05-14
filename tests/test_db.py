import unittest
from lega.utils.db import insert_file, get_errors, set_error, get_details, set_progress, set_encryption, finalize_file
from unittest import mock


class DBTest(unittest.TestCase):
    """Database

    Testing database actions."""

    def setUp(self):
        """Initialise fixtures."""
        self._query_result = [("example", "result"), ("more", "results")]

    @mock.patch('lega.utils.db.connect')
    def test_insert(self, mock_connect):
        """DB insert."""
        mock_connect().__enter__().cursor().__enter__().fetchone.return_value = self._query_result
        result = insert_file('filename', 'user_id', 'stable_id')
        assert result == ("example", "result")

    @mock.patch('lega.utils.db.connect')
    def test_get_errors(self, mock_connect):
        """DB get errors."""
        mock_connect().__enter__().cursor().__enter__().fetchall.return_value = self._query_result
        result = get_errors()
        assert result == self._query_result

    @mock.patch('lega.utils.db.connect')
    def test_get_details(self, mock_connect):
        """DB get details."""
        mock_connect().__enter__().cursor().__enter__().fetchone.return_value = self._query_result
        result = get_details('file_id')
        assert result[0] == ("example", "result")

    # Just need to verify that the cursor is called with execute
    # assert_called_with() can be used to verify the query passed

    @mock.patch('lega.utils.db.connect')
    def test_set_error(self, mock_connect):
        """DB set error."""
        set_error('file_id', 'error')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_set_progress(self, mock_connect):
        """DB set progress."""
        # Values are not important in this call
        set_progress("file_id", 'staging_name', 'enc_checksum', 'enc_checksum_algo', 'org_checksum', 'org_checksum_algo')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_set_encryption(self, mock_connect):
        """DB set encryption."""
        # Values are not important in this call
        set_encryption('file_id', 'info', 'digest')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_finalize_file(self, mock_connect):
        """DB finalise file."""
        # Values are not important in this call
        finalize_file('file_id', 'file_path', 100)
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()
