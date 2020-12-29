from dds_ci.dds import DDSWrapper
from dds_ci.testing import Project, RepoServer, PackageJSON
from dds_ci.testing.error import expect_error_marker
from dds_ci.testing.http import HTTPRepoServerFactory, RepoServer

import pytest

NEO_SQLITE_PKG_JSON = {
    'packages': {
        'neo-sqlite3': {
            '0.3.0': {
                'remote': {
                    'git': {
                        'url': 'https://github.com/vector-of-bool/neo-sqlite3.git',
                        'ref': '0.3.0',
                    }
                }
            }
        }
    }
}


@pytest.fixture(scope='session')
def _test_repo(http_repo_factory: HTTPRepoServerFactory) -> RepoServer:
    srv = http_repo_factory('test-pkg-db-repo')
    srv.import_json_data(NEO_SQLITE_PKG_JSON)
    return srv


def test_pkg_get(_test_repo: RepoServer, tmp_project: Project) -> None:
    _test_repo.import_json_data(NEO_SQLITE_PKG_JSON)
    tmp_project.dds.repo_add(_test_repo.url)
    tmp_project.dds.pkg_get('neo-sqlite3@0.3.0')
    assert tmp_project.root.joinpath('neo-sqlite3@0.3.0').is_dir()
    assert tmp_project.root.joinpath('neo-sqlite3@0.3.0/package.jsonc').is_file()


def test_pkg_repo(_test_repo: RepoServer, tmp_project: Project) -> None:
    dds = tmp_project.dds
    dds.repo_add(_test_repo.url)
    dds.run(['pkg', 'repo', dds.catalog_path_arg, 'ls'])


def test_pkg_repo_rm(_test_repo: RepoServer, tmp_project: Project) -> None:
    _test_repo.import_json_data(NEO_SQLITE_PKG_JSON)
    dds = tmp_project.dds
    dds.repo_add(_test_repo.url)
    # Okay:
    tmp_project.dds.pkg_get('neo-sqlite3@0.3.0')
    # Remove the repo:
    dds.run(['pkg', dds.catalog_path_arg, 'repo', 'ls'])
    dds.repo_remove(_test_repo.repo_name)
    # Cannot double-remove a repo:
    with expect_error_marker('repo-rm-no-such-repo'):
        dds.repo_remove(_test_repo.repo_name)
    # Now, fails:
    with expect_error_marker('pkg-get-no-pkg-id-listing'):
        tmp_project.dds.pkg_get('neo-sqlite3@0.3.0')


def test_pkg_search(_test_repo: RepoServer, tmp_project: Project) -> None:
    _test_repo.import_json_data(NEO_SQLITE_PKG_JSON)
    dds = tmp_project.dds
    with expect_error_marker('pkg-search-no-result'):
        dds.run(['pkg', dds.catalog_path_arg, 'search'])
    dds.repo_add(_test_repo.url)
    dds.run(['pkg', dds.catalog_path_arg, 'search'])
    dds.run(['pkg', dds.catalog_path_arg, 'search', 'neo-sqlite3'])
    dds.run(['pkg', dds.catalog_path_arg, 'search', 'neo-*'])
    with expect_error_marker('pkg-search-no-result'):
        dds.run(['pkg', dds.catalog_path_arg, 'search', 'nonexistent'])
