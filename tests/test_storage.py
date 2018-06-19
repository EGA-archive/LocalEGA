import unittest
from lega.utils.storage import FileStorage, S3FileReader, S3Storage
from test.support import EnvironmentVarGuard
from testfixtures import TempDirectory
import os
from io import UnsupportedOperation
from unittest import mock
import boto3


class TestFileStorage(unittest.TestCase):
    """FileStorage

    Testing storage on disk."""

    def setUp(self):
        """Initialise fixtures."""
        self._dir = TempDirectory()
        self.outputdir = self._dir.makedir('output')
        self.env = EnvironmentVarGuard()
        self.env.set('VAULT_LOCATION', self.outputdir)
        self._store = FileStorage()

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('VAULT_LOCATION')
        self._dir.cleanup_all()

    def test_location(self):
        """Test file location."""
        result = self._store.location('12')
        self.assertEqual(os.path.join(self.outputdir, '000/000/000/000/000/000/12'), result)

    def test_copy(self):
        """Test copy file."""
        path = self._dir.write('test.file', 'data1'.encode('utf-8'))
        path1 = self._dir.write('test1.file', ''.encode('utf-8'))
        result = self._store.copy(open(path, 'rb'), path1)
        self.assertEqual(os.stat(path1).st_size, result)


class TestS3Storage(unittest.TestCase):
    """S3Storage

    Testing storage on S3 solution."""

    def setUp(self):
        """Initialise fixtures."""
        self.env = EnvironmentVarGuard()
        self.env.set('VAULT_URL', 'http://localhost:5000')
        self.env.set('VAULT_REGION', 'lega')
        self.env.set('S3_ACCESS_KEY', 'test')
        self.env.set('S3_SECRET_KEY', 'test')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('VAULT_URL')
        self.env.unset('VAULT_REGION')
        self.env.unset('S3_ACCESS_KEY')
        self.env.unset('S3_SECRET_KEY')

    @mock.patch.object(boto3, 'client')
    def test_init_s3storage(self, mock_boto):
        """Initialise S3 storage."""
        S3Storage()
        mock_boto.assert_called()

    @mock.patch.object(boto3, 'client')
    def test_init_location(self, mock_boto):
        """Initialise S3 storage."""
        storage = S3Storage()
        result = storage.location('file_id')
        self.assertEqual('file_id', result)
        mock_boto.assert_called()


class TestS3FileReader(unittest.TestCase):
    """S3FileReader

    Testing S3FileReader."""

    def setUp(self):
        """Initialise fixtures."""
        s3 = mock.MagicMock(name='head_object')
        s3.head_object.return_value = {'ContentLength': 32}
        self._reader = S3FileReader(s3, 'lega', '/path', 'rb', 10)

    def test_tell(self):
        """Test tell, should return the proper loc result."""
        result = self._reader.tell()
        self.assertEqual(0, result)

    def test_seek_start(self):
        """Test seek with whence, should return from proper loc."""
        whence_0 = self._reader.seek(1, 0)
        self.assertEqual(1, whence_0)

    def test_seek_loc(self):
        """Test seek with whence, should return from proper loc."""
        whence_1 = self._reader.seek(1, 1)
        self.assertEqual(1, whence_1)

    def test_seek_end(self):
        """Test seek with whence, should return from proper loc."""
        whence_2 = self._reader.seek(1, 2)
        self.assertEqual(33, whence_2)

    def test_whence_invalid(self):
        """Invalid value of whence should raise ValueError."""
        with self.assertRaises(ValueError):
            self._reader.seek(33, 48)

    def test_str(self):
        """Str representation should return proper message."""
        result = str(self._reader)
        self.assertEqual('<S3FileReader /path>', result)

    def test_detach(self):
        """Detach should raise UnsupportedOperation."""
        with self.assertRaises(UnsupportedOperation):
            self._reader.detach()

    def test_read_error(self):
        """If file is closed should raise ValueError."""
        self._reader.closed = True
        with self.assertRaises(ValueError):
            self._reader.read()

    def test_close(self):
        """Testing close of the file reader."""
        self._reader.close()
        self.assertEqual(True, self._reader.closed)

    def test_exit(self):
        """Test exit."""
        self._reader.__exit__()
        self.assertEqual(True, self._reader.closed)

    def test_enter(self):
        """Testing returning one self."""
        self.assertEqual(self._reader, self._reader.__enter__())
