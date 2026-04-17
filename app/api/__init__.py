from fastapi import APIRouter

from app.api.r1_new_user_provision import newUserRou
from app.api.r3_inv import invRou
from app.api.too.s2_be import beRou
from app.api.too.s3_client import clientRou
from app.api.too.fee import feeRou
from app.api.too.item import itemRou
from app.api.too.payment_method import paymentMethodRou
from app.api.too.seed import seedRou
from app.api.too.tax import taxRou
from app.api.too.s1_me import userProfileRou
from app.api.r2_dashboard import homeRou
from app.api.t4.t4_employee import employeeRou

rou = APIRouter(prefix="/too")
rou.include_router(invRou)
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
rou.include_router(employeeRou)
