from lega.utils.checksum import instantiate, calculate, is_valid, get_from_companion, supported_algorithms
from lega.utils.exceptions import UnsupportedHashAlgorithm, CompanionNotFound
from lega.conf.__main__ import main
import hashlib
import unittest
from unittest import mock
from lega.utils import sanitize_user_id
from testfixtures import tempdir
# import sys
from io import StringIO


class TestBasicFunctions(unittest.TestCase):
    """Basic Tests.

    Suite of basic tests for various functions.
    """

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
