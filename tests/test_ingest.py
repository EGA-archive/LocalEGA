import unittest
from lega.ingest import get_master_key, main
import io
from unittest import mock
from . import rsa_data
import json


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


class testIngest(unittest.TestCase):
    """Ingest

    Testing ingestion functionalities."""

    @mock.patch('lega.ingest.CONF.get')
    def test_fetch_rsa_from_keyserver(self, mockedget):
        """Fetch RSA key from keyserver."""
        mockedget.return_value = 'https://ega-keys/active/rsa'
        returned_data = io.BytesIO(json.dumps(rsa_data.RSA_PRIVKEY_MATERIAL).encode())
        with PatchContextManager('lega.ingest.urlopen', returned_data) as mocked:
            get_master_key()
            mocked.assert_called()  # Just assume the openUrl is called

    @mock.patch('lega.ingest.CONF.get')
    def test_fetch_rsa_exception(self, mockedget):
        """Fetch RSA trigger SystemExit."""
        mockedget.return_value = 'https://ega-keys/active/rsa'
        """Fetch RSA key from keyserver."""
        with self.assertRaises(SystemExit):
            get_master_key()

    @mock.patch('lega.ingest.consume')
    @mock.patch('functools.partial')
    @mock.patch('lega.ingest.work')
    @mock.patch('lega.ingest.get_master_key')
    def test_main(self, mock_rsa, mock_work, mock_partial, mock_consume):
        """Test main ingest, by mocking every call."""
        mock_rsa.return_value = rsa_data.RSA_PRIVKEY_MATERIAL
        mock_partial.return_value = mock.MagicMock()
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_rsa.assert_called()
        mock_partial.assert_called()
        mock_consume.assert_called()
