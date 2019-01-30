import unittest
from lega.utils.storage import FileStorage, S3FileReader, S3Storage
from test.support import EnvironmentVarGuard
from testfixtures import TempDirectory
import os
from io import UnsupportedOperation, BufferedReader
from unittest import mock
import boto3


class TestFileStorage(unittest.TestCase):
    """FileStorage.

    Testing storage on disk.
    """

    def setUp(self):
        """Initialise fixtures."""
        self._dir = TempDirectory()
        self.outputdir = self._dir.makedir('output')
        self.env = EnvironmentVarGuard()
        self.env.set('ARCHIVE_LOCATION', self.outputdir + '/%s/')
        self._store = FileStorage('archive', 'lega')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('ARCHIVE_LOCATION')
        self._dir.cleanup_all()

    def test_location(self):
        """Test file location."""
        result = self._store.location('12')
        self.assertEqual(os.path.join(self.outputdir, 'lega', '000', '000', '000', '000', '000', '000', '12'), result)

    def test_copy(self):
        """Test copy file."""
        path = self._dir.write('output/lega/test.file', 'data1'.encode('utf-8'))
        path1 = self._dir.write('output/lega/test1.file', ''.encode('utf-8'))
        result = self._store.copy(open(path, 'rb'), path1)
        self.assertEqual(os.stat(path1).st_size, result)

    def test_open(self):
        """Test open file."""
        path = self._dir.write('output/lega/test.file', 'data1'.encode('utf-8'))
        print(path)
        with self._store.open('test.file') as resource:
            self.assertEqual(BufferedReader, type(resource))


class TestS3Storage(unittest.TestCase):
    """S3Storage.

    Testing storage on S3 solution.
    """

    def setUp(self):
        """Initialise fixtures."""
        self._dir = TempDirectory()
        self.env = EnvironmentVarGuard()
        self.env.set('ARCHIVE_URL', 'http://localhost:5000')
        self.env.set('ARCHIVE_REGION', 'lega')
        self.env.set('ARCHIVE_ACCESS_KEY', 'test')
        self.env.set('ARCHIVE_SECRET_KEY', 'test')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('ARCHIVE_URL')
        self.env.unset('ARCHIVE_REGION')
        self.env.unset('ARCHIVE_ACCESS_KEY')
        self.env.unset('ARCHIVE_SECRET_KEY')
        self._dir.cleanup_all()

    @mock.patch.object(boto3, 'client')
    def test_init_s3storage(self, mock_boto):
        """Initialise S3 storage."""
        S3Storage('archive', 'lega')
        mock_boto.assert_called()

    @mock.patch.object(boto3, 'client')
    def test_init_location(self, mock_boto):
        """Initialise S3 storage."""
        storage = S3Storage('archive', 'lega')
        result = storage.location('file_id')
        self.assertEqual('file_id', result)
        mock_boto.assert_called()

    @mock.patch.object(boto3, 'client')
    def test_upload(self, mock_boto):
        """Test copy to S3, should call boto3 client."""
        path = self._dir.write('test.file', 'data1'.encode('utf-8'))
        storage = S3Storage('archive', 'lega')
        storage.copy(path, 'lega')
        mock_boto.assert_called_with('s3', aws_access_key_id='test', aws_secret_access_key='test',
                                     endpoint_url='http://localhost:5000', region_name='lega',
                                     use_ssl=False, verify=False)

    @mock.patch.object(boto3, 'client')
    def test_open(self, mock_boto):
        """Test open , should call S3FileReader."""
        path = self._dir.write('test.file', 'data1'.encode('utf-8'))
        storage = S3Storage('archive', 'lega')
        with storage.open(path) as resource:
            self.assertEqual(S3FileReader, type(resource))


class TestS3FileReader(unittest.TestCase):
    """S3FileReader.

    Testing S3FileReader.
    """

    def setUp(self):
        """Initialise fixtures."""
        self._s3 = mock.MagicMock(name='head_object')
        self._s3.head_object.return_value = {'ContentLength': 32}
        self._s3.get_object.return_value = mock.MagicMock()
        self._reader = S3FileReader(self._s3, 'lega', '/path', 'rb', 10)

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

    def test_read(self):
        """Test end of file."""
        self._reader.closed = False
        self._reader.loc = self._reader.size = 1
        self.assertEqual(b'', self._reader.read())

    def test_read_length(self):
        """Test read file length."""
        self._reader.closed = False
        self._reader._fetch = mock.MagicMock()
        self._reader.loc = 1
        self._reader.size = 10
        with self._reader.read(-2):
            self._reader._fetch.assert_called()

    def test_read1(self):
        """Test read1."""
        self._reader.read = mock.Mock()
        self._reader.read1()
        self._reader.read.assert_called()

    def test_readinto(self):
        """Test readinto."""
        self._reader.read = mock.MagicMock()
        data = []
        self.assertEqual(0, self._reader.readinto(data))

    def test_readinto1(self):
        """Test readinto1."""
        self._reader.readinto = mock.Mock()
        self._reader.readinto1([])
        self._reader.readinto.assert_called()

    def test_fetch(self):
        """Test fetch."""
        self._reader.size = 10
        self._reader._fetch(1, 9, max_attempts=1)
        self._s3.get_object.assert_called()

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
