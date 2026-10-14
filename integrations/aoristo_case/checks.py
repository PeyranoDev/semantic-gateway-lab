"""Original/fixed HTTP regressions and real independent-session concurrency checks."""
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier

from integrations.aoristo.experiment import replay
from integrations.aoristo.model import Action, legitimate_seeds, uid
from integrations.aoristo.regressions import CASES

def headers(adapter, actor="alice"):
    return {"Authorization":"Bearer "+adapter.tokens[actor]}

def fixed_checks(adapter):
    report=[]
    for index, program in enumerate(legitimate_seeds()):
        trace=replay(adapter,program)
        assert not any(s["violations"] for s in trace), (index,trace)
        report.append({"case":f"legitimate-seed-{index}","passed":True})
    expected={"cancel_replay":[200,400],"read_foreign_sale":[404],"cancel_foreign_sale":[404],
              "revoke_foreign_invitation":[403],"create_foreign_invitation":[403],
              "create_own_invitation_response":[201],"list_own_invitation_response":[200]}
    for name,(program,_) in CASES.items():
        trace=replay(adapter,program)
        assert [s["response"]["status"] for s in trace] == expected[name], (name,trace)
        assert not any(s["violations"] for s in trace), (name,trace)
        report.append({"case":name,"statuses":expected[name],"passed":True})
    adapter.reset()
    response=adapter.client.post("/api/RedVecina/Invitations",headers=headers(adapter,"ruth"),
        json={"UnitId":str(uid(301)),"MaxUses":1,"ValidDays":1})
    assert response.status_code==201,response.text
    data=response.json()["data"]
    assert set(data)=={"Id","UnitId","Token","CurrentUses","MaxUses","ExpiresAt","CreatedAt"}
    assert data["UnitId"]==str(uid(301)) and data["CurrentUses"]==0 and data["MaxUses"]==1
    assert adapter.client.post("/api/RedVecina/Invitations/validate",json={"Token":data["Token"]}).status_code==200
    assert adapter.client.post("/api/RedVecina/Invitations/validate",json={"Token":data["Token"]}).status_code==400
    report.append({"case":"created-invitation-output-and-single-use","passed":True})

    from app.domain.models.profiles import RedVecinaProfile
    from app.domain.models.redvecina import Unit
    # Staff acts within the building; a resident remains restricted to their unit.
    adapter.reset()
    with adapter.Session() as session:
        session.add(Unit(Id=uid(303),BuildingId=uid(201),UnitNumber="extra"))
        session.query(RedVecinaProfile).filter(RedVecinaProfile.UserId==uid(103)).update({"Role":"staff","UnitId":None})
        session.commit()
    response=adapter.client.post("/api/RedVecina/Invitations",headers=headers(adapter,"ruth"),
        json={"UnitId":str(uid(303)),"MaxUses":1,"ValidDays":1})
    assert response.status_code==201,response.text
    identifier=response.json()["data"]["Id"]
    assert adapter.client.get("/api/RedVecina/Invitations",headers=headers(adapter,"ruth"),params={"unit_id":str(uid(303))}).status_code==200
    assert adapter.client.delete("/api/RedVecina/Invitations/"+identifier,headers=headers(adapter,"ruth")).status_code==200
    before=adapter.snapshot()
    assert adapter.client.post("/api/RedVecina/Invitations",headers=headers(adapter,"ruth"),
        json={"UnitId":str(uid(302)),"MaxUses":1,"ValidDays":1}).status_code==403
    assert adapter.snapshot()==before
    report.append({"case":"staff-building-scope","passed":True})
    adapter.reset()
    with adapter.Session() as session:
        session.query(RedVecinaProfile).filter(RedVecinaProfile.UserId==uid(103)).update({"Role":"unknown"})
        session.commit()
    before=adapter.snapshot()
    for method,path,kwargs in (
        ("POST","/api/RedVecina/Invitations",{"json":{"UnitId":str(uid(301)),"MaxUses":1,"ValidDays":1}}),
        ("GET","/api/RedVecina/Invitations",{"params":{"unit_id":str(uid(301))}}),
        ("DELETE","/api/RedVecina/Invitations/"+str(uid(601)),{})):
        assert adapter.client.request(method,path,headers=headers(adapter,"ruth"),**kwargs).status_code==403
    assert adapter.snapshot()==before
    report.append({"case":"unknown-role-fails-closed","passed":True})

    for status in ("completed","cancelled","refunded"):
        adapter.reset()
        with adapter.Session() as session:
            session.query(adapter.models["Sale"]).filter_by(Id=1).update({"Status":status})
            session.commit()
        before=adapter.snapshot()
        assert adapter.client.post("/api/Sales/1/cancel",headers=headers(adapter)).status_code==400
        assert adapter.snapshot()==before
    report.append({"case":"nonpending-sales-never-restore-stock","passed":True})
    adapter.reset()
    before=adapter.snapshot()
    assert adapter.client.get("/api/Sales/999",headers=headers(adapter)).status_code==404
    assert adapter.client.post("/api/Sales/999/cancel",headers=headers(adapter)).status_code==404
    assert adapter.snapshot()==before
    report.append({"case":"missing-sale-consistent-404","passed":True})
    return report

