#include "tasks/main_sor.hpp"

#include "task_utils.hpp"

TaskResult runMainSorTask(const InputData&, const VariantData&) {
    return makeTaskStub(
        "main-sor",
        "Основная задача, метод верхней релаксации",
        "4. Основная, МВР",
        "Основная задача Дирихле для уравнения Пуассона",
        "Метод верхней релаксации",
        "Курпяков Алексей",
        makeMainTaskColumns(),
        "src/tasks/main_sor.cpp");
}
