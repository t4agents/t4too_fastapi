from uuid import UUID
from datetime import date, timedelta

TEMPLATE_PAYROLL_SCHEDULES = [
    # Weekly
    {
        "frequency": "weekly",
        "effective_from": date.today() - timedelta(days=date.today().weekday()),
        "effective_to":   date.max,
        "status": "inactive",
        "description": "Description",

        "payon": "Friday",
        "semi1": None,
        "semi2": None,
        "period": "Mon-Fri",
        "note": "From Monday to Friday.",
    },

    # Biweekly
    {
        "frequency": "biweekly",
        "effective_from": date.today() - timedelta(days=date.today().weekday()),
        "effective_to":   date.max,
        "status": "inactive",
        "description": "Description",

        "payon": "Friday",
        "semi1": None,
        "semi2": None,
        "period": "Mon-Fri (2 weeks)",
        "note": "Pays every other week.",
    },

    # Semimonthly
    {
        "frequency": "semimonthly",
        "effective_from": date.today().replace(day=1),
        "effective_to":   date.max,
        "status": "inactive",
        "description": "Description",

        "payon": None,
        "semi1": "15",
        "semi2": "EOM",
        "period": "1st-15th, 16th-EOM",
        "note": "Pays twice a month.",
    },

    # Monthly
    {
        "frequency": "monthly",
        "effective_from": date.today().replace(day=1),
        "effective_to":   date.max,
        "status": "active",
        "description": "Description",

        "payon": "EOM",
        "semi1": None,
        "semi2": None,
        "period": "1st-EOM",
        "note": "Pays once a month.",},
]


SEED_PAYROLL_SCHEDULES = [
    {
        "id": UUID("00000000-0000-0000-0000-000000000101"),
        "ten_id": None,
        "biz_id": None,
        "owner_id": None,
        "created_by": None,
        **TEMPLATE_PAYROLL_SCHEDULES[0],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000102"),
        "ten_id": None,
        "biz_id": None,
        "owner_id": None,
        "created_by": None,
        **TEMPLATE_PAYROLL_SCHEDULES[1],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000103"),
        "ten_id": None,
        "biz_id": None,
        "owner_id": None,
        "created_by": None,
        **TEMPLATE_PAYROLL_SCHEDULES[2],
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000104"),
        "ten_id": None,
        "biz_id": None,
        "owner_id": None,
        "created_by": None,
        **TEMPLATE_PAYROLL_SCHEDULES[3],
    },
]
