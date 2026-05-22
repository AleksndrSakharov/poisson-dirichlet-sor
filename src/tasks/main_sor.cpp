#include "tasks/main_sor.hpp"

#include "task_utils.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace {

constexpr double pi = 3.141592653589793238462643383279502884;

struct GridSolution {
    int n = 0;
    int m = 0;
    double h = 0.0;
    double k = 0.0;
    int iterations = 0;
    double methodError = 0.0;
    double initialResidual = 0.0;
    double residual = 0.0;
    bool converged = false;
    std::vector<double> values;
};

int indexOf(int i, int j, int n) {
    return j * (n + 1) + i;
}

double rhs(double x, double y) {
    return std::abs(x - y);
}

double mu1(double y) {
    const double s = std::sin(pi * y);
    return s * s;
}

double mu2(double y) {
    return std::abs(std::exp(std::sin(pi * y)) - 1.0);
}

double mu3(double x) {
    return x * (1.0 - x);
}

double mu4(double x) {
    return x * (1.0 - x) * std::exp(x);
}

double boundaryCorner(double x, double y, const VariantData& variant) {
    if (std::abs(x - variant.a) < 1e-14) {
        return mu1(y);
    }
    if (std::abs(x - variant.b) < 1e-14) {
        return mu2(y);
    }
    if (std::abs(y - variant.c) < 1e-14) {
        return mu3(x);
    }
    return mu4(x);
}

double initialValue(double x, double y, const VariantData& variant) {
    const double sx = (x - variant.a) / (variant.b - variant.a);
    const double sy = (y - variant.c) / (variant.d - variant.c);

    const double leftRight = (1.0 - sx) * mu1(y) + sx * mu2(y);
    const double bottomTop = (1.0 - sy) * mu3(x) + sy * mu4(x);

    const double cornerBlend =
        (1.0 - sx) * (1.0 - sy) * boundaryCorner(variant.a, variant.c, variant) +
        sx * (1.0 - sy) * boundaryCorner(variant.b, variant.c, variant) +
        (1.0 - sx) * sy * boundaryCorner(variant.a, variant.d, variant) +
        sx * sy * boundaryCorner(variant.b, variant.d, variant);

    return leftRight + bottomTop - cornerBlend;
}

void applyBoundary(GridSolution& grid, const VariantData& variant) {
    for (int j = 0; j <= grid.m; ++j) {
        const double y = variant.c + j * grid.k;
        grid.values[indexOf(0, j, grid.n)] = mu1(y);
        grid.values[indexOf(grid.n, j, grid.n)] = mu2(y);
    }

    for (int i = 0; i <= grid.n; ++i) {
        const double x = variant.a + i * grid.h;
        grid.values[indexOf(i, 0, grid.n)] = mu3(x);
        grid.values[indexOf(i, grid.m, grid.n)] = mu4(x);
    }
}

double computeResidual(const GridSolution& grid, const VariantData& variant) {
    const double hx2 = grid.h * grid.h;
    const double ky2 = grid.k * grid.k;
    double maxResidual = 0.0;

    for (int j = 1; j < grid.m; ++j) {
        const double y = variant.c + j * grid.k;
        for (int i = 1; i < grid.n; ++i) {
            const double x = variant.a + i * grid.h;
            const double center = grid.values[indexOf(i, j, grid.n)];
            const double laplace =
                (grid.values[indexOf(i - 1, j, grid.n)] - 2.0 * center + grid.values[indexOf(i + 1, j, grid.n)]) / hx2 +
                (grid.values[indexOf(i, j - 1, grid.n)] - 2.0 * center + grid.values[indexOf(i, j + 1, grid.n)]) / ky2;
            maxResidual = std::max(maxResidual, std::abs(laplace + rhs(x, y)));
        }
    }

    return maxResidual;
}

GridSolution solvePoissonSor(
    int n,
    int m,
    const VariantData& variant,
    double omega,
    double methodTolerance,
    int maxIterations) {

    if (n < 2 || m < 2) {
        throw std::runtime_error("Grid must contain interior nodes");
    }

    GridSolution grid;
    grid.n = n;
    grid.m = m;
    grid.h = (variant.b - variant.a) / n;
    grid.k = (variant.d - variant.c) / m;
    grid.values.assign(static_cast<size_t>((n + 1) * (m + 1)), 0.0);

    for (int j = 0; j <= m; ++j) {
        const double y = variant.c + j * grid.k;
        for (int i = 0; i <= n; ++i) {
            const double x = variant.a + i * grid.h;
            grid.values[indexOf(i, j, n)] = initialValue(x, y, variant);
        }
    }
    applyBoundary(grid, variant);
    grid.initialResidual = computeResidual(grid, variant);

    const double ax = 1.0 / (grid.h * grid.h);
    const double ay = 1.0 / (grid.k * grid.k);
    const double denominator = 2.0 * (ax + ay);

    for (int iteration = 1; iteration <= maxIterations; ++iteration) {
        double maxChange = 0.0;

        for (int j = 1; j < m; ++j) {
            const double y = variant.c + j * grid.k;
            for (int i = 1; i < n; ++i) {
                const double x = variant.a + i * grid.h;
                const int id = indexOf(i, j, n);
                const double oldValue = grid.values[id];
                const double gsValue =
                    (ax * (grid.values[indexOf(i - 1, j, n)] + grid.values[indexOf(i + 1, j, n)]) +
                     ay * (grid.values[indexOf(i, j - 1, n)] + grid.values[indexOf(i, j + 1, n)]) +
                     rhs(x, y)) /
                    denominator;
                const double newValue = (1.0 - omega) * oldValue + omega * gsValue;
                grid.values[id] = newValue;
                maxChange = std::max(maxChange, std::abs(newValue - oldValue));
            }
        }

        grid.iterations = iteration;
        grid.methodError = maxChange;
        if (maxChange <= methodTolerance) {
            grid.converged = true;
            break;
        }
    }

    grid.residual = computeResidual(grid, variant);
    return grid;
}

