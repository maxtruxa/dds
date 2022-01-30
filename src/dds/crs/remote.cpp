#include "./remote.hpp"

#include <dds/error/result.hpp>
#include <dds/temp.hpp>
#include <dds/util/fs/io.hpp>
#include <dds/util/fs/shutil.hpp>
#include <dds/util/http/pool.hpp>

#include <neo/scope.hpp>
#include <neo/tar/util.hpp>
#include <neo/ufmt.hpp>

#include <fstream>

using namespace dds;
using namespace dds::crs;

namespace {

neo::url calc_pkg_url(neo::url_view from, pkg_id pkg) {
    return from.normalized() / "pkg" / pkg.name.str
        / neo::ufmt("{}~{}", pkg.version.to_string(), pkg.pkg_revision) / "pkg.tgz";
}

void expand_tgz(path_ref tgz_path, path_ref into) {
    auto infile = dds::open_file(tgz_path, std::ios::binary | std::ios::in);
    fs::create_directories(into);
    neo::expand_directory_targz(
        neo::expand_options{
            .destination_directory = into,
            .input_name            = tgz_path.string(),
        },
        infile);
}

}  // namespace

void crs::pull_pkg_ar_from_remote(path_ref dest, neo::url_view from, pkg_id pkg) {
    auto tgz_url = calc_pkg_url(from, pkg);

    fs::create_directories(dest.parent_path());

    if (from.scheme == "file") {
        auto local_path = fs::path{tgz_url.path};
        dds::copy_file(local_path, dest).value();
        return;
    }

    auto tmp = dest.parent_path() / ".dds-download.tmp";
    neo_defer { std::ignore = ensure_absent(tmp); };

    {
        auto& pool   = http_pool::thread_local_pool();
        auto  reqres = pool.request(tgz_url);
        reqres.save_file(tmp);
    }

    dds::ensure_absent(dest).value();
    dds::move_file(tmp, dest).value();
}

void crs::pull_pkg_from_remote(path_ref expand_into, neo::url_view from, pkg_id pkg) {
    fs::path expand_tgz_path;
    if (from.scheme == "file") {
        // We can skip copying the tarball and just expand the one in the repository directly.
        fs::path tgz_path = calc_pkg_url(from, pkg).path;
        expand_tgz(tgz_path, expand_into);
    } else {
        // Create a tempdir, download into it, and expand that
        auto tmpdir   = dds::temporary_dir::create_in(expand_into.parent_path());
        auto tgz_path = tmpdir.path()
            / neo::ufmt("~{}@{}~{}.tgz", pkg.name.str, pkg.version.to_string(), pkg.pkg_revision);
        // Download:
        pull_pkg_ar_from_remote(tgz_path, from, pkg);
        // Expand:
        expand_tgz(tgz_path, expand_into);
    }
}
