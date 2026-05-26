"""
Indian Events endpoint — festival calendar + demand impact predictions.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.schemas.schemas import EventResponse, UpcomingEventsResponse

router = APIRouter()

# Full Indian event calendar (CHANGE 7 — surfaced prominently)
INDIAN_EVENTS_CALENDAR = [
    {"id": 1, "event_name": "Navratri", "event_type": "festival", "start_date": "2026-10-01",
     "end_date": "2026-10-09", "magnitude": 3, "categories": ["Snacks", "Dairy", "Beverages", "Devotional"]},
    {"id": 2, "event_name": "Dussehra", "event_type": "festival", "start_date": "2026-10-10",
     "end_date": "2026-10-10", "magnitude": 3, "categories": ["Snacks", "Sweets"]},
    {"id": 3, "event_name": "Diwali", "event_type": "festival", "start_date": "2026-10-29",
     "end_date": "2026-11-02", "magnitude": 3, "categories": ["Snacks", "Dairy", "Bakery", "Household", "Gifting"]},
    {"id": 4, "event_name": "Uttarayan / Makar Sankranti", "event_type": "festival", "start_date": "2027-01-14",
     "end_date": "2027-01-15", "magnitude": 2, "categories": ["Snacks", "Dairy", "Sesame"]},
    {"id": 5, "event_name": "Republic Day", "event_type": "holiday", "start_date": "2027-01-26",
     "end_date": "2027-01-26", "magnitude": 2, "categories": ["Beverages", "Snacks"]},
    {"id": 6, "event_name": "Holi", "event_type": "festival", "start_date": "2027-03-14",
     "end_date": "2027-03-15", "magnitude": 3, "categories": ["Dairy", "Snacks", "Beverages", "Colours"]},
    {"id": 7, "event_name": "Eid-ul-Fitr", "event_type": "festival", "start_date": "2027-03-30",
     "end_date": "2027-03-31", "magnitude": 2, "categories": ["Snacks", "Dairy", "Bakery", "Dry Fruits"]},
    {"id": 8, "event_name": "IPL Season Start", "event_type": "cricket", "start_date": "2027-03-22",
     "end_date": "2027-05-30", "magnitude": 2, "categories": ["Beverages", "Snacks", "Frozen Foods"]},
    {"id": 9, "event_name": "Janmashtami", "event_type": "festival", "start_date": "2026-08-25",
     "end_date": "2026-08-25", "magnitude": 2, "categories": ["Dairy", "Sweets"]},
    {"id": 10, "event_name": "Ganesh Chaturthi", "event_type": "festival", "start_date": "2026-09-07",
     "end_date": "2026-09-17", "magnitude": 2, "categories": ["Sweets", "Dairy", "Devotional"]},
    {"id": 11, "event_name": "Pongal", "event_type": "festival", "start_date": "2027-01-14",
     "end_date": "2027-01-17", "magnitude": 2, "categories": ["Dairy", "Cereals", "Jaggery"]},
    {"id": 12, "event_name": "Big Billion Day", "event_type": "sale_event", "start_date": "2026-10-15",
     "end_date": "2026-10-20", "magnitude": 2, "categories": ["Personal Care", "Household", "Snacks"]},
    {"id": 13, "event_name": "Independence Day", "event_type": "holiday", "start_date": "2026-08-15",
     "end_date": "2026-08-15", "magnitude": 2, "categories": ["Beverages", "Snacks"]},
    {"id": 14, "event_name": "Raksha Bandhan", "event_type": "festival", "start_date": "2026-08-08",
     "end_date": "2026-08-08", "magnitude": 2, "categories": ["Sweets", "Gifting", "Snacks"]},
]


@router.get("/upcoming", response_model=UpcomingEventsResponse)
async def get_upcoming_events(
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get next 30 days of Indian festivals/events with predicted demand impact.

    This is the core India-first differentiator — make it prominent.
    """
    today = datetime.now().date()
    thirty_days = today + timedelta(days=30)

    events = []
    for evt in INDIAN_EVENTS_CALENDAR:
        start = datetime.strptime(evt["start_date"], "%Y-%m-%d").date()
        days_until = (start - today).days

        # Include events within 60 days (upcoming + recently passed for reference)
        if -7 <= days_until <= 60:
            impact = "High" if evt["magnitude"] >= 3 else "Medium" if evt["magnitude"] >= 2 else "Low"
            events.append(EventResponse(
                id=evt["id"],
                event_name=evt["event_name"],
                event_type=evt["event_type"],
                start_date=evt["start_date"],
                end_date=evt["end_date"],
                magnitude=evt["magnitude"],
                days_until=max(days_until, 0),
                demand_categories=evt["categories"],
                predicted_impact=impact,
            ))

    # Sort by days_until
    events.sort(key=lambda e: e.days_until)

    return UpcomingEventsResponse(events=events, total=len(events))
