import unittest
from lega.ingest import main, run_checksum
from unittest import mock


class testIngest(unittest.TestCase):
    """Ingest

    Testing ingestion functionalities."""

    @mock.patch('lega.ingest.checksum')
    def test_run_checksum(self, mock):
        """Testing running checksum."""
        mock.get_from_companion.return_value = '1', 'md5'
        data = {'encrypted_integrity': {'checksum': '1'}}
        run_checksum(data, 'encrypted_integrity', '/filename')
        mock.get_from_companion.assert_called()
        mock.is_valid.assert_called()

    @mock.patch('lega.ingest.get_connection')
    @mock.patch('lega.ingest.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
