from lega.utils.checksum import instantiate, calculate, is_valid, get_from_companion, supported_algorithms
from lega.keyserver import _unlock_key, load_keys_conf, Cache
from lega.utils.exceptions import UnsupportedHashAlgorithm, CompanionNotFound
import hashlib
import unittest
from unittest import mock
from test.support import EnvironmentVarGuard
from lega.utils import get_file_content, sanitize_user_id
import io
from testfixtures import tempdir
from . import pgp_data


class TestBasicFunctions(unittest.TestCase):
    """Basic Tests

    Suite of basic tests for various functions."""

    def setUp(self):
        """Initialise fixtures."""
        self.env = EnvironmentVarGuard()
        self.env.set('LEGA_PASSWORD', 'value')

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

    def test_companion_not_found(self):
        """Companion file not found."""
        with self.assertRaises(CompanionNotFound):
            get_from_companion('tests/resources/priv.pgp')

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
        """Should get a tuple of supported algorithms"""
        result = supported_algorithms()
        self.assertEqual(('md5', 'sha256'), result)

    # @tempdir()
    # # @mock.patch('lega.keyserver._cache')
    # def test_unlock_key(self, filedir):
    #     """Should unlock a private key and return the key ID."""
    #     sec_keyfile = filedir.write('sec_key.asc', pgp_data.PGP_PRIVKEY.encode('utf-8'))
    #
    #     # class CacheObj:
    #     #     def get(self):
    #     #         return pgp_data.PGP_PRIVKEY_BIN
    #     # with self.env:
    #     #     mock_cache.return_value = Cache()
    #     _unlock_key(pgp_data.PGP_NAME, path=sec_keyfile, passphrase=pgp_data.PGP_PASSPHRASE)
    #     # mock_cache.return_value.get(pgp_data.KEY_ID, 'private').assert_called()
    #     # print(dir(result))
    #     self.assertTrue(False)
    #     filedir.cleanup()

    @tempdir()
    @mock.patch('lega.keyserver._cache')
    def test_unlock_key_public(self, mock_cache, filedir):
        """Trying to unlock public key should return assertion error."""
        pub_keyfile = filedir.write('pub_key.asc', pgp_data.PGP_PUBKEY.encode('utf-8'))
        with self.env:
            mock_cache.return_value = Cache()
        with self.assertRaises(AssertionError):
            _unlock_key(pgp_data.PGP_NAME, path=pub_keyfile)
        filedir.cleanup()
