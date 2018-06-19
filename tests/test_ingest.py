import unittest
from lega.ingest import main, run_checksum, work
from lega.utils.exceptions import NotFoundInInbox
from unittest import mock
from testfixtures import tempdir
from lega.utils.exceptions import Checksum
from pathlib import PosixPath
from . import pgp_data


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

    @mock.patch('lega.ingest.checksum')
    def test_run_checksum_no_alg(self, mock):
        """Testing running checksum, if there is already an algorithm key."""
        mock.get_from_companion.return_value = '1', 'md5'
        data = {'encrypted_integrity': {'checksum': '1', 'algorithm': None}}
        result = run_checksum(data, 'encrypted_integrity', '/filename')
        self.assertEqual(None, result)

    @mock.patch('lega.ingest.checksum')
    def test_run_checksum_not_valid(self, mock):
        """Testing running checksum, if there is already an algorithm key."""
        mock.get_from_companion.return_value = '1', 'md5'
        mock.is_valid.return_value = False
        data = {'encrypted_integrity': {'checksum': '1'}}
        with self.assertRaises(Checksum):
            run_checksum(data, 'encrypted_integrity', '/filename')

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
        # Mocking a lot of stuff, ast it is previously tested
        mock_path = mock.Mock(spec=PosixPath)
        mock_path.return_value = ''
        mock_header.return_value = b'beginning', b'header'
        mock_db.insert_file.return_value = 'db_file_id'
        mock_db.set_status.return_value = 'db_status'
        mock_db.Status = mock.MagicMock(name='Archived')
        mock_db.Status.Archived.value = 'Archived'
        store = mock.MagicMock()
        store.location.return_value = 'smth'
        store.open.return_value = mock.MagicMock()
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        infile = filedir.write('infile.in',  bytearray.fromhex(pgp_data.ENC_FILE))
        data = {'filepath': infile, 'stable_id': 1, 'user': 'user_id@exlir-europe.org'}
        result = work(store, mock_broker, data)
        mocked = {'filepath': infile, 'stable_id': 1,
                  'user': 'user_id@exlir-europe.org', 'file_id': 'db_file_id', 'user_id': 'user_id',
                  'org_msg': {'filepath': infile, 'stable_id': 1, 'user': 'user_id@exlir-europe.org'},
                  'status': 'Archived', 'header': '626567696e6e696e67686561646572',
                  'vault_path': 'smth', 'vault_type': 'MagicMock'}
        self.assertEqual(mocked, result)
        filedir.cleanup()
