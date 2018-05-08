import unittest
from lega.fs import LegaFS
from unittest import mock


class TestLegaFS(unittest.TestCase):
    """LegaFS

    Testing LocalEGA FS."""

    def setUp(self):
        """Setting things up."""
        connection = mock.MagicMock()
        connection.channel.return_value = "test"
        self._fs = LegaFS("/root/is/this/", "user", connection)

    @mock.patch('os.path.join')
    def test_real_path(self, mockedjoin):
        """Test retrieve real path."""
        mockedjoin.return_value = "/root/is/this/dir/to/use"
        result = self._fs._real_path('/dir/to/use')
        assert result == "/root/is/this/dir/to/use"
