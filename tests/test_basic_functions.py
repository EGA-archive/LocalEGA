from lega.utils.checksum import instantiate, calculate, is_valid, get_from_companion
from lega.utils.exceptions import UnsupportedHashAlgorithm, CompanionNotFound
import hashlib
import unittest
from unittest import mock
from lega.utils import get_file_content, sanitize_user_id
import io
from testfixtures import tempdir
from . import openpgp_data


class TestBasicFunctions(unittest.TestCase):
    """Basic Tests

    Suite of basic tests for various functions."""

    def test_instantiate(self):
        """Test instantiate algorithm."""
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
    def test_calculate(self, dir):
        """Test Computes the checksum of the file-object."""
        path = dir.write('priv.pgp', openpgp_data.PGP_PRIVKEY.encode('utf-8'))
        with open(path, 'rb') as file_data:
            data = file_data.read()
            file_hash = (hashlib.md5)(data).hexdigest()
        assert calculate(path, 'md5') == file_hash

    def test_calculate_error(self):
        """Test nonexisting file."""
        assert calculate('tests/resources/notexisting.file', 'md5') is None

    @mock.patch('lega.utils.checksum.calculate')
    def test_is_valid(self, mock):
        """Test is valid, mocking calculate."""
        mock.return_value = '20655cb038a3e76e5f27749a028101e7'
        assert is_valid('file/path', '20655cb038a3e76e5f27749a028101e7', 'md5') is True

    def test_companion_not_found(self):
        """Test companion file not found."""
        with self.assertRaises(CompanionNotFound):
            get_from_companion('tests/resources/priv.pgp')

    @mock.patch('lega.utils.open')
    def test_get_file_content(self, mocked: mock.MagicMock):
        """Testing reading file contents."""
        testStream = io.BytesIO()
        testStream.write(b'T.M.')
        testStream.seek(0)
        mocked.return_value = io.TextIOWrapper(io.BytesIO(b'T.M.'))
        assert 'T.M.' == get_file_content('data/file')

    def test_get_file_fail(self):
        """Test reading file error. File does not exist."""
        assert get_file_content('data/notexists.file') is None

    def test_sanitize_user_id(self):
        """Test Sanitize User id."""
        # A good test would be to see if it actually ends in @elixir-europe.org
        # because currently the function does not
        assert sanitize_user_id('user_1245@elixir-europe.org') == 'user_1245'
