#include "tasks/test_sor.hpp"

#include "task_utils.hpp"

TaskResult runTestSorTask(const InputData&, const VariantData&) {
    return makeTaskStub(
        "test-sor",
        "Тестовая задача, метод верхней релаксации",
        "2. Тест, МВР",
        "Тестовая задача Дирихле для уравнения Пуассона",
        "Метод верхней релаксации",
        "Романова Василиса",
        makeTestTaskColumns(),
        "src/tasks/test_sor.cpp");
}
