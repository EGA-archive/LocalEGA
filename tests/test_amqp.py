import unittest
from unittest import mock
from lega.utils.amqp import get_connection, publish, consume


class BrokerTest(unittest.TestCase):
    """MQ Broker

    Test broker connections."""

    @mock.patch('lega.utils.amqp.CONF')
    @mock.patch('lega.utils.amqp.pika')
    def test_connection_blocking(self, mock_pika, mock_conf):
        """Test if the pika BlockingConnection is called."""
        sections = {'broker': {'hearbeat': 0, 'ssl': True}, 'other': {}}
        mock_conf.sections = mock.Mock(return_value=sections.keys())

        def values(domain, value, conv=str, default=None):
            if value == 'heartbeat_interval':
                return 1
            elif value == 'ssl':
                return True
            else:
                pass
        mock_conf.get_value = mock.MagicMock(side_effect=values)
        get_connection('broker')
        mock_pika.BlockingConnection.assert_called()

    @mock.patch('lega.utils.amqp.CONF')
    @mock.patch('lega.utils.amqp.pika')
    def test_connection_select(self, mock_pika, mock_conf):
        """Test if the pika SelectConnection is called with paramters."""
        sections = {'broker': {'hearbeat': 0, 'ssl': True}, 'other': {}}
        mock_conf.sections = mock.Mock(return_value=sections.keys())
        get_connection('broker', False)
        mock_pika.SelectConnection.assert_called()

    @mock.patch('lega.utils.amqp.get_connection')
    def test_publish(self, mock_channel):
        """Test if publish actually calls the publish to channel."""
        mock_channel = mock.MagicMock(name='basic_publish')
        mock_channel.basic_publish.return_value = mock.Mock()
        publish('message', mock_channel, 'exchange', 'routing')
        mock_channel.basic_publish.assert_called()

    @mock.patch('lega.utils.amqp.pika')
    @mock.patch('lega.utils.amqp.publish')
    def test_consume(self, mock_publish, mock_pika):
        """Testing consume, should look into a queue."""
        work = mock.Mock()
        work.return_value = mock.MagicMock()
        consume(work, mock_pika, 'queue', 'routing')
        print(dir(mock_pika))
        mock_pika.channel.assert_called()
