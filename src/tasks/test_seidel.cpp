#include "tasks/test_seidel.hpp"
#include "task_utils.hpp"

#include <cmath>
#include <vector>
#include <algorithm>
#include <sstream>
#include <iomanip>

namespace {
    const double PI = std::acos(-1.0);

    double u_exact(double x, double y) {
        double P = PI * x * y;
        double sinP = std::sin(P);
        return std::exp(sinP * sinP);
    }

    double f_test(double x, double y) {
        double P = PI * x * y;
        double sinP = std::sin(P);
        double cosP = std::cos(P);
        
        double sin2P = std::sin(2.0 * P);
        double cos2P = std::cos(2.0 * P);

        double u = u_exact(x, y);

        double term2 = (sin2P * sin2P) + (2.0 * cos2P);
        double delta_u = u * PI * PI * (x * x + y * y) * term2;

        return -delta_u;
    }
}

TaskResult runTestSeidelTask(const InputData& input, const VariantData& variant) {
    double a = 0.0;
    double b = 1.0;
    double c = 0.0;
    double d = 2.0;

    int n = input.n;
    int m = input.m;

    double hx = (b - a) / n;
    double hy = (d - c) / m;
    double hx2 = hx * hx;
    double hy2 = hy * hy;
    
    double C = 2.0 / hx2 + 2.0 / hy2;

    std::vector<std::vector<double>> v(n + 1, std::vector<double>(m + 1, 0.0));

    for (int i = 0; i <= n; ++i) {
        double x = a + i * hx;
        v[i][0] = u_exact(x, c);
        v[i][m] = u_exact(x, d);
    }
    for (int j = 0; j <= m; ++j) {
        double y = c + j * hy;
        v[0][j] = u_exact(a, y);
        v[n][j] = u_exact(b, y);
    }

    for (int i = 1; i < n; ++i) {
        for (int j = 1; j < m; ++j) {
            double v_x = v[0][j] + (double)i / n * (v[n][j] - v[0][j]);
            double v_y = v[i][0] + (double)j / m * (v[i][m] - v[i][0]);
            v[i][j] = (v_x + v_y) / 2.0;
        }
    }

    int iterations = 0;
    double max_diff = 0.0;

    do {
        max_diff = 0.0;
        for (int i = 1; i < n; ++i) {
            for (int j = 1; j < m; ++j) {
                double x = a + i * hx;
                double y = c + j * hy;

                double v_new = ((v[i - 1][j] + v[i + 1][j]) / hx2 +
                                (v[i][j - 1] + v[i][j + 1]) / hy2 +
                                f_test(x, y)) / C;

                double diff = std::abs(v_new - v[i][j]);
                if (diff > max_diff) {
                    max_diff = diff;
                }
                v[i][j] = v_new; 
            }
        }
        iterations++;
    } while (max_diff >= input.methodTolerance && iterations < input.maxIterations);

    double max_residual = 0.0;
    for (int i = 1; i < n; ++i) {
        for (int j = 1; j < m; ++j) {
            double x = a + i * hx;
            double y = c + j * hy;
            double laplacian = (v[i - 1][j] - 2.0 * v[i][j] + v[i + 1][j]) / hx2 +
                               (v[i][j - 1] - 2.0 * v[i][j] + v[i][j + 1]) / hy2;
            double r = std::abs(laplacian + f_test(x, y));
            if (r > max_residual) max_residual = r;
        }
    }

    double max_accuracy_error = 0.0;
    double err_x = 0.0;
    double err_y = 0.0;
    for (int i = 0; i <= n; ++i) {
        for (int j = 0; j <= m; ++j) {
            double x = a + i * hx;
            double y = c + j * hy;
            double exact = u_exact(x, y);
            double diff = std::abs(v[i][j] - exact);
            if (diff > max_accuracy_error) {
                max_accuracy_error = diff;
                err_x = x;
                err_y = y;
            }
        }
    }

    double max_truncation_error = 0.0;
    for (int i = 1; i < n; ++i) {
        for (int j = 1; j < m; ++j) {
            double x = a + i * hx;
            double y = c + j * hy;
            double lap_u = (u_exact(x - hx, y) - 2.0 * u_exact(x, y) + u_exact(x + hx, y)) / hx2 +
                           (u_exact(x, y - hy) - 2.0 * u_exact(x, y) + u_exact(x, y + hy)) / hy2;
            double psi = std::abs(lap_u + f_test(x, y));
            if (psi > max_truncation_error) max_truncation_error = psi;
        }
    }

    double Lx = b - a;
    double Ly = d - c;
    double lambda_min = (4.0 / hx2) * std::pow(std::sin(PI * hx / (2.0 * Lx)), 2) + 
                        (4.0 / hy2) * std::pow(std::sin(PI * hy / (2.0 * Ly)), 2);

    double Z_bound = max_residual / lambda_min;
    double z_scheme_bound = max_truncation_error / lambda_min;
    double total_error_bound = Z_bound + z_scheme_bound;

    std::ostringstream report;
    report << std::scientific << std::setprecision(3);
    report << "Для решения тестовой задачи использованы сетка с числом разбиений по x n = " << n 
           << " и числом разбиений по y m = " << m << ",\n"
           << "метод Зейделя (МВР с параметром ω = 1.0), применены критерии остановки по точности "
           << "ε_мет = " << input.methodTolerance << " и по числу итераций N_max = " << input.maxIterations << "\n\n"
           << "На решение схемы (СЛАУ) затрачено итераций N = " << iterations 
           << " и достигнута точность итерационного метода ε^(N) = " << max_diff << "\n\n"
           << "Схема (СЛАУ) решена с невязкой ||R^(N)|| = " << max_residual << "\n"
           << "для невязки СЛАУ использована норма «максимальная (чебышёвская)»;\n\n"
           << "Тестовая задача должна быть решена с погрешностью не более ε = " << input.tolerance 
           << "; задача решена с погрешностью ε_1 = " << max_accuracy_error << "\n\n"
           << "Максимальное отклонение точного и численного решений наблюдается в узле "
           << "x = " << std::fixed << std::setprecision(4) << err_x << "; y = " << err_y << "\n\n"
           << "В качестве начального приближения использовано:\n"
           << "«Среднее (полусумма линейных интерполяций вдоль x и y)»\n\n"
           << "================ РАСЧЕТЫ ДЛЯ ОТЧЕТА ================\n"
           << std::scientific << std::setprecision(3)
           << "Схема (СЛАУ) решена с погрешностью ||Z^(N)|| <= " << Z_bound << "\n"
           << "Погрешность схемы оценивается как ||z||_inf <= " << z_scheme_bound << "\n"
           << "использована норма ||z||_inf = «максимальная (чебышёвская)»\n"
           << "Общая погрешность решения тестовой задачи оценивается как ||z_общ||_inf <= " << total_error_bound << "\n"
           << "использована норма ||z_общ||_inf = «максимальная (чебышёвская)»";

    std::vector<TableRow> rows;
    for (int i = 0; i <= n; i += input.tableStrideX) {
        for (int j = 0; j <= m; j += input.tableStrideY) {
            double x = a + i * hx;
            double y = c + j * hy;
            double exact = u_exact(x, y);
            double approx = v[i][j];

            TableRow row;
            row.i = i;
            row.j = j;
            row.x = x;
            row.y = y;
            row.u = exact;
            row.v = approx;
            row.difference = exact - approx;
            row.v2 = 0;
            rows.push_back(row);
        }
    }

    TaskResult task;
    task.id = "test-seidel";
    task.title = "Тестовая задача, метод Зейделя";
    task.shortTitle = "1. Тест, Зейдель";
    task.problemKind = "Тестовая задача Дирихле для уравнения Пуассона";
    task.method = "Метод Зейделя";
    task.ownerHint = "Папулина Юлия";
    task.status = max_diff < input.methodTolerance ? "success" : "warning"; 
    
    task.note = report.str();

    task.n = n;
    task.m = m;
    task.iterations = iterations;
    task.methodError = max_diff;
    task.residual = max_residual;
    task.accuracy = max_accuracy_error;
    task.maxX = err_x;
    task.maxY = err_y;

    task.columns = makeTestTaskColumns();
    task.rows = std::move(rows);

    return task;
}