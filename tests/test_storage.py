import unittest
from lega.utils.storage import FileStorage
from test.support import EnvironmentVarGuard
from testfixtures import TempDirectory
import os


class TestFileStorage(unittest.TestCase):
    """FileStorage

    Testing storge on disk."""

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
