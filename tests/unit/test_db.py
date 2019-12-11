import unittest
from lega.utils.db import (insert_file,
                           set_error,
                           get_info,
                           store_header, set_archived,
                           mark_in_progress, mark_completed,
                           set_stable_id,
                           connection)
from unittest import mock
import asyncio


class DBTest(unittest.TestCase):
    """Database.

    Testing database actions.
    """

    def setUp(self):
        """Initialise fixtures."""
        self._query_result = [("example", "result"), ("more", "results")]

    @mock.patch('lega.utils.db.CONF')
    @mock.patch('lega.utils.db.psycopg2')
    def test_connect(self, mock_db_connect, mock_conf):
        """Test that connection is returning a connection."""

        # For CONF.get_value(....)
        def values(domain, value, conv=str, default=None, raw=True):
            d = {
                'connection': r'postgresql://user:passwd@db:5432/lega',
                'interval': 10,
                'attempts': 30
            }
            return d.get(value, default)
        mock_conf.get_value = mock.MagicMock(side_effect=values)

        connection.ping()
        mock_db_connect.connect.assert_called()

    @mock.patch('lega.utils.db.connection')
    def test_insert(self, mock_connection):
        """DB insert."""
        mock_connection.cursor().__enter__().fetchone.return_value = self._query_result
        result = insert_file('filename', 'user_id')
        assert result == ("example", "result")

    @mock.patch('lega.utils.db.connection')
    def test_insert_fail(self, mock_connection):
        """DB insert."""
        mock_connection.cursor().__enter__().fetchone.return_value = [()]
        with self.assertRaises(Exception):
            insert_file('filename', 'user_id', 'stable_id')

    @mock.patch('lega.utils.db.connection')
    def test_get_details(self, mock_connection):
        """DB get details."""
        mock_connection.cursor().__enter__().fetchone.return_value = self._query_result
        result = get_info('file_id')
        assert result[0] == ("example", "result")

    # Just need to verify that the cursor is called with execute
    # assert_called_with() can be used to verify the query passed

    @mock.patch('lega.utils.db.connection')
    def test_set_error(self, mock_connection):
        """DB set error."""
        error = mock.Mock()
        error.__cause__ = mock.MagicMock(name='__cause__')
        error.__cause__.return_value = 'something'
        set_error('file_id', error)
        mock_connection.cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connection')
    def test_store_header(self, mock_connection):
        """DB set progress."""
        # Values are not important in this call
        store_header("file_id", b'header')
        mock_connection.cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connection')
    def test_set_archived(self, mock_connection):
        """DB set progress."""
        # Values are not important in this call
        set_archived("file_id", '/ega/archive/000/000/0a1', 1000)
        mock_connection.cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connection')
    def test_mark_in_progress(self, mock_connection):
        """DB mark in progress."""
        # Values are not important in this call
        mark_in_progress('file_id')
        mock_connection.cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connection')
    def test_mark_completed(self, mock_connection):
        """DB mark completed."""
        # Values are not important in this call
        mark_completed('file_id')
        mock_connection.cursor().__enter__().execute.assert_called()

    @mock.patch('lega.utils.db.connection')
    def test_set_stable_id(self, mock_connection):
        """DB mark completed."""
        # Values are not important in this call
        set_stable_id("file_id", 'EGAF00001')
        mock_connection.cursor().__enter__().execute.assert_called()