def purchase_scope_checks(adapter, variant):
    from app.domain.models.purchase import Purchase
    adapter.reset()
    with adapter.Session() as session:
        session.add_all([Purchase(Id=i,GroceryId=i,Total=6,Status="received",Notes="fixture") for i in (1,2)])
        session.commit()
    own=adapter.client.get("/api/Purchases/1",headers=headers(adapter))
    assert own.status_code==200,own.text
    foreign=adapter.client.get("/api/Purchases/2",headers=headers(adapter))
    update=adapter.client.put("/api/Purchases/2",headers=headers(adapter),json={"notes":"changed"})
    with adapter.Session() as session:
        notes=session.query(Purchase).filter_by(Id=2).one().Notes
    if variant=="fixed":
        assert (foreign.status_code,update.status_code,notes)==(404,404,"fixture")
        assert adapter.client.put("/api/Purchases/1",headers=headers(adapter),json={"notes":"own"}).status_code==200
    else:
        assert (foreign.status_code,update.status_code,notes)==(200,200,"changed")
    return {"case":"purchase-read-update-tenant-scope","variant":variant,
            "foreign_read":foreign.status_code,"foreign_update":update.status_code,"passed":True}

def transaction_checks(adapter):
    from sqlalchemy import event
    from sqlalchemy.orm import sessionmaker
    adapter.reset()
    before=adapter.snapshot()
    def fail_status_update(connection,cursor,statement,parameters,context,executemany):
        if statement.lstrip().startswith('UPDATE "Sales"'):
            raise RuntimeError("injected fixture failure after inventory restoration")
    event.listen(adapter.engine,"before_cursor_execute",fail_status_update)
    try:
        response=adapter.client.post("/api/Sales/1/cancel",headers=headers(adapter))
    finally:
        event.remove(adapter.engine,"before_cursor_execute",fail_status_update)
    assert response.status_code==500,response.text
    assert adapter.snapshot()==before, "Stock or sale status survived transaction rollback"
    report=[{"case":"failure-after-stock-update-rolls-back","passed":True}]

    # Commit fixtures, then serve concurrent HTTP calls with separate SQL sessions.
    # This check deliberately leaves serial savepoint isolation behind.
    adapter.reset()
    adapter.transaction.commit()
    adapter.transaction=None
    IndependentSession=sessionmaker(bind=adapter.engine)
    def independent_db():
        with IndependentSession() as session:
            yield session
    adapter.app.dependency_overrides[adapter.get_db]=independent_db
    barrier=Barrier(2)
    def synchronize_lock_attempts(connection,cursor,statement,parameters,context,executemany):
        if 'FROM "Sales"' in statement and "FOR UPDATE" in statement:
            barrier.wait(timeout=15)
    event.listen(adapter.engine,"before_cursor_execute",synchronize_lock_attempts)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=sorted(pool.map(lambda _:adapter.client.post("/api/Sales/1/cancel",headers=headers(adapter)).status_code, range(2)))
    finally:
        event.remove(adapter.engine,"before_cursor_execute",synchronize_lock_attempts)
    after=adapter.snapshot()
    assert statuses==[200,400],statuses
    assert after["inventory"]["1"]==10 and after["sales"]["a"]["status"]=="cancelled",after
    report.append({"case":"concurrent-http-cancellation-two-independent-sessions",
                   "statuses":statuses,"stock_after":10,"passed":True})
    return report
