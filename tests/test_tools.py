"""Unit tests for agent tools."""

import pytest
from unittest.mock import Mock, patch
from src.tools import (
    create_change_request,
    validate_change_request,
    check_calendar_conflicts,
)


class TestAzureDevOpsTools:
    """Tests for Azure DevOps integration tools."""

    @patch("src.tools.azure_devops_tool.azure_devops_auth")
    def test_create_change_request_success(self, mock_auth):
        """Test successful CR creation."""
        # Mock the API response
        mock_auth.call_api.return_value = {
            "id": 12345,
            "_links": {"html": {"href": "https://dev.azure.com/org/project/_workitems/12345"}},
        }

        result = create_change_request(
            title="Test CR",
            description="Test description",
            scheduled_time="2025-10-25T18:00:00Z",
            duration_hours=2,
            requester_email="test@example.com",
        )

        assert result["status"] == "success"
        assert result["cr_id"] == "CR12345"
        assert "url" in result

    @patch("src.tools.azure_devops_tool.azure_devops_auth")
    def test_validate_change_request_missing_fields(self, mock_auth):
        """Test validation with missing required fields."""
        # Mock CR with missing fields
        mock_auth.call_api.return_value = {
            "fields": {
                "System.Title": "Test CR",
                # Missing description, scheduled_time, duration
            }
        }

        result = validate_change_request("CR12345")

        assert result["valid"] is False
        assert len(result["issues"]) > 0


class TestCalendarTools:
    """Tests for calendar integration tools."""

    @patch("src.tools.calendar_tool.microsoft_auth")
    def test_check_calendar_no_conflicts(self, mock_auth):
        """Test calendar check with no conflicts."""
        # Mock empty calendar response
        mock_auth.call_graph_api.return_value = {"value": []}

        result = check_calendar_conflicts(
            user_email="test@example.com",
            start_time="2025-10-25T18:00:00Z",
            end_time="2025-10-25T20:00:00Z",
        )

        assert result["status"] == "success"
        assert result["has_conflicts"] is False
        assert result["conflict_count"] == 0

    @patch("src.tools.calendar_tool.microsoft_auth")
    def test_check_calendar_with_conflicts(self, mock_auth):
        """Test calendar check with conflicts."""
        # Mock calendar with events
        mock_auth.call_graph_api.return_value = {
            "value": [
                {
                    "subject": "Team Meeting",
                    "start": {"dateTime": "2025-10-25T18:30:00Z"},
                    "end": {"dateTime": "2025-10-25T19:30:00Z"},
                    "organizer": {"emailAddress": {"address": "manager@example.com"}},
                }
            ]
        }

        result = check_calendar_conflicts(
            user_email="test@example.com",
            start_time="2025-10-25T18:00:00Z",
            end_time="2025-10-25T20:00:00Z",
        )

        assert result["status"] == "success"
        assert result["has_conflicts"] is True
        assert result["conflict_count"] == 1
        assert len(result["conflicts"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
