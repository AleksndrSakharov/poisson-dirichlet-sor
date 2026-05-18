#include "solver.hpp"

#include "tasks/main_seidel.hpp"
#include "tasks/main_sor.hpp"
#include "tasks/test_seidel.hpp"
#include "tasks/test_sor.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace {

std::string readTextFile(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("Cannot open input file: " + path);
    }
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return buffer.str();
}

double parseNumber(const std::string& text, const std::string& key, double fallback) {
    const std::string needle = "\"" + key + "\"";
    size_t pos = text.find(needle);
    if (pos == std::string::npos) {
        return fallback;
    }

    pos = text.find(':', pos);
    if (pos == std::string::npos) {
        return fallback;
    }
    ++pos;

    while (pos < text.size() && std::isspace(static_cast<unsigned char>(text[pos]))) {
        ++pos;
    }

    size_t end = pos;
    while (end < text.size()) {
        const char ch = text[end];
        const bool numeric =
            std::isdigit(static_cast<unsigned char>(ch)) || ch == '.' || ch == '-' || ch == '+' || ch == 'e' || ch == 'E';
        if (!numeric) {
            break;
        }
        ++end;
    }

    if (end == pos) {
        return fallback;
    }
    return std::stod(text.substr(pos, end - pos));
}

int parseInt(const std::string& text, const std::string& key, int fallback) {
    return static_cast<int>(std::llround(parseNumber(text, key, static_cast<double>(fallback))));
}

std::string escapeJson(const std::string& text) {
    std::string out;
    out.reserve(text.size());
    for (char ch : text) {
        switch (ch) {
            case '\\':
                out += "\\\\";
                break;
            case '"':
                out += "\\\"";
                break;
            case '\n':
                out += "\\n";
                break;
            case '\r':
                out += "\\r";
                break;
            case '\t':
                out += "\\t";
                break;
            default:
                out += ch;
                break;
        }
    }
    return out;
}

void validateInput(InputData& input) {
    if (input.n < 2 || input.m < 2) {
        throw std::runtime_error("n and m must be at least 2");
    }
    if (input.tolerance <= 0.0 || input.methodTolerance <= 0.0) {
        throw std::runtime_error("tolerances must be positive");
    }
    if (input.maxIterations <= 0) {
        throw std::runtime_error("maxIterations must be positive");
    }
    if (input.maxN < input.n || input.maxM < input.m) {
        throw std::runtime_error("maxN/maxM must be greater than or equal to n/m");
    }
    if (input.tableStrideX <= 0) {
        input.tableStrideX = 1;
    }
    if (input.tableStrideY <= 0) {
        input.tableStrideY = 1;
    }
    if (input.omega <= 0.0 || input.omega >= 2.0) {
        input.omega = 1.7;
    }
}

void writeColumnsJson(std::ostream& out, const std::vector<TableColumn>& columns) {
    out << "[";
    for (size_t i = 0; i < columns.size(); ++i) {
        if (i > 0) {
            out << ",";
        }
        out << "{\"key\":\"" << escapeJson(columns[i].key) << "\",\"title\":\"" << escapeJson(columns[i].title) << "\"}";
    }
    out << "]";
}

void writeRowsJson(std::ostream& out, const std::vector<TableRow>& rows) {
    out << "[";
    for (size_t n = 0; n < rows.size(); ++n) {
        const TableRow& row = rows[n];
        if (n > 0) {
            out << ",";
        }
        out << "{"
            << "\"i\":" << row.i << ","
            << "\"j\":" << row.j << ","
            << "\"x\":" << std::setprecision(16) << row.x << ","
            << "\"y\":" << row.y << ","
            << "\"u\":" << row.u << ","
            << "\"v\":" << row.v << ","
            << "\"v2\":" << row.v2 << ","
            << "\"difference\":" << row.difference
            << "}";
    }
    out << "]";
}

void writeTaskJson(std::ostream& out, const TaskResult& task) {
    out << "{\n";
    out << "\"id\":\"" << escapeJson(task.id) << "\",\n";
    out << "\"title\":\"" << escapeJson(task.title) << "\",\n";
    out << "\"shortTitle\":\"" << escapeJson(task.shortTitle) << "\",\n";
    out << "\"problemKind\":\"" << escapeJson(task.problemKind) << "\",\n";
    out << "\"method\":\"" << escapeJson(task.method) << "\",\n";
    out << "\"ownerHint\":\"" << escapeJson(task.ownerHint) << "\",\n";
    out << "\"status\":\"" << escapeJson(task.status) << "\",\n";
    out << "\"note\":\"" << escapeJson(task.note) << "\",\n";
    out << "\"n\":" << task.n << ",\"m\":" << task.m << ",\"n2\":" << task.n2 << ",\"m2\":" << task.m2 << ",\n";
    out << "\"iterations\":" << task.iterations << ",\"iterations2\":" << task.iterations2 << ",\n";
    out << "\"methodError\":" << std::setprecision(16) << task.methodError << ",\"methodError2\":" << task.methodError2 << ",\n";
    out << "\"residual\":" << task.residual << ",\"residual2\":" << task.residual2 << ",\n";
    out << "\"accuracy\":" << task.accuracy << ",\"maxX\":" << task.maxX << ",\"maxY\":" << task.maxY << ",\n";
    out << "\"columns\":";
    writeColumnsJson(out, task.columns);
    out << ",\n\"rows\":";
    writeRowsJson(out, task.rows);
    out << "\n}";
}

