import unittest
from unittest.mock import patch, MagicMock
import script


class TestAccessAutomation(unittest.TestCase):
    @patch('script.requests.get')
    @patch('script.requests.post')
    @patch('script.send_email')
    def test_main(self, mock_send_email, mock_post, mock_get):
        # Mock JIRA response for GET
        mock_jira_response = MagicMock()
        mock_jira_response.json.return_value = {
            "issues": [
                {
                    "key": "TEST-123",
                    "fields": {
                        "customfield_12305": "John Doe",
                        "customfield_12420": "john.doe@example.com",
                        "customfield_12477": "1234567890",
                        "customfield_12334": "Admin"
                    }
                }
            ]
        }
        mock_jira_response.status_code = 200
        mock_get.return_value = mock_jira_response

        # Mock POST responses
        mock_add_user_response = MagicMock()
        mock_add_user_response.status_code = 201

        mock_comment_response = MagicMock()
        mock_comment_response.status_code = 201

        mock_transition_response = MagicMock()
        mock_transition_response.status_code = 204

        mock_post.side_effect = [
            mock_add_user_response,
            mock_comment_response,
            mock_transition_response
        ]

        # Mock send_email behavior
        mock_send_email.return_value = None

        # Execute the function under test
        script.main()

        # Verify calls
        self.assertEqual(mock_get.call_count, 1)  # Ensure JIRA GET call was made
        self.assertEqual(mock_post.call_count, 3)  # Ensure 3 POST calls were made
        mock_send_email.assert_called_once_with("john.doe@example.com", unittest.mock.ANY)  # Verify email was sent


if __name__ == '__main__':
    unittest.main()
