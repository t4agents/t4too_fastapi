from fastapi import APIRouter

from app.api.r1_new_user_provision import newUserRou
from app.api.settings.be import beRou
from app.api.settings.client import clientRou
from app.api.settings.fee import feeRou
from app.api.settings.item import itemRou
from app.api.settings.payment_method import paymentMethodRou
from app.api.settings.seed import seedRou
from app.api.settings.tax import taxRou
from app.api.settings.userprofile import userProfileRou
from app.api.r2_dashboard import homeRou

rou = APIRouter()
rou.include_router(newUserRou)
rou.include_router(homeRou)
rou.include_router(userProfileRou)
rou.include_router(beRou)
rou.include_router(clientRou)
rou.include_router(taxRou)
rou.include_router(itemRou)
rou.include_router(paymentMethodRou)
rou.include_router(feeRou)
rou.include_router(seedRou)
