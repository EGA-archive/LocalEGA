import unittest
from lega.mapper import main, work
from unittest import mock


class testMapper(unittest.TestCase):
    """Mapper

    Testing verify functionalities."""
    def setUp(self):
        """Initialise fixtures."""
        pass

    def tearDown(self):
        """Remove anything that was setup."""
        pass

    @mock.patch('lega.mapper.db')
    def test_work(self, mock_db):
        """Test mapper worker, should insert into database."""
        # mock_db.set_stable_id.return_value = mock.Mock()
        data = {'stable_id': '1', 'file_id': '123'}
        work(data)
        mock_db.set_stable_id.assert_called_with('123', '1')

    @mock.patch('lega.mapper.get_connection')
    @mock.patch('lega.mapper.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main mapper, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
