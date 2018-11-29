import unittest
from lega.verify import main  # , _work
from unittest import mock
from test.support import EnvironmentVarGuard
# from testfixtures import tempdir


class PatchContextManager:
    """Patch Context Manger.

    Following: https://stackoverflow.com/a/32127557 example.
    """

    def __init__(self, method, enter_return, exit_return=False):
        """Init for class."""
        self._patched = mock.patch(method)
        self._enter_return = enter_return
        self._exit_return = exit_return

    def __enter__(self):
        """Define enter function."""
        res = self._patched.__enter__()
        res.context = mock.MagicMock()
        res.context.__enter__.return_value = self._enter_return
        res.context.__exit__.return_value = self._exit_return
        res.return_value = res.context
        return res

    def __exit__(self, type, value, tb):
        """Define exit function."""
        return self._patched.__exit__()


class testVerify(unittest.TestCase):
    """Verify.

    Testing verify functionalities.
    """

    def setUp(self):
        """Initialise fixtures."""
        self.env = EnvironmentVarGuard()
        self.env.set('LEGA_PASSWORD', 'value')
        self.env.set('QUALITY_CONTROL_VERIFY_CERTIFICATE', 'True')

    def tearDown(self):
        """Remove setup variables."""
        self.env.unset('LEGA_PASSWORD')
        self.env.unset('QUALITY_CONTROL_VERIFY_CERTIFICATE')

    @mock.patch('lega.verify.get_connection')
    @mock.patch('lega.verify.consume')
    def test_main(self, mock_consume, mock_connection):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()

    # @tempdir()
    # @mock.patch('lega.verify.db')
    # @mock.patch('lega.verify.body_decrypt')
    # @mock.patch('lega.verify.publish')
    # @mock.patch('lega.verify.get_records')
    # def test_work(self, mock_records, mock_publish, mock_decrypt, mock_db, filedir):
    #     """Test verify worker, should send a messge."""
    #     # Mocking a lot of stuff, ast it is previously tested
    #     mock_publish.return_value = mock.MagicMock()
    #     mock_db.status.return_value = mock.Mock()
    #     mock_records.return_value = ['data'], 'key_id'
    #     mock_decrypt.return_value = mock.Mock()
    #     store = mock.MagicMock()
    #     store.open.return_value = mock.MagicMock()
    #     mock_broker = mock.MagicMock(name='channel')
    #     mock_broker.channel.return_value = mock.Mock()
    #     infile = filedir.write('infile.in', 'text'.encode("utf-8"))
    #     data = {'header': pgp_data.ENC_FILE, 'stable_id': '1', 'vault_path': infile, 'file_id': '123', 'org_msg': {}}
    #     result = _work('10', store, mock_broker, data)
    #     self.assertTrue({'status': {'state': 'COMPLETED', 'details': '1'}}, result)
    #     filedir.cleanup()
