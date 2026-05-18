#pragma once

#include <string>
#include <vector>

struct InputData {
    int n = 20;
    int m = 40;
    double tolerance = 0.5e-6;
    double methodTolerance = 1.0e-8;
    int maxIterations = 100000;
    int maxN = 160;
    int maxM = 320;
    int tableStrideX = 2;
    int tableStrideY = 4;
    double omega = 1.7;
};

struct VariantData {
    int labNumber = 4;
    int variantNumber = 6;
    double a = 0.0;
    double b = 1.0;
    double c = 0.0;
    double d = 2.0;
    std::string exact = "exp(sin^2(pi*x*y))";
    std::string rhs = "|x-y|";
    std::string mu1 = "sin^2(pi*y)";
    std::string mu2 = "|exp(sin(pi*y))-1|";
    std::string mu3 = "x(1-x)";
    std::string mu4 = "x(1-x)exp(x)";
};

struct TableColumn {
    std::string key;
    std::string title;
};

struct TableRow {
    int i = 0;
    int j = 0;
    double x = 0.0;
    double y = 0.0;
    double u = 0.0;
    double v = 0.0;
    double v2 = 0.0;
    double difference = 0.0;
};

struct TaskResult {
    std::string id;
    std::string title;
    std::string shortTitle;
    std::string problemKind;
    std::string method;
    std::string ownerHint;
    std::string status;
    std::string note;
    int n = 0;
    int m = 0;
    int n2 = 0;
    int m2 = 0;
    int iterations = 0;
    int iterations2 = 0;
    double methodError = 0.0;
    double methodError2 = 0.0;
    double residual = 0.0;
    double residual2 = 0.0;
    double accuracy = 0.0;
    double maxX = 0.0;
    double maxY = 0.0;
    std::vector<TableColumn> columns;
    std::vector<TableRow> rows;
};

struct ProjectResult {
    InputData input;
    VariantData variant;
    std::vector<TaskResult> tasks;
};
