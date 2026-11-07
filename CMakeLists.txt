cmake_minimum_required(VERSION 3.24)
project(factory LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "Build type" FORCE)
endif()

# --- shared warning / ABI profile --------------------------------------------
# One interface target so every module is compiled under identical rules: a
# warning that fails in one target must fail in every target (STYLE-*).
add_library(fct_flags INTERFACE)

if(MSVC)
    target_compile_options(fct_flags INTERFACE /W4 /WX /permissive- /GR-)
else()
    target_compile_options(fct_flags INTERFACE
        -Wall
        -Wextra
        -Wpedantic
        -Wshadow
        -Wnon-virtual-dtor
        -Wold-style-cast
        -Wcast-align
        -Woverloaded-virtual
        -Wdouble-promotion
        -Wformat=2
        -Wmissing-declarations
        -Wundef
        -Werror)
    # The engine never throws and never uses RTTI (STYLE-ERR-*, MEM-*).
    target_compile_options(fct_flags INTERFACE -fno-exceptions -fno-rtti)
endif()

# --- modules -----------------------------------------------------------------
add_library(fct_core STATIC
    src/core/log.cpp
    src/core/version.cpp)
target_include_directories(fct_core PUBLIC src)
target_link_libraries(fct_core PUBLIC fct_flags)

add_library(fct_sim STATIC
    src/sim/world.cpp)
target_link_libraries(fct_sim PUBLIC fct_core)

# Platform: SDL3 when present, otherwise the headless stub. Both satisfy
# src/platform/window.h, so nothing above this module notices the difference.
find_package(SDL3 CONFIG QUIET)

add_library(fct_platform STATIC
    src/platform/time.cpp)
target_link_libraries(fct_platform PUBLIC fct_core)

if(SDL3_FOUND)
    message(STATUS "SDL3 ${SDL3_VERSION} found: window backend enabled")
    target_sources(fct_platform PRIVATE src/platform/window_sdl.cpp)
    target_compile_definitions(fct_platform PUBLIC FCT_HAVE_SDL3=1)
    target_link_libraries(fct_platform PRIVATE SDL3::SDL3)
else()
    message(WARNING "SDL3 not found: building the headless platform stub")
    target_sources(fct_platform PRIVATE src/platform/window_stub.cpp)
    target_compile_definitions(fct_platform PUBLIC FCT_HAVE_SDL3=0)
endif()

# RHI: the device and swap chain contract plus the headless backend. The GL
# backend (rhi/gl) is added with SDL3, next to the window backend, so a build
# without a GPU still links a working device.
add_library(fct_rhi STATIC
    src/rhi/device.cpp
    src/rhi/null_device.cpp)
target_link_libraries(fct_rhi PUBLIC fct_core)

add_executable(fct_app
    src/app/main.cpp)
target_link_libraries(fct_app PRIVATE fct_sim fct_platform fct_rhi)

# --- tests -------------------------------------------------------------------
add_executable(fct_tests
    tests/harness.cpp
    tests/unit/main.cpp
    tests/unit/test_core.cpp
    tests/unit/test_sim.cpp
    tests/unit/test_fixed_step.cpp
    tests/unit/test_log.cpp
    tests/unit/test_platform.cpp
    tests/unit/test_rhi.cpp)
target_include_directories(fct_tests PRIVATE tests)
target_link_libraries(fct_tests PRIVATE fct_sim fct_platform fct_rhi)

enable_testing()
add_test(NAME unit COMMAND fct_tests)
