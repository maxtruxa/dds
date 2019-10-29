#pragma once

#include <dds/build/plan/full.hpp>

#include <range/v3/view/concat.hpp>
#include <range/v3/view/filter.hpp>
#include <range/v3/view/join.hpp>
#include <range/v3/view/transform.hpp>

namespace dds {

inline auto iter_libraries(const build_plan& plan) {
    return                                                    //
        plan.packages()                                       //
        | ranges::views::transform(&package_plan::libraries)  //
        | ranges::views::join                                 //
        ;
}

inline auto iter_compilations(const build_plan& plan) {
    auto lib_compiles =                                                                        //
        iter_libraries(plan)                                                                   //
        | ranges::views::transform(&library_plan::create_archive)                              //
        | ranges::views::filter([&](auto&& opt) { return bool(opt); })                         //
        | ranges::views::transform([&](auto&& opt) -> auto& { return opt->compile_files(); })  //
        | ranges::views::join                                                                  //
        ;

    auto exe_compiles =                                                       //
        iter_libraries(plan)                                                  //
        | ranges::views::transform(&library_plan::executables)                //
        | ranges::views::join                                                 //
        | ranges::views::transform(&link_executable_plan::main_compile_file)  //
        ;

    return ranges::views::concat(lib_compiles, exe_compiles);
}

}  // namespace dds