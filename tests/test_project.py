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

    project += Well.from_las('tests/2.las')
    assert len(project) == 2
