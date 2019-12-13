import unittest
from unittest import mock
from lega.utils.amqp import connection, publish, consume


class BrokerTest(unittest.TestCase):
    """MQ Broker.

    Test broker connections.
    """

    @mock.patch('lega.utils.amqp.CONF')
    @mock.patch('lega.utils.amqp.pika')
    def test_connection(self, mock_pika, mock_conf):
        """Test if the pika BlockingConnection is called."""

        # For CONF.sections()
        sections = {'broker': {'hearbeat': 0, 'connection': 'amqp://user:passwd@localhost:5672/%2F'}, 'other': {}}
        mock_conf.sections = mock.Mock(return_value=sections.keys())

        # For CONF.get_value(....)
        def values(domain, value, conv=str, default=None, raw=True):
            if value == 'connection':
                return r'amqp://user:passwd@localhost:5672/%2F'
            else:
                pass
        mock_conf.get_value = mock.MagicMock(side_effect=values)
        with connection.channel() as c:
            mock_pika.BlockingConnection.assert_called()


    # @mock.patch('lega.utils.amqp.connection')
    # def test_publish(self, mock_channel):
    #     """Test if publish actually calls the publish to channel."""
    #     mock_channel = mock.MagicMock(name='basic_publish')
    #     mock_channel.basic_publish.return_value = mock.Mock()
    #     publish('message', 'exchange', 'routing', correlation_id='1234')
    #     mock_channel.basic_publish.assert_called()

    # @mock.patch('lega.utils.amqp.pika')
    # @mock.patch('lega.utils.amqp.publish')
    # def test_consume(self, mock_publish, mock_pika):
    #     """Testing consume, should look into a queue."""
    #     work = mock.Mock()
    #     work.return_value = mock.MagicMock()
    #     consume(work, 'queue', 'routing')
    #     mock_pika.channel.assert_called()
