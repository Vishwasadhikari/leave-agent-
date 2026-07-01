from datetime import datetime

from strands import tool

from app.services.dynamodb_service import db


@tool
def get_holidays():
    """
    Return all company holidays.
    """

    holidays = db.get_all_holidays()

    return {
        "success": True,
        "holidays": holidays
    }


@tool
def is_holiday(date: str):
    """
    Check whether a given date is a company holiday.
    Date format: YYYY-MM-DD
    """

    holiday = db.get_holiday(date)

    if holiday:
        return {
            "is_holiday": True,
            "holiday": holiday
        }

    return {
        "is_holiday": False
    }


@tool
def is_weekend(date: str):
    """
    Check if a date falls on Saturday or Sunday.
    Date format: YYYY-MM-DD
    """

    day = datetime.strptime(date, "%Y-%m-%d")

    if day.weekday() >= 5:
        return {
            "is_weekend": True
        }

    return {
        "is_weekend": False
    }