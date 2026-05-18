#include "task_utils.hpp"

#include <utility>

TaskResult makeTaskStub(
    std::string id,
    std::string title,
    std::string shortTitle,
    std::string problemKind,
    std::string method,
    std::string ownerHint,
    std::vector<TableColumn> columns,
    std::string implementationFile) {

    TaskResult task;
    task.id = std::move(id);
    task.title = std::move(title);
    task.shortTitle = std::move(shortTitle);
    task.problemKind = std::move(problemKind);
    task.method = std::move(method);
    task.ownerHint = std::move(ownerHint);
    task.status = "cpp_stub";
    task.note =
        "UI и backend-контракт готовы. Численную реализацию нужно добавить в файл " +
        implementationFile +
        ". Формат таблиц, JSON и графиков уже подключен к интерфейсу.";
    task.columns = std::move(columns);
    return task;
}

std::vector<TableColumn> makeTestTaskColumns() {
    return {
        {"j", "j"},
        {"i", "i"},
        {"x", "x_i"},
        {"y", "y_j"},
        {"u", "u*(x_i,y_j)"},
        {"v", "v(x_i,y_j)"},
        {"difference", "u*-v"}
    };
}

std::vector<TableColumn> makeMainTaskColumns() {
    return {
        {"j", "j"},
        {"i", "i"},
        {"x", "x_i"},
        {"y", "y_j"},
        {"v", "v на сетке (n,m)"},
        {"v2", "v2 на сетке (2n,2m)"},
        {"difference", "v-v2"}
    };
}
