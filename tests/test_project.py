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
    assert w in project
    assert len(project) == 2

    project += project

    assert project.uwis[0] == 1

    s = "<table>"
    s += "<tr><th>Index</th><th>UWI</th><th>Data</th><th>Curves</th></tr>"
    s += "<tr><td>0</td><td><strong>1</strong></td>"
    assert s in project._repr_html_()

    # Check __getitem__.
    assert project[1] == w
    assert len(project[:2]) == 2
    l = [0, 1]
    assert len(project[l]) == 2

    assert len(project.get_mnemonics(['DT'])) == 4

    html = project.curve_table_html()
    assert '<table><tr><th>Idx</th><th>UWI</th><th>Data</th><th>Passing</th>' in html
    assert "<th>DPHI_SAN</th>" in html
    s = """<td style="background-color:#CCEECC; line-height:80%; padding:5px 4px 2px 4px;">DTS"""
    assert s in html


def test_data_as_matrix():
    alias = {'Sonic': ['DT', 'foo']}
    project = Project.from_las('tests/*.las')
    # X_train, y_train = project.data_as_matrix(X_keys=['DEPT', 'HCAL', 'Sonic'],
    #                                           y_key='CALI',
    #                                           alias=alias,
    #                                           window_length=1,
    #                                           remove_zeros=True,
    #                                           )
    # # Test needs repair
    # assert X_train.shape[0] == y_train.size
