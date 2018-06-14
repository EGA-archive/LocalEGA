import unittest
from lega.verify import main, get_records, work
from unittest import mock
from test.support import EnvironmentVarGuard
from testfixtures import tempdir
from . import pgp_data
import io


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

    @mock.patch('lega.verify.get_connection')
    @mock.patch('lega.verify.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
