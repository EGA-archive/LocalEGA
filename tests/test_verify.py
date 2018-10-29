import unittest
from lega.verify import main, get_records, work
from unittest import mock
from test.support import EnvironmentVarGuard
from testfixtures import tempdir
from . import pgp_data
import io
from urllib.error import HTTPError
from lega.utils.exceptions import PGPKeyError, KeyserverError


class PatchContextManager:
    """Following: https://stackoverflow.com/a/32127557 example."""

    def __init__(self, method, enter_return, exit_return=False):
        self._patched = mock.patch(method)
        self._enter_return = enter_return
        self._exit_return = exit_return

    def __enter__(self):
        res = self._patched.__enter__()
        res.context = mock.MagicMock()
        res.context.__enter__.return_value = self._enter_return
        res.context.__exit__.return_value = self._exit_return
        res.return_value = res.context
        return res

    def __exit__(self, type, value, tb):
        return self._patched.__exit__()


class testVerify(unittest.TestCase):
    """Verify

    Testing verify functionalities."""
    def setUp(self):
        """Initialise fixtures."""
        self.env = EnvironmentVarGuard()
        self.env.set('LEGA_PASSWORD', 'value')
        self.env.set('QUALITY_CONTROL_VERIFY_CERTIFICATE', 'True')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('LEGA_PASSWORD')
        self.env.unset('QUALITY_CONTROL_VERIFY_CERTIFICATE')

    @tempdir()
    @mock.patch('lega.verify.header_to_records')
    @mock.patch('lega.verify.get_key_id')
    def test_get_records(self, mock_key, mock_records, filedir):
        """Should call the url in order to provide the records."""
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
        returned_data = io.BytesIO(pgp_data.PGP_PRIVKEY.encode())
        with PatchContextManager('lega.verify.urlopen', returned_data) as mocked:
            get_records(open(infile, 'rb'))
            mocked.assert_called()
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.verify.header_to_records')
    @mock.patch('lega.verify.get_key_id')
    def test_get_records_no_verify(self, mock_key, mock_records, filedir):
        """Should call the url in order to provide the records even without a verify turned off."""
        self.env.set('QUALITY_CONTROL_VERIFY_CERTIFICATE', 'False')
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
        returned_data = io.BytesIO(pgp_data.PGP_PRIVKEY.encode())
        with PatchContextManager('lega.verify.urlopen', returned_data) as mocked:
            get_records(open(infile, 'rb'))
            mocked.assert_called()
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.verify.header_to_records')
    @mock.patch('lega.verify.get_key_id')
    def test_get_records_key_error(self, mock_key, mock_records, filedir):
        """The PGP key was not found, should raise PGPKeyError error."""
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
        with mock.patch('lega.verify.urlopen') as urlopen_mock:
            urlopen_mock.side_effect = HTTPError('url', 404, 'msg', None, None)
            with self.assertRaises(PGPKeyError):
                get_records(open(infile, 'rb'))
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.verify.header_to_records')
    @mock.patch('lega.verify.get_key_id')
    def test_get_records_server_error(self, mock_key, mock_records, filedir):
        """Some keyserver error occured, should raise KeyserverError error."""
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
        with mock.patch('lega.verify.urlopen') as urlopen_mock:
            urlopen_mock.side_effect = HTTPError('url', 400, 'msg', None, None)
            with self.assertRaises(KeyserverError):
                get_records(open(infile, 'rb'))
        filedir.cleanup()

    @tempdir()
    @mock.patch('lega.verify.header_to_records')
    @mock.patch('lega.verify.get_key_id')
    def test_get_records_error(self, mock_key, mock_records, filedir):
        """Some general error occured, should raise KeyserverError error."""
        self.env.set('QUALITY_CONTROL_VERIFY_CERTIFICATE', 'False')
        infile = filedir.write('infile.in', bytearray.fromhex(pgp_data.ENC_FILE))
        with mock.patch('lega.verify.urlopen') as urlopen_mock:
            urlopen_mock.side_effect = Exception
            with self.assertRaises(KeyserverError):
                get_records(open(infile, 'rb'))
        filedir.cleanup()

    @mock.patch('lega.verify.get_connection')
    @mock.patch('lega.verify.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()

    @tempdir()
    @mock.patch('lega.verify.db')
    @mock.patch('lega.verify.body_decrypt')
    @mock.patch('lega.verify.publish')
    @mock.patch('lega.verify.get_records')
    def test_work(self, mock_records, mock_publish, mock_decrypt, mock_db, filedir):
        """Test verify worker, should send a messge."""
        # Mocking a lot of stuff, ast it is previously tested
        mock_publish.return_value = mock.MagicMock()
        mock_db.status.return_value = mock.Mock()
        mock_records.return_value = ['data'], 'key_id'
        mock_decrypt.return_value = mock.Mock()
        store = mock.MagicMock()
        store.open.return_value = mock.MagicMock()
        mock_broker = mock.MagicMock(name='channel')
        mock_broker.channel.return_value = mock.Mock()
        infile = filedir.write('infile.in', 'text'.encode("utf-8"))
        data = {'header': pgp_data.ENC_FILE, 'stable_id': '1', 'vault_path': infile, 'file_id': '123', 'org_msg': {}}
        result = work('10', store, mock_broker, data)
        self.assertTrue({'status': {'state': 'COMPLETED', 'details': '1'}}, result)
        filedir.cleanup()
