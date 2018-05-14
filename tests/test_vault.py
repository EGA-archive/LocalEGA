import unittest
from lega.vault import main
from unittest import mock


class testVault(unittest.TestCase):
    """Vault

    Testing vault functionalities."""

    @mock.patch('lega.vault.consume')
    def test_main(self, mock_consume):
        """Test main vault, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
