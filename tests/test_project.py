# -*- coding: utf 8 -*-
"""
Define a suite a tests for the Project module.
"""
from urllib.error import URLError

import pytest

import welly
from welly import Project, Well


def test_project():
    """
    Test basic stuff.
    """
    project = Project.from_las('tests/assets/1.las')
    assert len(project) == 1

    w = Well.from_las('tests/assets/2.las')
    project += w
    assert w in project
    assert len(project) == 2

    project += project

    assert project.uwis[0] == '1'

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

    project.pop(2)
    assert len(project) == 3


def test_project_print(project, capsys):  # or use "capfd" for fd-level
    print(project)
    captured = capsys.readouterr()
    assert captured.out == "Long = 63* 45'24.460  W\n"


def test_filter_wells_by_data(project):
    """
    String should raise a warning. Should be an iterable
    """
    with pytest.warns(DeprecationWarning):
        project.filter_wells_by_data('string')


def test_get_wells(project):
    """
    Test `Project.get_wells()` method
    """
    # no keyword argument gets all wells
    assert len(project.get_wells()) == 1

    # get the only well in project
    assert len(project.get_wells(["Long = 63* 45'24.460  W"])) == 1
    assert isinstance(project.get_wells(["Long = 63* 45'24.460  W"]), Project)


def test_get_well(project):
    """
    Test `Project.get_well()` method
    """
    # need to specify `uwi` keyword
    with pytest.raises(TypeError):
        project.get_well()

    # get the only well in project
    assert isinstance(project.get_well("Long = 63* 45'24.460  W"), Well)


def test_merge_wells(project):
    """
    Test `Project.merge_wells()` method
    """
    project1 = welly.read_las('tests/assets/F03-02.las')
    project1[0].uwi = "Long = 63* 45'24.460  W"
    merged_project = project1.merge_wells(project)
    assert len(merged_project[0].data.values()) == 32


def test_omit_wells(project):
    """
    Test `Project.omit_wells()` method.
    """
    # need to specify `uwi` keyword
    with pytest.raises(ValueError):
        project.omit_wells()

    assert len(project.omit_wells(["Long = 63* 45'24.460  W"])) == 0


def test_data_as_matrix():
    """
    Test and method currently not working.
    """
    # alias = {'Sonic': ['DT', 'foo']}
    # project = Project.from_las('tests/assets/*.las')
    # X_train, y_train = project.data_as_matrix(X_keys=['DEPT', 'HCAL', 'Sonic'],
    #                                           y_key='CALI',
    #                                           alias=alias,
    #                                           window_length=1,
    #                                           remove_zeros=True)
    # # Test needs repair
    # assert X_train.shape[0] == y_train.size


def test_df():
    """
    Test transforming a project to a pd.DataFrame.
    """
    p = Project.from_las("tests/assets/P-129_out.LAS")
    alias = {'Gamma': ['GR', 'GRC', 'NGT'], 'Caliper': ['HCAL', 'CALI']}
    keys = ['Caliper', 'Gamma', 'DT']
    df = p.df(keys=keys, alias=alias)
    assert df.iloc[10, 1] - 46.69865036 < 0.001
    assert df.shape == (12718, 3)


def test_url_project():
    """
    Test loading a project through the URL. Requires internet connection.
    """
    try:
        url = 'https://www.nlog.nl/brh-web/rest/brh/logdocument/394951463'
        p = Project.from_las(url)
        assert len(p) == 1
    except URLError:
        # not connected to internet
        pass


def test_read_las():
    project = welly.read_las('tests/assets/1.las')
    assert len(project) == 1
