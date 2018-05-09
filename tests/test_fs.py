import unittest
<<<<<<< HEAD
from lega.fs import LegaFS, FuseOSError
from unittest import mock
import errno
=======
from lega.fs import LegaFS
from unittest import mock
>>>>>>> 17db32876063689a6e43a643fb5477be3e4e5a3d


class TestLegaFS(unittest.TestCase):
    """LegaFS

    Testing LocalEGA FS."""

    def setUp(self):
        """Setting things up."""
<<<<<<< HEAD
        self._fs = LegaFS("/root/is/this/", "user", 'broker')

    # Testing these is really optional, but good to do.

    @mock.patch('os.path.join')
    def test_real_path(self, mocked):
        """Test retrieve real path."""
        mocked.return_value = "/root/is/this/dir/to/use"
        result = self._fs._real_path('/dir/to/use')
        assert result == "/root/is/this/dir/to/use"

    @mock.patch('os.lstat')
    def test_getattr(self, mocked):
        """Test get file attributes."""
        mocked.return_value = mock.Mock(st_mode=33188, st_ino=14551755, st_dev=64768, st_nlink=1,
                                        st_uid=90393, st_gid=101, st_size=4170, st_atime=1525082089,
                                        st_mtime=1525081721, st_ctime=1525081724)
        expected_result = {'st_uid': 90393, 'st_gid': 101, 'st_mode': 33188, 'st_size': 4170, 'st_nlink': 1,
                           'st_atime': 1525082089, 'st_ctime': 1525081724, 'st_mtime': 1525081721}
        result = self._fs.getattr('/dir/to/use')
        assert result == expected_result

    @mock.patch('os.access')
    def test_no_access(self, mocked):
        """Raise FuseOSError as user does not have access."""
        # if this was not tested the errno missing module
        # would not have been spotted
        mocked.return_value = False
        with self.assertRaises(FuseOSError):
            self._fs.access('/some/paht', 'rb')
=======
        connection = mock.MagicMock()
        connection.channel.return_value = "test"
        self._fs = LegaFS("/root/is/this/", "user", connection)

    @mock.patch('os.path.join')
    def test_real_path(self, mockedjoin):
        """Test retrieve real path."""
        mockedjoin.return_value = "/root/is/this/dir/to/use"
        result = self._fs._real_path('/dir/to/use')
        assert result == "/root/is/this/dir/to/use"
>>>>>>> 17db32876063689a6e43a643fb5477be3e4e5a3d
