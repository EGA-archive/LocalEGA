import unittest
from lega.finalize import main, work
from unittest import mock


class testFinalize(unittest.TestCase):
    """Finalize.

    Testing Finalizer functionalities.
    """

    def setUp(self):
        """Initialise fixtures."""
        pass

    def tearDown(self):
        """Remove anything that was setup."""
        pass

    @mock.patch('lega.finalize.db')
    def test_work(self, mock_db):
        """Test finalize worker, should insert into database."""
        # mock_db.set_stable_id.return_value = mock.Mock()
        data = {'stable_id': '1', 'file_id': '123'}
        work(data)
        mock_db.set_stable_id.assert_called_with('123', '1')

    @mock.patch('lega.finalize.get_connection')
    @mock.patch('lega.finalize.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main finalize, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
