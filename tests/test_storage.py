import unittest
from lega.utils.storage import FileStorage, S3FileReader, S3Storage
from test.support import EnvironmentVarGuard
from testfixtures import TempDirectory
import os
from unittest import mock


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


class TestS3FileReader(unittest.TestCase):
    """S3FileReader

    Testing S3FileReader."""

    def setUp(self):
        """Initialise fixtures."""
        self._reader = S3FileReader()
