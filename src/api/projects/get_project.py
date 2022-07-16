from model import Project
from lib import api_tools


def get_project(project_id):
    project = Project.query.filter(Project.project_identifier == project_id).first()

    if project is None:
        return {}, 404
    
    return api_tools.parse_project_long(project)