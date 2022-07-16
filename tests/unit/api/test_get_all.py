# import sys
# import helper

# from fixtures import api


# def test_get_all(api):
#     client, app = api

#     sys.path.append("src")

#     from model import db

#     response = client.get("/projects")

#     assert response.status_code == 200
#     assert response.json == {
#         "count": 0,
#         "projects": []
#     }

#     with app.app_context():
#         helper.create_fake_project(db.session)

#     response = client.get("/projects")

#     assert response.status_code == 200
#     assert response.json == {
#         "count": 1,
#         "projects": [{
#             "name": "Project Name",
#             "short_description": "Vry sht dscpt",
#             "funding_currency": "ADA",
#             "funding_achieved": 0,
#             "funding_expected": 100_000_000_000,
#             "project_proposer": "addr_test123",
#         }]
#     }
