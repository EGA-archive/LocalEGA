import unittest
from lega.ingest import main
from unittest import mock


class testIngest(unittest.TestCase):
    """Ingest

    Testing ingestion functionalities."""
    @mock.patch('lega.ingest.consume')
    def test_main(self, mock_consume):
        """Test main verify, by mocking cosume call."""
        mock_consume.return_value = mock.MagicMock()
        main()
        mock_consume.assert_called()
