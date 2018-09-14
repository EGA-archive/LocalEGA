import unittest
from lega.ingest import main, work
from unittest import mock
from testfixtures import tempdir
from pathlib import PosixPath
from . import pgp_data
from lega.utils.exceptions import FromUser


class testIngest(unittest.TestCase):
    """Ingest

    Testing ingestion functionalities."""

    @mock.patch('lega.ingest.get_connection')
    @mock.patch('lega.ingest.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()

    @tempdir()
    @mock.patch('lega.ingest.get_header')
    @mock.patch('lega.ingest.Path')
    @mock.patch('lega.ingest.db')
    def test_work(self, mock_db, mock_path, mock_header, filedir):
        """Test ingest worker, should send a messge."""
        # Mocking a lot of stuff, as it is previously tested
        mock_path = mock.Mock(spec=PosixPath)
        mock_path.return_value = ''
        mock_header.return_value = b'beginning', b'header'
        mock_db.insert_file.return_value = 32
        store = mock.MagicMock()
        store.location.return_value = 'smth'
        store.open.return_value = mock.MagicMock()
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
        data = {'filepath': infile, 'user': 'user_id@elixir-europe.org'}
        result = work(store, mock_broker, data)
        mocked = {'filepath': infile, 'user': 'user_id@elixir-europe.org',
                  'file_id': 32,
                  'org_msg': {'filepath': infile, 'user': 'user_id@elixir-europe.org'},
                  'header': '626567696e6e696e67686561646572',
                  'vault_path': 'smth'}
        self.assertEqual(mocked, result)
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.ingest.get_header')
    @mock.patch('lega.ingest.Path')
    @mock.patch('lega.ingest.db')
    def test_db_fail(self, mock_db, mock_path, mock_header, filedir):
        """Test ingest worker, insert_file fails."""
        # Mocking a lot of stuff, as it is previously tested
        mock_path = mock.Mock(spec=PosixPath)
        mock_path.return_value = ''
        mock_header.return_value = b'beginning', b'header'
        mock_db.insert_file.side_effect = Exception("Some strange exception")

        store = mock.MagicMock()
        store.location.return_value = 'smth'
        store.open.return_value = mock.MagicMock()
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))

        data = {'filepath': infile, 'user': 'user_id@elixir-europe.org'}
        result = work(store, mock_broker, data)
        self.assertEqual(None, result)
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.ingest.get_header')
    @mock.patch('lega.ingest.Path')
    @mock.patch('lega.ingest.db')
    @mock.patch('lega.utils.db.set_error')
    def test_mark_in_progress_fail(self, mock_set_error, mock_db, mock_path, mock_header, filedir):
        """Test ingest worker, mark_in_progress fails."""
        # Mocking a lot of stuff, as it is previously tested
        mock_path = mock.Mock(spec=PosixPath)
        mock_path.return_value = ''
        mock_header.return_value = b'beginning', b'header'
        mock_db.mark_in_progress.side_effect = Exception("Some strange exception")

        store = mock.MagicMock()
        store.location.return_value = 'smth'
        store.open.return_value = mock.MagicMock()
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))

        data = {'filepath': infile, 'user': 'user_id@elixir-europe.org'}
        result = work(store, mock_broker, data)
        self.assertEqual(None, result)
        mock_set_error.assert_called()
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.ingest.get_header')
    @mock.patch('lega.ingest.Path')
    @mock.patch('lega.ingest.db')
    @mock.patch('lega.utils.db.set_error')
    @mock.patch('lega.utils.db.get_connection')
    @mock.patch('lega.utils.db.publish')
    def test_mark_in_progress_fail_with_from_user_error(self, mock_publish, mock_get_connection, mock_set_error, mock_db, mock_path, mock_header, filedir):
        """Test ingest worker, mark_in_progress fails."""
        # Mocking a lot of stuff, as it is previously tested
        raised_exception = FromUser()

        mock_path = mock.Mock(spec=PosixPath)
        mock_path.return_value = ''
        mock_header.return_value = b'beginning', b'header'
        mock_db.mark_in_progress.side_effect = raised_exception
        mock_db.insert_file.return_value = 32

        store = mock.MagicMock()
        store.location.return_value = 'smth'
        store.open.return_value = mock.MagicMock()
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))

        data = {'filepath': infile, 'user': 'user_id@elixir-europe.org'}
        result = work(store, mock_broker, data)

        self.assertEqual(None, result)
        mock_set_error.assert_called_with(32, raised_exception, True)
        mock_get_connection.assert_called()

        mock_publish.assert_called()
        args_to_publish = mock_publish.call_args[0]
        assert(args_to_publish[2] == 'cega')
        assert(args_to_publish[3] == 'files.error')
        assert('filepath' in args_to_publish[0])
        assert('user' in args_to_publish[0])
        assert('reason' in args_to_publish[0])
        assert(args_to_publish[0]['user'] == 'user_id@elixir-europe.org')
        assert(args_to_publish[0]['reason'] == str(raised_exception))

        filedir.cleanup()