std::string csvNameForTask(std::string id) {
    std::replace(id.begin(), id.end(), '-', '_');
    return id + ".csv";
}

double valueByColumnKey(const TableRow& row, const std::string& key) {
    if (key == "i") {
        return static_cast<double>(row.i);
    }
    if (key == "j") {
        return static_cast<double>(row.j);
    }
    if (key == "x") {
        return row.x;
    }
    if (key == "y") {
        return row.y;
    }
    if (key == "u") {
        return row.u;
    }
    if (key == "v") {
        return row.v;
    }
    if (key == "v2") {
        return row.v2;
    }
    if (key == "difference") {
        return row.difference;
    }
    return 0.0;
}

}  // namespace

InputData parseInputJson(const std::string& path) {
    const std::string text = readTextFile(path);

    InputData input;
    input.n = parseInt(text, "n", input.n);
    input.m = parseInt(text, "m", input.m);
    input.tolerance = parseNumber(text, "tolerance", input.tolerance);
    input.methodTolerance = parseNumber(text, "methodTolerance", input.methodTolerance);
    input.maxIterations = parseInt(text, "maxIterations", input.maxIterations);
    input.maxN = parseInt(text, "maxN", input.maxN);
    input.maxM = parseInt(text, "maxM", input.maxM);
    input.tableStrideX = parseInt(text, "tableStrideX", input.tableStrideX);
    input.tableStrideY = parseInt(text, "tableStrideY", input.tableStrideY);
    input.omega = parseNumber(text, "omega", input.omega);

    validateInput(input);
    return input;
}

ProjectResult runProjectAnalysis(const InputData& inputData) {
    InputData input = inputData;
    validateInput(input);

    ProjectResult result;
    result.input = input;
    result.variant = VariantData{};

    result.tasks.push_back(runTestSeidelTask(input, result.variant));
    result.tasks.push_back(runTestSorTask(input, result.variant));
    result.tasks.push_back(runMainSeidelTask(input, result.variant));
    result.tasks.push_back(runMainSorTask(input, result.variant));

    return result;
}

void writeResultJson(const std::string& outputPath, const ProjectResult& result) {
    std::ofstream out(outputPath);
    if (!out) {
        throw std::runtime_error("Cannot write output JSON: " + outputPath);
    }

    out << "{\n";
    out << "\"variant\":{"
        << "\"labNumber\":" << result.variant.labNumber << ","
        << "\"variantNumber\":" << result.variant.variantNumber << ","
        << "\"a\":" << result.variant.a << ","
        << "\"b\":" << result.variant.b << ","
        << "\"c\":" << result.variant.c << ","
        << "\"d\":" << result.variant.d << ","
        << "\"exact\":\"" << escapeJson(result.variant.exact) << "\","
        << "\"rhs\":\"" << escapeJson(result.variant.rhs) << "\","
        << "\"mu1\":\"" << escapeJson(result.variant.mu1) << "\","
        << "\"mu2\":\"" << escapeJson(result.variant.mu2) << "\","
        << "\"mu3\":\"" << escapeJson(result.variant.mu3) << "\","
        << "\"mu4\":\"" << escapeJson(result.variant.mu4) << "\""
        << "},\n";

    out << "\"input\":{"
        << "\"n\":" << result.input.n << ","
        << "\"m\":" << result.input.m << ","
        << "\"tolerance\":" << std::setprecision(16) << result.input.tolerance << ","
        << "\"methodTolerance\":" << result.input.methodTolerance << ","
        << "\"maxIterations\":" << result.input.maxIterations << ","
        << "\"maxN\":" << result.input.maxN << ","
        << "\"maxM\":" << result.input.maxM << ","
        << "\"tableStrideX\":" << result.input.tableStrideX << ","
        << "\"tableStrideY\":" << result.input.tableStrideY << ","
        << "\"omega\":" << result.input.omega
        << "},\n";

    out << "\"tasks\":[\n";
    for (size_t i = 0; i < result.tasks.size(); ++i) {
        writeTaskJson(out, result.tasks[i]);
        if (i + 1 < result.tasks.size()) {
            out << ",";
        }
        out << "\n";
    }
    out << "]\n";
    out << "}\n";
}

void writeCsvTables(const std::string& outDir, const ProjectResult& result) {
    const std::filesystem::path base(outDir);
    std::filesystem::create_directories(base);

    for (const TaskResult& task : result.tasks) {
        std::ofstream out(base / csvNameForTask(task.id));
        if (!out) {
            throw std::runtime_error("Cannot write task CSV");
        }

        for (size_t i = 0; i < task.columns.size(); ++i) {
            if (i > 0) {
                out << ",";
            }
            out << task.columns[i].title;
        }
        out << "\n";

        out << std::setprecision(12);
        for (const TableRow& row : task.rows) {
            for (size_t i = 0; i < task.columns.size(); ++i) {
                if (i > 0) {
                    out << ",";
                }
                out << valueByColumnKey(row, task.columns[i].key);
            }
            out << "\n";
        }

        if (task.rows.empty()) {
            out << "# C++ implementation placeholder for this participant.\n";
        }
    }
}
