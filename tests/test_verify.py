import unittest
from lega.verify import main
from unittest import mock


class testVerify(unittest.TestCase):
    """Verify

    Testing verify functionalities."""

    @mock.patch('lega.verify.consume')
    def test_main(self, mock_consume):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
