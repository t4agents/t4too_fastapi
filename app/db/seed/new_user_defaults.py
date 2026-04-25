from __future__ import annotations

from datetime import date, timedelta

NEW_USER_DEFAULTS = {
    "email": "invoaice@gmail.com",
    "name": "Invoaice Agents",
    "usr_type": "usr_type",
    "firstName": "Invoaice",
    "lastName": "Agents",
    "avatar": "https://raw.githubusercontent.com/ainvoaice/ainvoAIce/refs/heads/main/entrepreneurs.jpg",
    "phone": "332-203-4114",
    "position": "CPA",
    "facebook": "https://facebook.com/invoaice",
    "twitter": "https://twitter.com/invoaice",
    "github": "https://github.com/invoaice",
    "reddit": "https://reddit.com/u/invoaice",
    "country": "Canada",
    "state": "Ontario",
    "pin": "3322034114",
    "zip": "M5V 2T6",
    "taxNo": "invoaice123",
}


def default_payroll_schedule_templates() -> list[dict[str, object]]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    return [
        {
            "frequency": "weekly",
            "effective_from": week_start,
            "effective_to": date.max,
            "status": "inactive",
            "description": "Description",
            "payon": "Friday",
            "semi1": "EOM",
            "semi2": "EOM",
            "period": "Mon-Fri",
            "note": "From Monday to Friday.",
        },
        {
            "frequency": "biweekly",
            "effective_from": week_start,
            "effective_to": date.max,
            "status": "inactive",
            "description": "Description",
            "payon": "Friday",
            "semi1": "EOM",
            "semi2": "EOM",
            "period": "Mon-Fri (2 weeks)",
            "note": "Pays every other week.",
        },
        {
            "frequency": "semimonthly",
            "effective_from": month_start,
            "effective_to": date.max,
            "status": "inactive",
            "description": "Description",
            "payon": "EOM",
            "semi1": "15",
            "semi2": "EOM",
            "period": "1st-15th, 16th-EOM",
            "note": "Pays twice a month.",
        },
        {
            "frequency": "monthly",
            "effective_from": month_start,
            "effective_to": date.max,
            "status": "active",
            "description": "Description",
            "payon": "EOM",
            "semi1": "EOM",
            "semi2": "EOM",
            "period": "1st-EOM",
            "note": "Pays once a month.",
        },
    ]
