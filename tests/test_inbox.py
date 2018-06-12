import unittest
from lega.inbox import LegaFS, FuseOSError, parse_options, main
from unittest import mock
import types
from testfixtures import TempDirectory


class TestLegaFS(unittest.TestCase):
    """LegaFS

    Testing LocalEGA FS."""

    def setUp(self):
        """Setting things up."""
        self._dir = TempDirectory()
        self._fs = LegaFS("/root/is/this/", "user", self._dir.path)
        self._path = self._dir.write('test.smth', 'test'.encode('utf-8'))
        self._path = self._dir.write('test.md5', 'md5'.encode('utf-8'))

    def tearDown(self):
        """Remove setup variables."""
        self._dir.cleanup_all()

    # Testing these is really optional, but good to do.

    @mock.patch('os.path.join')
    def test_real_path(self, mocked):
        """Test retrieve real path, should call os.path.join and return a path."""
        mocked.return_value = "/root/is/this/dir/to/use"
        result = self._fs.real_path('/dir/to/use')
        assert result == "/root/is/this/dir/to/use"

    @mock.patch('os.lstat')
    def test_getattr(self, mocked):
        """Test get file attributes, should call os.lstat with mock values."""
        mocked.return_value = mock.Mock(st_mode=33188, st_ino=14551755, st_dev=64768, st_nlink=1,
                                        st_uid=90393, st_gid=101, st_size=4170, st_atime=1525082089,
                                        st_mtime=1525081721, st_ctime=1525081724)
        expected_result = {'st_uid': 90393, 'st_gid': 101, 'st_mode': 33188, 'st_size': 4170, 'st_nlink': 1,
                           'st_atime': 1525082089, 'st_ctime': 1525081724, 'st_mtime': 1525081721}
        result = self._fs.getattr('/dir/to/use')
        assert result == expected_result

    @mock.patch('os.statvfs')
    def test_statvfs(self, mocked):
        """Test statvfs, should call os.statvfs with mock values."""
        mocked.return_value = mock.Mock(f_bsize=4096, f_frsize=4096, f_blocks=59241954, f_bfree=42909971,
                                        f_bavail=39894880, f_files=15056896, f_ffree=13746982, f_favail=13746982,
                                        f_flag=4096, f_namemax=255)

        expected_result = {'f_bavail': 39894880, 'f_bfree': 42909971, 'f_blocks': 59241954, 'f_bsize': 4096,
                           'f_favail': 13746982, 'f_ffree': 13746982, 'f_files': 15056896, 'f_flag': 4096,
                           'f_frsize': 4096, 'f_namemax': 255}
        result = self._fs.statfs('/dir/to/use')
        assert result == expected_result

    @mock.patch('os.access')
    def test_no_access(self, mocked):
        """Raise FuseOSError as user does not have access."""
        # if this was not tested the errno missing module
        # would not have been spotted
        mocked.return_value = False
        with self.assertRaises(FuseOSError):
            self._fs.access('/some/paht', 'rb')

    @mock.patch('os.fsync')
    def test_fsync(self, mocked):
        """Test LegaFS flush call, should call os.fsync."""
        self._fs.flush('/dir/to/use.txt', 'O_WRONLY')
        self.assertTrue(mocked.called)
        self._fs.fsync('/dir/to/use.txt', 'fdatasync', 'O_WRONLY')
        self.assertTrue(mocked.called)

    @mock.patch('os.unlink')
    def test_unlink(self, mocked):
        """Test LegaFS unlink call, should call os.unlink."""
        self._fs.unlink('/dir/to/use.txt')
        self.assertTrue(mocked.called)

    @mock.patch('os.rmdir')
    def test_rmdir(self, mocked):
        """Test LegaFS rmdir call, should call os.rmdir."""
        self._fs.rmdir('/dir/to/use')
        self.assertTrue(mocked.called)

    @mock.patch('os.mkdir')
    def test_mkdir(self, mocked):
        """Test LegaFS mkdir call."""
        self._fs.mkdir('/dir/to/use', 0o755)
        self.assertTrue(mocked.called)

    @mock.patch('os.chmod')
    def test_chmod(self, mocked):
        """Test LegaFS chmod call, should call os.chmod."""
        self._fs.chmod('/dir/to/use', 0o755)
        self.assertTrue(mocked.called)

    @mock.patch('os.chown')
    def test_chown(self, mocked):
        """Test LegaFS chown call, should call os.chown."""
        self._fs.chown('/dir/to/use.txt', 1, 2)
        self.assertTrue(mocked.called)

    @mock.patch('os.open')
    def test_open(self, mocked):
        """Test LegaFS open call."""
        self._fs.open('/dir/to/use.txt', 'O_WRONLY')
        self.assertTrue(mocked.called)

    @mock.patch('os.open')
    def test_create(self, mocked):
        """Test LegaFS create call, should call os.open."""
        self._fs.create('/dir/to/use.txt', 'O_WRONLY')
        self.assertTrue(mocked.called)

    @mock.patch('os.rename')
    def test_rename(self, mocked):
        """Test LegaFS rename call, should call os.rename."""
        self._fs.rename('/dir/to/old.txt', '/dir/new.txt')
        self.assertTrue(mocked.called)

    @mock.patch('os.utime')
    def test_utimens(self, mocked):
        """Test LegaFS utime call, should call os.utime."""
        self._fs.utimens('/dir/to/file.txt')
        self.assertTrue(mocked.called)

    @mock.patch('os.read')
    @mock.patch('os.lseek')
    def test_read(self, mocklseek, mockread):
        """Test LegaFS read call, should call os.read and os.leek."""
        self._fs.read('/dir/to/use.txt', 100, 0, 'O_RDONLY')
        self.assertTrue(mocklseek.called)
        self.assertTrue(mockread.called)

    @mock.patch('os.write')
    @mock.patch('os.lseek')
    def test_write(self, mocklseek, mockwrite):
        """Test LegaFS write call, should call os.write and os.leek."""
        self._fs.write('/dir/to/use.txt', 100, 0, 'O_WRONLY')
        self.assertTrue(mocklseek.called)
        self.assertTrue(mockwrite.called)

    @mock.patch('os.walk')
    def test_readdir(self, mockwalk):
        """Test LegaFS readdir, should return a generator."""
        result = self._fs.readdir('/dir/to/use', 1)
        self.assertTrue(isinstance(result, types.GeneratorType))

    def test_parse_options_missing(self):
        """Test parse options, should exit because args missing."""
        with self.assertRaises(SystemExit):
            parse_options()

    def test_truncate(self):
        """Test LegaFS truncate, should add path to pending."""
        self._fs.truncate('test.md5', 1)
        self.assertEqual({'test.md5'}, self._fs.pending)

    @mock.patch('lega.inbox.publish')
    @mock.patch('lega.inbox.get_connection')
    @mock.patch('os.close')
    def test_release(self, mock_closed, mock_broker, mock_publish):
        """Test LegaFS release, should send message and close file."""
        self._fs.pending.add('test.smth')
        self._fs.release('test.smth', 1)
        mock_closed.assert_called()

    @mock.patch('lega.inbox.publish')
    @mock.patch('lega.inbox.get_connection')
    def test_send_message(self, mock_broker, mock_publish):
        """"Sending message should try to publish info to broker."""
        self._fs.send_message('test.smth')
        self._fs.send_message('test.md5')
        mock_publish.assert_called()
