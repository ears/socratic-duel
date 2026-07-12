import datetime
import pytest
from app.agent import LAST_PRICE_UPDATE

def test_pricing_updated_recently():
    """
    Ensures that the hardcoded GEMINI_PRICING in app/agent.py is reviewed 
    and updated at least every 30 days to prevent cost estimation drift.
    """
    last_update = datetime.datetime.strptime(LAST_PRICE_UPDATE, "%Y-%m-%d").date()
    today = datetime.date.today()
    
    days_since_update = (today - last_update).days
    
    assert days_since_update <= 30, (
        f"The GEMINI_PRICING in app/agent.py was last updated {days_since_update} days ago. "
        "Please review the prices against the official Gemini API pricing page, "
        "update them if necessary, and bump the LAST_PRICE_UPDATE date."
    )
