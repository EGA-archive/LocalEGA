import unittest
from lega.utils.db import (insert_file,
                           get_errors, set_error,
                           get_info,
                           store_header, set_archived,
                           mark_in_progress, mark_completed,
                           set_stable_id,
                           fetch_args, connect)
from unittest import mock
import asyncio


class DBTest(unittest.TestCase):
    """Database.

    Testing database actions.
    """

    def setUp(self):
        """Initialise fixtures."""
        self._loop = asyncio.get_event_loop()
        self._query_result = [("example", "result"), ("more", "results")]

    @mock.patch('lega.utils.db.fetch_args')
    @mock.patch('lega.utils.db.psycopg2')
    def test_connect(self, mock_db_connect, mock_args):
        """Test that connection is returning a connection."""
        connect()
        mock_args.assert_called()
        mock_db_connect.connect.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_insert(self, mock_connect):
        """DB insert."""
        mock_connect().__enter__().cursor().__enter__().fetchone.return_value = self._query_result
        result = insert_file('filename', 'user_id')
        assert result == ("example", "result")

    @mock.patch('lega.utils.db.connect')
    def test_insert_fail(self, mock_connect):
        """DB insert."""
        mock_connect().__enter__().cursor().__enter__().fetchone.return_value = [()]
        with self.assertRaises(Exception):
            insert_file('filename', 'user_id', 'stable_id')

    @mock.patch('lega.utils.db.connect')
    def test_get_errors(self, mock_connect):
        """DB get errors."""
        mock_connect().__enter__().cursor().__enter__().fetchall.return_value = self._query_result
        result = get_errors()
        assert result == self._query_result

    @mock.patch('lega.utils.db.connect')
    def test_get_details(self, mock_connect):
        """DB get details."""
        mock_connect().__enter__().cursor().__enter__().fetchone.return_value = self._query_result
        result = get_info('file_id')
        assert result[0] == ("example", "result")

    # Just need to verify that the cursor is called with execute
    # assert_called_with() can be used to verify the query passed

    @mock.patch('lega.utils.db.connect')
    def test_set_error(self, mock_connect):
        """DB set error."""
        error = mock.Mock()
        error.__cause__ = mock.MagicMock(name='__cause__')
        error.__cause__.return_value = 'something'
        set_error('file_id', error)
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_store_header(self, mock_connect):
        """DB set progress."""
        # Values are not important in this call
        store_header("file_id", b'header')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_set_archived(self, mock_connect):
        """DB set progress."""
        # Values are not important in this call
        set_archived("file_id", '/ega/archive/000/000/0a1', 1000)
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_mark_in_progress(self, mock_connect):
        """DB mark in progress."""
        # Values are not important in this call
        mark_in_progress('file_id')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_mark_completed(self, mock_connect):
        """DB mark completed."""
        # Values are not important in this call
        mark_completed('file_id')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connect')
    def test_set_stable_id(self, mock_connect):
        """DB mark completed."""
        # Values are not important in this call
        set_stable_id("file_id", 'EGAF00001')
        mock_connect().__enter__().cursor().__enter__().execute.assert_called()

    def test_fetch_args(self):
        """Test fetching arguments."""
        data_object = mock.MagicMock(name='get_value')
        data_object.get_value.return_value = 'value'
        result = fetch_args(data_object)
        assert {'user': 'value',
                'password': 'value',
                'database': 'value',
                'host': 'value',
                'port': 'value',
                'sslmode': 'value'} == result
