from io import BytesIO

from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image
from PIL import Image, ImageDraw, ImageFont


OUTPUT = "program_data_table.png"
FONT = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

rows = [
    ("a, b", r"$a,\ b$", "Границы области по x: a = 0, b = 1"),
    ("c, d", r"$c,\ d$", "Границы области по y: c = 0, d = 2"),
    ("n", r"$n$", "Число разбиений сетки по x"),
    ("m", r"$m$", "Число разбиений сетки по y"),
    ("h, hx", r"$h_x=\frac{b-a}{n}$", "Шаг сетки по x"),
    ("k, hy", r"$h_y=\frac{d-c}{m}$", "Шаг сетки по y"),
    ("i, j", r"$i,\ j$", "Индексы узла сетки"),
    ("x, y", r"$x_i,\ y_j$", "Координаты узла: x_i = a + ih_x, y_j = c + jh_y"),
    ("rhs(x, y)", r"$f(x,y)$", "Правая часть f(x, y) = |x − y|"),
    ("mu1(y)", r"$\mu_1(y)$", "Граничное условие u(0, y) = sin²(πy)"),
    ("mu2(y)", r"$\mu_2(y)$", "Граничное условие u(1, y) = |exp(sin(πy)) − 1|"),
    ("mu3(x)", r"$\mu_3(x)$", "Граничное условие u(x, 0) = x(1 − x)"),
    ("mu4(x)", r"$\mu_4(x)$", "Граничное условие u(x, 2) = x(1 − x)exp(x)"),
    ("values", r"$v_{ij}$", "Массив приближённого решения"),
    ("initialValue", r"$v_{ij}^{(0)}$", "Начальное приближение, построенное по граничным условиям"),
    ("ax", r"$\frac{1}{h_x^2}$", "Коэффициент разностной схемы по x"),
    ("ay", r"$\frac{1}{h_y^2}$", "Коэффициент разностной схемы по y"),
    ("denominator", r"$2\left(\frac{1}{h_x^2}+\frac{1}{h_y^2}\right)$", "Знаменатель итерационной формулы"),
    ("oldValue", r"$v_{ij}^{(s)}$", "Значение до текущего обновления"),
    ("newValue", r"$v_{ij}^{(s+1)}$", "Новое значение метода Зейделя"),
    ("maxChange", r"$\varepsilon^{(s)}$", "Максимальное изменение решения за итерацию"),
    ("methodTolerance", r"$\varepsilon_{\mathrm{мет}}$", "Допуск остановки итерационного метода"),
    ("maxIterations", r"$N_{\max}$", "Максимальное число итераций"),
    ("iterations", r"$N$", "Фактически выполненное число итераций"),
    ("laplace", r"$\Delta_h v_{ij}$", "Разностный оператор Лапласа"),
    ("residual", r"$|R|_{\infty}$", "Максимальная (чебышёвская) норма невязки на основной сетке"),
    ("initialResidual", r"$|R^{(0)}|_{\infty}$", "Норма невязки начального приближения"),
    ("residual2", r"$|R_2|_{\infty}$", "Норма невязки на контрольной сетке (2n, 2m)"),
    ("v2", r"$v_{2i,2j}^{(2)}$", "Решение на контрольной сетке"),
    ("maxDiff, accuracy", r"$\varepsilon_2$", "Максимальная разность решений на основной и контрольной сетках"),
    ("tolerance", r"$\varepsilon$", "Требуемая точность основной задачи"),
]

headers = ("Обозначение в программе", "Математический символ", "Описание")
widths = (620, 600, 1380)
padding_x = 22
padding_y = 14
header_font = ImageFont.truetype(FONT_BOLD, 31)
body_font = ImageFont.truetype(FONT, 29)
title_font = ImageFont.truetype(FONT_BOLD, 38)
math_font = FontProperties(size=13)
math_cache = {}


def render_math(text):
    if text in math_cache:
        return math_cache[text]
    buffer = BytesIO()
    math_to_image(text, buffer, prop=math_font, dpi=160, format="png", color="black")
    buffer.seek(0)
    formula = Image.open(buffer).convert("RGBA")
    luminance = formula.convert("L")
    alpha = luminance.point(lambda value: 255 - value)
    bbox = alpha.getbbox()
    if bbox:
        formula = formula.crop(bbox)
        alpha = alpha.crop(bbox)
    formula.putalpha(alpha)
    math_cache[text] = formula
    return formula


def wrapped_lines(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


probe = Image.new("RGB", (sum(widths), 100), "white")
probe_draw = ImageDraw.Draw(probe)
line_height = 36
header_height = 78
title_height = 96
row_layout = []
for row in rows:
    cells = [
        [row[i]] if i == 1 else wrapped_lines(probe_draw, row[i], body_font, widths[i] - 2 * padding_x)
        for i in range(3)
    ]
    formula_height = render_math(row[1]).height + 2 * padding_y
    text_height = max(len(cells[0]), len(cells[2])) * line_height + 2 * padding_y
    height = max(64, formula_height, text_height)
    row_layout.append((cells, height))

image = Image.new(
    "RGB",
    (sum(widths) + 2, title_height + header_height + sum(h for _, h in row_layout) + 2),
    "white",
)
draw = ImageDraw.Draw(image)
draw.text((image.width // 2, 24), "Данные, используемые программой", font=title_font, fill="black", anchor="ma")

y = title_height
x = 0
for i, header in enumerate(headers):
    draw.rectangle((x, y, x + widths[i], y + header_height), fill="white", outline="black", width=2)
    draw.multiline_text(
        (x + widths[i] / 2, y + header_height / 2),
        header,
        font=header_font,
        fill="black",
        anchor="mm",
        align="center",
    )
    x += widths[i]

y += header_height
for row_number, (cells, height) in enumerate(row_layout):
    x = 0
    fill = "white"
    for i, lines in enumerate(cells):
        draw.rectangle((x, y, x + widths[i], y + height), fill=fill, outline="black", width=2)
        if i == 1:
            formula = render_math(lines[0])
            formula_x = int(x + padding_x)
            formula_y = int(y + (height - formula.height) / 2)
            image.paste(formula, (formula_x, formula_y), formula)
        else:
            text_y = y + (height - len(lines) * line_height) / 2
            for line in lines:
                draw.text((x + padding_x, text_y), line, font=body_font, fill="black")
                text_y += line_height
        x += widths[i]
    y += height

image.save(OUTPUT, dpi=(200, 200))
print(OUTPUT)
