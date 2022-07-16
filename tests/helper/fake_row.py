import sys


sys.path.append("src")


def create_fake_user(session, **args):

    from model import User

    user = User()

    if "id" in args:
        user.id = args["id"]

    if "user_identifier" in args:
        user.user_identifier = args["user_identifier"]

    user.user_address = "addr_test123" if not "address" in args else args["address"]
    user.user_public_key_hash = "pubkeyhash123" if not "public_key_hash" in args else args[
        "public_key_hash"]

    session.add(user)
    session.commit()

    session.refresh(user)

    return user


def create_fake_project(session, **args):

    from model import Project, User, Judge, Deliverable, ProjectState

    project = Project()

    # Add proposer
    proposer = User()

    if "proposer_address" in args:
        proposer.user_address = args["proposer_address"]
    else:
        proposer.user_address = "addr_test123"

    if "proposer_public_key_hash" in args:
        proposer.user_public_key_hash = args["proposer_public_key_hash"]
    else:
        proposer.user_public_key_hash = "pubkeyhash123"

    project.proposer = proposer

    # Project Name
    if "name" in args:
        project.name = args["name"]
    else:
        project.name = "Project Name"

    # Descriptions
    if "short_description" in args:
        project.short_description = args["short_description"]
    else:
        project.short_description = "Vry sht dscpt"

    if "long_description" in args:
        project.long_description = args["long_description"]
    else:
        project.long_description = "Veeeery loooooong descriiiiiiiiptioon"

    # Funding
    if "funding_currency" in args:
        project.funding_currency = args["funding_currency"]
    else:
        project.funding_currency = "ADA"

    if "funding_achieved" in args:
        project.funding_achieved = args["funding_achieved"]
    else:
        project.funding_achieved = 0

    if "funding_expected" in args:
        project.funding_expected = args["funding_expected"]
    else:
        project.funding_expected = 100_000_000_000

    # Deliverables
    if "deliverables" in args:
        project.deliverables = []
        for deliverable in args["deliverables"]:
            if not "declaration" in deliverable:
                raise ValueError(
                    "Deliverables formated incorrectly, missing declaration key!")

            if not "duration" in deliverable:
                raise ValueError(
                    "Deliverables formated incorrectly, missing duration key!")

            if not "percentage_requested" in deliverable:
                raise ValueError(
                    "Deliverables formated incorrectly, missing percentage_requested key!")

            deliverable = Deliverable()

            deliverable.declaration = deliverable["declaration"]
            deliverable.duration = deliverable["duration"]
            deliverable.percentage_requested = deliverable["percentage_requested"]

            project.deliverables.append(deliverable)
    else:
        deliverable = Deliverable()
        deliverable.declaration = "I will do a very good project"
        deliverable.duration = 5
        deliverable.percentage_requested = 100

        project.deliverables = [deliverable]

    # Judges
    if "judges" in args:
        project.judges = []
        for judge in args["judges"]:
            if not "address" in judge:
                raise ValueError(
                    "judges formated incorrectly, missing address key!")

            judge = Judge()
            judge.judge_address = judge["address"]

            project.judges.append(judge)
    else:
        judge_1 = Judge()
        judge_1.judge_address = "addr_test456"

        judge_2 = Judge()
        judge_2.judge_address = "addr_test789"

        project.judges = [judge_1, judge_2]

    # Project State
    if "project_state" in args:
        project_state = ProjectState()

        if not "state" in args["project_state"]:
            raise ValueError(
                "project state formated incorrectly, missing state key!")

        project_state.state = args["project_state"]["state"]

        project.project_state = project_state
    else:
        project_state = ProjectState()
        project_state.state = "draft"

        project.project_state = project_state

    session.add(project)
    session.commit()

    session.refresh(project)

    return project
