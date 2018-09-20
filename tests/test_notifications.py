import unittest
from lega.notifications import Forwarder
from unittest import mock


class testForwarder(unittest.TestCase):
    """Notifications.

    Testing Notifications functionalities.
    """

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

    @mock.patch('lega.notifications.LOG')
    def test_connection_close(self, mock_logger):
        """Test connection close, should call transport close."""
        self._forwarder.transport = mock.Mock()
        self._forwarder.connection_lost('')
        self._forwarder.transport.close.assert_called()

    def test_data_single_file_parsed(self):
        """Test parsed data single file."""
        for u, f in self._forwarder.parse(b'user$file.name$'):
            self.assertEqual(u, "user")
            self.assertEqual(f, "file.name")

    def test_data_multiple_file_parsed(self):
        """Test parsed data, multiple files."""
        for u, f in self._forwarder.parse(b'john$/dir/subdir/fileA.txt$john$/dir/subdir/fileB.txt$john$/dir/subdir/fileC.txt$'):
            self.assertEqual(u, "john")
            self.assertIn(f, ["/dir/subdir/fileA.txt", "/dir/subdir/fileB.txt", "/dir/subdir/fileC.txt"])

    def test_received_data(self):
        """Test received data send message."""
        self._forwarder.send_message = mock.Mock()
        self._forwarder.data_received(b'user$file.name$')
        self._forwarder.send_message.assert_called_with('user', 'file.name')

    def test_received_data_2(self):
        """Test received data send message."""
        self._forwarder.send_message = mock.Mock()
        self._forwarder.data_received(b'user$file.name$user$/to')
        self._forwarder.send_message.assert_called_with('user', 'file.name')
        self._forwarder.data_received(b'to4.txt$us')
        self._forwarder.send_message.assert_called_with('user', '/toto4.txt')
        self._forwarder.data_received(b'er$test.fi')
        self._forwarder.data_received(b'le$')
        self._forwarder.send_message.assert_called_with('user', 'test.file')

    @mock.patch('os.stat')
    @mock.patch('lega.notifications.publish')
    @mock.patch('lega.notifications.calculate')
    def test_send_message(self, mock_calculate, mock_publish, mock_stat):
        """Test received data error."""
        mock_stat.size.return_value = 1
        self._forwarder.send_message('user', 'file.name')
        mock_publish.assert_called()
