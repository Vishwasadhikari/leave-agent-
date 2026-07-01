from app.tools.holiday_tools import (
    get_holidays,
    is_holiday,
    is_weekend
)

print("=" * 50)
print("Holiday Tool Test")
print("=" * 50)

print(get_holidays())
print()

print(is_holiday("2026-08-15"))
print()

print(is_holiday("2026-08-16"))
print()

print(is_weekend("2026-08-16"))