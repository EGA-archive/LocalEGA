from lega.utils.checksum import instantiate, calculate, is_valid, get_from_companion, supported_algorithms
from lega.utils.exceptions import UnsupportedHashAlgorithm, CompanionNotFound
from lega.conf.__main__ import main
from lega.utils.db import _do_exit
import hashlib
import unittest
from unittest import mock
from lega.utils import get_file_content, sanitize_user_id
import io
from testfixtures import tempdir
from . import pgp_data
from io import StringIO


class TestBasicFunctions(unittest.TestCase):
    """Basic Tests

    Suite of basic tests for various functions."""

    def test_instantiate(self):
        """Instantiate algorithm."""
        m1 = instantiate('md5')
        m2 = instantiate('sha256')
        data = 'data'.encode('utf-8')
        m1.update(data)
        m2.update(data)
        assert m1.hexdigest() == (hashlib.md5)(data).hexdigest()
        assert m2.hexdigest() == (hashlib.sha256)(data).hexdigest()
        with self.assertRaises(UnsupportedHashAlgorithm):
            instantiate('unkownAlg')

    @tempdir()
    def test_calculate(self, filedir):
        """Compute the checksum of the file-object."""
        path = filedir.write('priv.pgp', pgp_data.PGP_PRIVKEY.encode('utf-8'))
        with open(path, 'rb') as file_data:
            data = file_data.read()
            file_hash = (hashlib.md5)(data).hexdigest()
        assert calculate(path, 'md5') == file_hash
        filedir.cleanup()

    def test_calculate_error(self):
        """Test nonexisting file."""
        assert calculate('tests/resources/notexisting.file', 'md5') is None

    @mock.patch('lega.utils.checksum.calculate')
    def test_is_valid(self, mock):
        """Test is_valid function, mocking calculate."""
        mock.return_value = '20655cb038a3e76e5f27749a028101e7'
        assert is_valid('file/path', '20655cb038a3e76e5f27749a028101e7', 'md5') is True

    @tempdir()
    def test_companion_not_found(self, filedir):
        """Companion file not found."""
        path = filedir.write('priv.file', 'content'.encode('utf-8'))
        with self.assertRaises(CompanionNotFound):
            get_from_companion(path)
        filedir.cleanup()

    @tempdir()
    def test_companion_file(self, filedir):
        """Test Companion file contents."""
        path = filedir.write('priv.file', 'content'.encode('utf-8'))
        filedir.write('priv.file.md5', 'md5content'.encode('utf-8'))
        result = get_from_companion(path)
        self.assertEqual(('md5content', 'md5'), result)
        filedir.cleanup()

    @mock.patch('lega.utils.open')
    def test_get_file_content(self, mocked: mock.MagicMock):
        """Reading file contents, should get the proper contents."""
        testStream = io.BytesIO()
        testStream.write(b'T.M.')
        testStream.seek(0)
        mocked.return_value = io.TextIOWrapper(io.BytesIO(b'T.M.'))
        assert 'T.M.' == get_file_content('data/file')

    def test_get_file_fail(self):
        """Reading file error. File does not exist."""
        assert get_file_content('data/notexists.file') is None

    def test_sanitize_user_id(self):
        """Sanitize User ID, should get just the user ID."""
        # A good test would be to see if it actually ends in @elixir-europe.org
        # because currently the function does not
        assert sanitize_user_id('user_1245@elixir-europe.org') == 'user_1245'

    def test_supported_algorithms(self):
        """Should get a tuple of supported algorithms."""
        result = supported_algorithms()
        self.assertEqual(('md5', 'sha256'), result)

    def test_config_main(self):
        """Testing main configuration."""
        with mock.patch('sys.stdout', new=StringIO()) as fake_stdout:
            main(['--conf', 'fake/conf.ini'])
            self.assertTrue(fake_stdout.getvalue(), 'Configuration files:')

        with mock.patch('sys.stdout', new=StringIO()) as fake_stdout:
            main(['--list'])
            self.assertTrue(fake_stdout.getvalue(), 'Configuration values:')

    def test_do_exit(self):
        """Testing simple exit."""
        # Mostly for completion.
        with self.assertRaises(SystemExit):
            _do_exit()
