import unittest
import psycopg2
from lega.mapper import main, work
from unittest import mock


class testMapper(unittest.TestCase):
    """Mapper

    Testing mapper functionalities."""
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

    @mock.patch('lega.mapper.db')
    @mock.patch('lega.utils.db.set_error')
    def test_work_fail_insert(self, mock_set_error, mock_db):
        """Test mapper worker, test failure to insert into db."""
        # mock_db.set_stable_id.return_value = mock.Mock()
        data = {'stable_id': '1', 'file_id': '123'}
        raised_exception = psycopg2.Error("Custom error in tha house")
        mock_db.set_stable_id.side_effect = raised_exception

        work(data)

        mock_db.set_stable_id.assert_called_with('123', '1')
        mock_set_error.assert_called_with('123', raised_exception, False)
