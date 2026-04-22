from fastapi import APIRouter, Depends
from app.api.r_invoice import invoiceRou

from app.api.r1_new_user_only import newUserRou
from app.api.r2_zme import zmeRou
from app.api.r3_be import beRou

from app.api.r7_payroll_entry import entryRou
from app.api.r6_payroll_history import historyRou
from app.api.r5_payroll_schedule import scheduleRow
from app.api.r4_employee import employeeRou
from app.api.r_stripe import stripeRou

from app.api.ai_rag import embRou
from app.api.ai_rag_eval import ragEvalRou
from app.api.ai_brain import routerRou
from app.api.ai_langgraph import langRou
from app.api.ai_guardrail import guardrailRou

rou = APIRouter()
rou.include_router(ragEvalRou, prefix="/rag-eval", tags=['ai.rag.eval'])
rou.include_router(guardrailRou, prefix="/guardrail", tags=['ai.guardrail'])

rou.include_router(langRou, prefix="/langgraph", tags=['ai.LangGraph'])
rou.include_router(routerRou, prefix="/brain", tags=['ai.agent'])
rou.include_router(embRou, prefix="/embedding", tags=['ai.embedding'])

rou.include_router(newUserRou, prefix="/newuseronly", tags=["1.Register. Create New User Only"])     #给自己用的，创建用户和企业账号的
rou.include_router(zmeRou, prefix="/zme", tags=["2.ZMe"])    
rou.include_router(beRou, prefix="/be", tags=["3. clients. Business Entity"])
rou.include_router(employeeRou, prefix="/employee", tags=["4.Employee"])
rou.include_router(scheduleRow, prefix="/schedule", tags=["5.Payroll Schedule"])
rou.include_router(historyRou, prefix="/history", tags=["6.Payroll History"])
rou.include_router(entryRou, prefix="/entry", tags=["7.Payroll Entry"])
rou.include_router(stripeRou, prefix="/stripe", tags=["Stripe Billing"])









































rou.include_router(invoiceRou, prefix="/invoice", tags=["Invoice"])     #给别人用的
