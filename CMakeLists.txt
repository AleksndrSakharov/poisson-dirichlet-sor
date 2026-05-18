cmake_minimum_required(VERSION 3.16)
project(poisson_dirichlet_sor LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(poisson_solver
    src/main.cpp
    src/solver.cpp
    src/task_utils.cpp
    src/tasks/test_seidel.cpp
    src/tasks/test_sor.cpp
    src/tasks/main_seidel.cpp
    src/tasks/main_sor.cpp
)

target_include_directories(poisson_solver PRIVATE include)

if(MSVC)
    target_compile_options(poisson_solver PRIVATE /utf-8)
endif()