std::vector<int> sampledIndices(int last, int stride) {
    std::vector<int> indices;
    for (int i = 0; i <= last; i += std::max(1, stride)) {
        indices.push_back(i);
    }
    if (indices.empty() || indices.back() != last) {
        indices.push_back(last);
    }
    return indices;
}

}  // namespace

TaskResult runMainSorTask(const InputData& input, const VariantData& variant) {
    TaskResult task;
    task.id = "main-sor";
    task.title = "Основная задача, метод верхней релаксации";
    task.shortTitle = "4. Основная, МВР";
    task.problemKind = "Основная задача Дирихле для уравнения Пуассона";
    task.method = "Метод верхней релаксации";
    task.ownerHint = "Курпяков Алексей";
    task.columns = makeMainTaskColumns();

    const double omega = input.omega;
    int n = std::max(2, input.n);
    int m = std::max(2, input.m);
    GridSolution coarse;
    GridSolution fine;
    double maxDiff = 0.0;
    int maxI = 0;
    int maxJ = 0;
    if (2 * n <= input.maxN && 2 * m <= input.maxM) {
        coarse = solvePoissonSor(n, m, variant, omega, input.methodTolerance, input.maxIterations);
        fine = solvePoissonSor(2 * n, 2 * m, variant, omega, input.methodTolerance, input.maxIterations);

        maxDiff = 0.0;
        maxI = 0;
        maxJ = 0;
        for (int j = 0; j <= m; ++j) {
            for (int i = 0; i <= n; ++i) {
                const double diff = std::abs(
                    coarse.values[indexOf(i, j, n)] -
                    fine.values[indexOf(2 * i, 2 * j, 2 * n)]);
                if (diff > maxDiff) {
                    maxDiff = diff;
                    maxI = i;
                    maxJ = j;
                }
            }
        }
    }

    if (coarse.values.empty() || fine.values.empty()) {
        task.status = "warning";
        task.note =
            "Не удалось построить контрольную сетку (2n,2m): увеличьте maxN/maxM или уменьшите начальные n,m.";
        return task;
    }

    task.n = coarse.n;
    task.m = coarse.m;
    task.n2 = fine.n;
    task.m2 = fine.m;
    task.iterations = coarse.iterations;
    task.iterations2 = fine.iterations;
    task.methodError = coarse.methodError;
    task.methodError2 = fine.methodError;
    task.residual = coarse.residual;
    task.residual2 = fine.residual;
    task.accuracy = maxDiff;
    task.maxX = variant.a + maxI * coarse.h;
    task.maxY = variant.c + maxJ * coarse.k;
    task.status = (coarse.converged && fine.converged) ? "done" : "warning";

    std::ostringstream note;
    note << "Для решения основной задачи использована сетка n = " << coarse.n
         << ", m = " << coarse.m << "; контроль точности выполнен на сетке 2n = "
         << fine.n << ", 2m = " << fine.m << ".\n";
    note << "Метод: МВР (omega = " << std::fixed << std::setprecision(3) << omega
         << "). Критерий остановки по итерациям epsilon_met = "
         << std::scientific << std::setprecision(3) << input.methodTolerance
         << ", Nmax = " << input.maxIterations << ".\n";
    note << "На основной сетке: N = " << coarse.iterations
         << ", достигнутая точность итерационного метода = " << coarse.methodError
         << ", ||R^(0)||_max = " << coarse.initialResidual
         << ", ||R||_max = " << coarse.residual << ".\n";
    note << "На контрольной сетке: N2 = " << fine.iterations
         << ", достигнутая точность итерационного метода = " << fine.methodError
         << ", ||R2^(0)||_max = " << fine.initialResidual
         << ", ||R2||_max = " << fine.residual << ".\n";
    note << "Заданная для контроля точность основной задачи epsilon = " << input.tolerance
         << "; на выбранной сетке получено epsilon_2 = " << maxDiff << ".\n";
    note << "Максимальное отклонение решений на общих узлах находится в узле i = "
         << maxI << ", j = " << maxJ << " (x = " << std::fixed << std::setprecision(6)
         << task.maxX << ", y = " << task.maxY << ").\n";
    note << "Начальное приближение построено трансфинитной линейной интерполяцией граничных условий.";
    if (!coarse.converged || !fine.converged) {
        note << "\nПредупреждение: итерационный метод не достиг epsilon_met до ограничения Nmax.";
    }
    task.note = note.str();

    const std::vector<int> xs = sampledIndices(coarse.n, input.tableStrideX);
    const std::vector<int> ys = sampledIndices(coarse.m, input.tableStrideY);
    for (int j : ys) {
        for (int i : xs) {
            TableRow row;
            row.i = i;
            row.j = j;
            row.x = variant.a + i * coarse.h;
            row.y = variant.c + j * coarse.k;
            row.v = coarse.values[indexOf(i, j, coarse.n)];
            row.v2 = fine.values[indexOf(2 * i, 2 * j, fine.n)];
            row.difference = row.v - row.v2;
            task.rows.push_back(row);
        }
    }

    return task;
}
