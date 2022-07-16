# from __future__ import annotations

# import sys
# import helper

# from fixtures import api


# def test_get_all(api):
#     client, app = api

#     sys.path.append("src")

#     from model import db, Project

#     response = client.get("/projects")

#     assert response.status_code == 200
#     assert response.json == {
#         "count": 0,
#         "projects": []
#     }

#     with app.app_context():
#         project: Project = helper.create_fake_project(
#             db.session,
#             funding_achieved=13_000_000_000,
#             proposer_address="addr_test1qr70n9s9zhfw6p4valvvzc69e0eu7efxtjs6hu786f34rj0lawt235dpfa6sm7hfxevh22p5we3fthwjv5az4pcxr0kqhcndp6"
#         )
#         project_identifier = project.project_identifier

#     response = client.get(f"/projects/{project_identifier}")

#     assert response.status_code == 200
#     assert response.json == helper.samples.project_long_return
