import unittest
from lega.notifications import Forwarder
from unittest import mock


class testForwarder(unittest.TestCase):
    """Ingest

    Testing ingestion functionalities."""

    def setUp(self):
        """Initialise fixtures."""
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        self._forwarder = Forwarder(mock_broker)

    @mock.patch('lega.notifications.LOG')
    def test_connection_made(self, mock_logger):
        """Test connection to socket remote address."""
        mock_transport = mock.MagicMock()
        mock_transport.get_extra_info.return_value = "127.0.0.1"
        self._forwarder.connection_made(mock_transport)
        mock_logger.debug.assert_called_with('Connection from 127.0.0.1')

    def test_data_single_file_parsed(self):
        """Test parsed data."""
        for u, f in self._forwarder.parse(b'user$file.name$'):
            self.assertEqual(u, "user")
            self.assertEqual(f, "file.name")

    def test_data_multiple_file_parsed(self):
        """Test parsed data."""
        for u, f in self._forwarder.parse(b'john$/dir/subdir/fileA.txt$john$/dir/subdir/fileB.txt$john$/dir/subdir/fileC.txt$'):
            self.assertEqual(u, "john")
            self.assertIn(f, ["/dir/subdir/fileA.txt", "/dir/subdir/fileB.txt", "/dir/subdir/fileC.txt"])
