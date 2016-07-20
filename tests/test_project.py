# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Project module.
"""
from welly import Project, Well


def test_project():
    """
    Test basic stuff.
    """
    project = Project.from_las('tests/1.las')
    assert len(project) == 1

    w = Well.from_las('tests/2.las')
    project += w
    assert w in p
    assert len(project) == 2

    project += project

    assert project.uwis[0] == '1'

    s = "<table><tr><th>UWI</th><th>Data</th><th>Curves</th></tr><tr><td>300A524400060300</td>"
    assert s in p._repr_html_()

    assert p[1] == w
