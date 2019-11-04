#pragma once

#include <dds/build/plan/compile_file.hpp>
#include <dds/build/source_dir.hpp>
#include <dds/library_manifest.hpp>
#include <dds/source.hpp>

#include <string>

namespace dds {

struct library_ident {
    std::string namespace_;
    std::string name;
};

class library {
    fs::path         _path;
    source_list      _sources;
    library_manifest _man;

    library(path_ref dir, source_list&& src, library_manifest&& man)
        : _path(dir)
        , _sources(std::move(src))
        , _man(std::move(man)) {}

public:
    static library from_directory(path_ref);

    auto& manifest() const noexcept { return _man; }

    source_directory src_dir() const noexcept { return source_directory{path() / "src"}; }
    source_directory include_dir() const noexcept { return source_directory{path() / "include"}; }

    path_ref path() const noexcept { return _path; }
    fs::path public_include_dir() const noexcept;
    fs::path private_include_dir() const noexcept;

    const source_list&        all_sources() const noexcept { return _sources; }
    shared_compile_file_rules base_compile_rules() const noexcept;
};

struct library_build_params {
    fs::path out_subdir;
    bool     build_tests     = false;
    bool     build_apps      = false;
    bool     enable_warnings = false;

    // Extras for compiling tests:
    std::vector<fs::path> test_include_dirs;
    std::vector<fs::path> test_link_files;
};

std::vector<library> collect_libraries(path_ref where);

}  // namespace dds