from pytest import fixture

from welly import Project


@fixture()
def project():
    return Project.from_las('tests/assets/P-129_out.LAS')


@fixture()
def well(project):
    return project[0]


@fixture()
def curve(well):
    return well.data['GR']
