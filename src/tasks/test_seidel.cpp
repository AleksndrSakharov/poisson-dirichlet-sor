#include "tasks/test_seidel.hpp"

#include "task_utils.hpp"

TaskResult runTestSeidelTask(const InputData&, const VariantData&) {
    return makeTaskStub(
        "test-seidel",
        "Тестовая задача, метод Зейделя",
        "1. Тест, Зейдель",
        "Тестовая задача Дирихле для уравнения Пуассона",
        "Метод Зейделя",
        "Папулина Юлия",
        makeTestTaskColumns(),
        "src/tasks/test_seidel.cpp");
}
