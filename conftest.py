from pytest import fixture

from welly import Well


@fixture()
def well():
    return Well.from_las('tests/assets/P-129_out.LAS')
