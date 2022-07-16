# from __future__ import annotations

# import sys
# import helper

# from fixtures import api


# def test_fund(api):
#     client, app = api

#     sys.path.append("src")

#     from model import db, Project, Fund, User

#     addr = "addr_test1qr70n9s9zhfw6p4valvvzc69e0eu7efxtjs6hu786f34rj0lawt235dpfa6sm7hfxevh22p5we3fthwjv5az4pcxr0kqhcndp6"
#     with app.app_context():
#         project: Project = helper.create_fake_project(db.session)
#         user: User = helper.create_fake_user(db.session, address=addr)

#         response = client.post(
#             f"/projects/{project.project_identifier}/fund?user={addr}&amount=5000000")

#         assert response.status_code == 200
#         assert response.json == {
#             "success": True,
#             "transaction_cbor": "<cbor>"
#         }

#         funds = Fund.query.all()
#         assert len(funds) == 1

#         fund: Fund = funds[0]
#         assert fund.funder_id == user.id
#         assert fund.project_id == project.id
        
#         assert fund.funding_amount == 5_000_000
#         assert fund.status == "draft"  

#         db.session.refresh(project)
#         db.session.refresh(user)

#         project_funding = project.project_funding
#         assert len(project_funding) == 1
#         assert project_funding[0].id == fund.id

#         user_funding = user.user_funding
#         assert len(user_funding) == 1
#         assert user_funding[0].id == fund.id
