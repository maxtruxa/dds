import json
import tarfile
import pytest
from pathlib import Path

import platform

from bpt_ci.bpt import BPTWrapper
from bpt_ci.testing import ProjectOpener, Project, error, CRSRepo
from bpt_ci.util import read_tarfile_member


@pytest.fixture()
def test_project(project_opener: ProjectOpener) -> Project:
    return project_opener.open('projects/simple')


def test_create_pkg(test_project: Project, tmp_path: Path) -> None:
    # Create in the default location
    test_project.pkg_create()
    sd_dir = test_project.build_root / 'foo@1.2.3~1.tar.gz'
    assert sd_dir.is_file(), 'Did not create an sdist in the default location'
    # Create in a different location
    dest = tmp_path / 'dummy.tar.gz'
    test_project.pkg_create(dest=dest)
    assert dest.is_file(), 'Did not create an sdist in the new location'


def test_create_pkg_already_exists_fails(test_project: Project) -> None:
    test_project.pkg_create()
    with error.expect_error_marker('sdist-already-exists'):
        test_project.pkg_create()


def test_create_pkg_already_exists_fails_with_explicit_fail(test_project: Project) -> None:
    test_project.pkg_create()
    with error.expect_error_marker('sdist-already-exists'):
        test_project.pkg_create(if_exists='fail')


def test_create_pkg_already_exists_succeeds_with_ignore(test_project: Project) -> None:
    test_project.pkg_create()
    test_project.pkg_create(if_exists='ignore')


def test_create_pkg_already_exists_succeeds_with_replace(test_project: Project) -> None:
    sd_path: Path = test_project.build_root / 'foo@1.2.3~1.tar.gz'
    test_project.build_root.mkdir(exist_ok=True, parents=True)
    sd_path.touch()
    test_project.pkg_create(if_exists='replace')
    assert sd_path.stat().st_size > 0, 'Did not replace the existing file'


def test_sdist_invalid_project(tmp_project: Project) -> None:
    with error.expect_error_marker('no-pkg-meta-files'):
        tmp_project.pkg_create()


@pytest.mark.skipif(platform.system() != 'Linux', reason='We know this fails on Linux')
def test_sdist_unreadable_dir(bpt: BPTWrapper) -> None:
    with error.expect_error_marker('sdist-open-fail-generic'):
        bpt.run(['pkg', 'create', '--project=/root'])


def test_sdist_invalid_yml(tmp_project: Project) -> None:
    tmp_project.write('bpt.yaml', '[[')
    with error.expect_error_marker('package-yaml-parse-error'):
        tmp_project.pkg_create()


def test_pkg_search(tmp_crs_repo: CRSRepo, tmp_project: Project) -> None:
    with error.expect_error_marker('pkg-search-no-result'):
        tmp_project.bpt.run(['pkg', 'search', 'test-pkg', '-r', tmp_crs_repo.path])
    tmp_project.bpt_yaml = {
        'name': 'test-pkg',
        'version': '0.1.2',
    }
    tmp_crs_repo.import_(tmp_project.root)
    # No error now:
    tmp_project.bpt.run(['pkg', 'search', 'test-pkg', '-r', tmp_crs_repo.path])


def test_pkg_spdx(tmp_project: Project) -> None:
    tmp_project.bpt_yaml = {
        'name': 'foo',
        'version': '1.2.3',
        'license': 'MIT',
    }
    tmp_project.pkg_create()
    tmp_project.bpt_yaml['license'] = 'bogus'
    with error.expect_error_marker('invalid-spdx'):
        tmp_project.pkg_create()

    dest_tgz = tmp_project.root / 'test.tgz'
    tmp_project.bpt_yaml['license'] = 'MIT'
    tmp_project.pkg_create(dest=dest_tgz)
    with tarfile.open(dest_tgz) as tgz:
        pkg_json = json.loads(tgz.extractfile('pkg.json').read())
    assert 'meta' in pkg_json
    assert 'license' in pkg_json['meta']
    assert pkg_json['meta']['license'] == 'MIT'


def test_pkg_create_almost_valid(tmp_project: Project) -> None:
    pkg_data = {
        "name":
        "catch2",
        "version":
        "2.13.6",
        "pkg-version":
        1,
        "libraries": [{
            "name": "catch2",
            "path": ".",
            "using": [],
            "test-using": [],
            "dependencies": [],
            "test-dependencies": []
        }, {
            "name": "main",
            "path": "libs/main",
            "test-dependencies": [],
            "dependencies": [],
            "test-using": [],
            "using": [{
                "lib": "catch2"
            }]
        }],
        "schema-version":
        1
    }
    tmp_project.write('pkg.json', json.dumps(pkg_data))
    with error.expect_error_marker('invalid-pkg-json'):
        tmp_project.build()
    with error.expect_error_marker('invalid-pkg-json'):
        tmp_project.pkg_create()

    pkg_data['libraries'][1]['using'] = ['catch2']
    tmp_project.root.joinpath('libs/main').mkdir(parents=True)
    tmp_project.write('pkg.json', json.dumps(pkg_data))
    tmp_project.build()
    tmp_project.pkg_create()


def test_pkg_create_default_using(tmp_project: Project):
    tmp_project.bpt_yaml = {'name': 'foo', 'version': '1.2.3', 'dependencies': ['bar@4.1.3']}
    tmp_project.pkg_create()
    pkg_json = json.loads(read_tarfile_member(tmp_project.build_root / 'foo@1.2.3~1.tar.gz', 'pkg.json'))
    assert pkg_json['libraries'][0] == {
        'name': 'foo',
        'path': '.',
        'using': [],
        'test-using': [],
        'test-dependencies': [],
        'dependencies': [{
            'name': 'bar',
            'versions': [{
                'low': '4.1.3',
                'high': '5.0.0'
            }],
            'using': ['bar'],
        }]
    }
