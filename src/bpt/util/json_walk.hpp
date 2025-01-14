#pragma once

#include <bpt/dym.hpp>
#include <bpt/util/parse_enum.hpp>
#include <bpt/util/string.hpp>

#include <boost/leaf/exception.hpp>
#include <json5/data.hpp>
#include <magic_enum.hpp>
#include <neo/assert.hpp>
#include <neo/tl.hpp>
#include <neo/ufmt.hpp>
#include <semester/walk.hpp>

#include <ranges>

namespace semver {
struct version;
}

namespace bpt {
struct name;
}

namespace bpt::walk_utils {

using namespace semester::walk_ops;
using semester::walk_error;

using json5_mapping   = json5::data::mapping_type;
using json5_array     = json5::data::array_type;
using require_mapping = semester::require_type<json5_mapping>;
using require_array   = semester::require_type<json5_array>;
using require_str     = semester::require_type<std::string>;

struct name_from_string {
    bpt::name operator()(std::string s);
};

struct version_from_string {
    semver::version operator()(std::string s);
};

struct key_dym_tracker {
    std::set<std::string_view, std::less<>> known_keys;
    std::set<std::string, std::less<>>      seen_keys = {};

    auto tracker() {
        return [this](auto&& key, auto&&) {
            seen_keys.emplace(std::string(key));
            return walk.pass;
        };
    }

    template <typename E>
    auto rejecter() {
        return [this](auto&& key, auto &&) -> semester::walk_result {
            auto unseen
                = known_keys | std::views::filter([&](auto k) { return !seen_keys.contains(k); });
            BOOST_LEAF_THROW_EXCEPTION(E{std::string(key), did_you_mean(key, unseen)});
            neo::unreachable();
        };
    }
};

struct reject_with_known {};

}  // namespace bpt::walk_utils
