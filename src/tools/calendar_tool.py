"""Microsoft Graph calendar integration tools."""

import sys
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import microsoft_auth, get_logger

logger = get_logger(__name__)


def check_calendar_conflicts(
    user_email: str, start_time: str, end_time: str
) -> Dict[str, Any]:
    """
    Check if a user has calendar conflicts during a specified time window.

    Args:
        user_email: Email address of the user to check.
        start_time: Start time in ISO format.
        end_time: End time in ISO format.

    Returns:
        Dictionary with conflict status and list of conflicting events.
    """
    logger.info(
        "Checking calendar conflicts",
        user=user_email,
        start_time=start_time,
        end_time=end_time,
    )

    try:
        # Build calendar view query
        endpoint = (
            f"/users/{user_email}/calendarView"
            f"?startDateTime={start_time}&endDateTime={end_time}"
        )

        result = microsoft_auth.call_graph_api(endpoint=endpoint, method="GET")

        events = result.get("value", [])
        conflicts = []

        for event in events:
            conflicts.append(
                {
                    "subject": event.get("subject"),
                    "start": event.get("start", {}).get("dateTime"),
                    "end": event.get("end", {}).get("dateTime"),
                    "organizer": event.get("organizer", {})
                    .get("emailAddress", {})
                    .get("address"),
                }
            )

        has_conflicts = len(conflicts) > 0

        logger.info(
            "Calendar check complete",
            user=user_email,
            has_conflicts=has_conflicts,
            conflict_count=len(conflicts),
        )

        return {
            "status": "success",
            "user": user_email,
            "has_conflicts": has_conflicts,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
        }

    except Exception as e:
        logger.error("Failed to check calendar", user=user_email, error=str(e))
        return {
            "status": "error",
            "user": user_email,
            "message": f"Failed to check calendar: {str(e)}",
        }


def get_team_availability(
    team_emails: List[str], start_time: str, duration_hours: int
) -> Dict[str, Any]:
    """
    Check availability for multiple team members during a time window.

    Args:
        team_emails: List of team member email addresses.
        start_time: Start time in ISO format.
        duration_hours: Duration in hours.

    Returns:
        Dictionary with availability status for each team member.
    """
    logger.info(
        "Checking team availability",
        team_size=len(team_emails),
        start_time=start_time,
        duration_hours=duration_hours,
    )

    # Calculate end time
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(hours=duration_hours)
    end_time = end_dt.isoformat()

    availability_results = {}

    for email in team_emails:
        result = check_calendar_conflicts(email, start_time, end_time)
        availability_results[email] = {
            "available": not result.get("has_conflicts", True),
            "conflicts": result.get("conflicts", []),
        }

    # Calculate overall availability
    all_available = all(
        member["available"] for member in availability_results.values()
    )

    logger.info(
        "Team availability check complete",
        all_available=all_available,
        team_size=len(team_emails),
    )

    return {
        "status": "success",
        "all_available": all_available,
        "team_availability": availability_results,
        "start_time": start_time,
        "end_time": end_time,
    }


def find_available_time_slots(
    user_email: str, date: str, duration_hours: int, business_hours_only: bool = True
) -> Dict[str, Any]:
    """
    Find available time slots for a user on a specific date.

    Args:
        user_email: Email address of the user.
        date: Date to check in YYYY-MM-DD format.
        duration_hours: Required duration in hours.
        business_hours_only: If True, only return slots during business hours (9 AM - 5 PM).

    Returns:
        Dictionary with list of available time slots.
    """
    logger.info(
        "Finding available time slots",
        user=user_email,
        date=date,
        duration_hours=duration_hours,
    )

    try:
        # Define search window
        if business_hours_only:
            start_time = f"{date}T09:00:00"
            end_time = f"{date}T17:00:00"
        else:
            start_time = f"{date}T00:00:00"
            end_time = f"{date}T23:59:59"

        # Get all events for the day
        endpoint = (
            f"/users/{user_email}/calendarView"
            f"?startDateTime={start_time}&endDateTime={end_time}"
        )

        result = microsoft_auth.call_graph_api(endpoint=endpoint, method="GET")
        events = result.get("value", [])

        # Sort events by start time
        events.sort(key=lambda e: e.get("start", {}).get("dateTime", ""))

        # Find gaps between events
        available_slots = []
        current_time = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)

        for event in events:
            event_start = datetime.fromisoformat(
                event.get("start", {}).get("dateTime", "")
            )
            event_end = datetime.fromisoformat(
                event.get("end", {}).get("dateTime", "")
            )

            # Check if there's a gap before this event
            gap_duration = (event_start - current_time).total_seconds() / 3600

            if gap_duration >= duration_hours:
                available_slots.append(
                    {
                        "start": current_time.isoformat(),
                        "end": event_start.isoformat(),
                        "duration_hours": gap_duration,
                    }
                )

            current_time = max(current_time, event_end)

        # Check for gap after last event
        final_gap = (end_dt - current_time).total_seconds() / 3600
        if final_gap >= duration_hours:
            available_slots.append(
                {
                    "start": current_time.isoformat(),
                    "end": end_dt.isoformat(),
                    "duration_hours": final_gap,
                }
            )

        logger.info(
            "Available slots found",
            user=user_email,
            slot_count=len(available_slots),
        )

        return {
            "status": "success",
            "user": user_email,
            "date": date,
            "available_slots": available_slots,
            "slot_count": len(available_slots),
        }

    except Exception as e:
        logger.error("Failed to find available slots", user=user_email, error=str(e))
        return {
            "status": "error",
            "user": user_email,
            "message": f"Failed to find available slots: {str(e)}",
        }
