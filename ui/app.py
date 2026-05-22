from __future__ import annotations

import json
import os
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt

plt.rcParams["toolbar"] = "None"
plt.rcParams["font.family"] = "Segoe UI"


TASK_DEFINITIONS = [
    {
        "id": "test-seidel",
        "tab": "1. Тест, Зейдель",
        "title": "Тестовая задача, метод Зейделя",
        "subtitle": "Проверка по точному решению u*(x,y)=exp(sin^2(pi*x*y))",
        "owner": "Исполнитель 1",
        "expected": [
            "Реализовать тестовую задачу варианта 6.",
            "Вывести u*, v, u*-v и погрешность epsilon_1.",
            "Проверить порядок сходимости при сгущении сетки.",
        ],
    },
    {
        "id": "test-sor",
        "tab": "2. Тест, МВР",
        "title": "Тестовая задача, метод верхней релаксации",
        "subtitle": "Тестовая задача с подбором omega из интервала (0,2)",
        "owner": "Исполнитель 2",
        "expected": [
            "Реализовать МВР для тестовой задачи.",
            "Подобрать omega и вывести норму невязки.",
            "Показать графики точного, численного решения и ошибки.",
        ],
    },
    {
        "id": "main-seidel",
        "tab": "3. Основная, Зейдель",
        "title": "Основная задача, метод Зейделя",
        "subtitle": "Твоя часть: решение основной задачи на сетках (n,m) и (2n,2m)",
        "owner": "Исполнитель 3",
        "expected": [
            "Реализовано: f(x,y)=|x-y| и граничные условия варианта 6.",
            "Реализовано: метод Зейделя, контроль по ||v-v2||max.",
            "Выводятся справка, таблица, CSV и графики поверхностей.",
        ],
    },
    {
        "id": "main-sor",
        "tab": "4. Основная, МВР",
        "title": "Основная задача, метод верхней релаксации",
        "subtitle": "Основная задача с ускорением сходимости параметром omega",
        "owner": "Исполнитель 4",
        "expected": [
            "Реализовать основную задачу методом верхней релаксации.",
            "Подобрать omega, близкое к оптимальному.",
            "Вывести v, v2, v-v2 и достигнутую точность epsilon_2.",
        ],
    },
]


class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color="#ffffff", corner_radius=10, padding=12, autoresize=True, **kwargs):
        super().__init__(parent, highlightthickness=0, borderwidth=0, **kwargs)
        self.bg_color = bg_color
        self.corner_radius = corner_radius
        self.padding = padding
        self.autoresize = autoresize
        self.inner_frame = ttk.Frame(self, style="Card.TFrame")
        self.window_id = self.create_window(0, 0, window=self.inner_frame, anchor="nw")
        self.bind("<Configure>", self._on_resize)
        self.inner_frame.bind("<Configure>", self._on_inner_configure)

    def _on_inner_configure(self, event):
        if not self.autoresize:
            return
        target_height = self.inner_frame.winfo_reqheight() + 2 * self.padding
        if abs(self.winfo_height() - target_height) > 4:
            self.configure(height=target_height)

    def _on_resize(self, event):
        width, height = event.width, event.height
        self.delete("bg_rect")
        radius = min(self.corner_radius, width // 2, height // 2)
        self.create_rectangle(radius, 0, width - radius, height, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        self.create_rectangle(0, radius, width, height - radius, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        self.create_oval(0, 0, 2 * radius, 2 * radius, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        self.create_oval(width - 2 * radius, 0, width, 2 * radius, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        self.create_oval(0, height - 2 * radius, 2 * radius, height, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        self.create_oval(width - 2 * radius, height - 2 * radius, width, height, fill=self.bg_color, outline=self.bg_color, tags="bg_rect")
        inner_width = max(1, width - 2 * self.padding)
        if self.autoresize:
            self.itemconfigure(self.window_id, width=inner_width)
        else:
            self.itemconfigure(self.window_id, width=inner_width, height=max(1, height - 2 * self.padding))
        self.coords(self.window_id, self.padding, self.padding)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command=None,
        width=130,
        height=36,
        bg_color="#3b82f6",
        fg_color="#ffffff",
        hover_color="#2563eb",
        font=None,
    ):
        try:
            parent_bg = parent["background"]
        except tk.TclError:
            parent_bg = "#ffffff"
        super().__init__(parent, width=width, height=height, highlightthickness=0, borderwidth=0, bg=parent_bg)
        self.base_width = width
        self.base_height = height
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.font = font or ("Segoe UI", 9, "bold")
        self.color = bg_color
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda event: self._draw(event.width, event.height))
        self._draw(width, height)

    def _draw(self, width, height):
        self.delete("all")
        radius = min(10, width / 2, height / 2)
        points = [
            radius, 0, width - radius, 0, width, 0, width, radius, width, height - radius,
            width, height, width - radius, height, radius, height, 0, height, 0, height - radius,
            0, radius, 0, 0,
        ]
        self.create_polygon(points, smooth=True, fill=self.color, outline=self.color)
        self.create_text(width / 2, height / 2, text=self.text, fill=self.fg_color, font=self.font, width=max(30, width - 16))

    def _on_enter(self, _event):
        self.color = self.hover_color
        self.config(cursor="hand2")
        self._draw(self.winfo_width(), self.winfo_height())

    def _on_leave(self, _event):
        self.color = self.bg_color
        self.config(cursor="")
        self._draw(self.winfo_width(), self.winfo_height())

    def _on_click(self, _event):
        if self.command:
            self.command()


class SegmentedTaskButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=220, height=40, font=None):
        super().__init__(parent, width=width, height=height, highlightthickness=0, borderwidth=0, bg="#ffffff")
        self.base_width = width
        self.base_height = height
        self.text = text
        self.command = command
        self.font = font or ("Segoe UI", 9, "bold")
        self.active = False
        self.hover = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda event: self._redraw(event.width, event.height))
        self._redraw(width, height)

    def set_active(self, active: bool) -> None:
        self.active = active
        self._redraw(self.winfo_width() or 1, self.winfo_height() or 1)

    def _redraw(self, width, height):
        self.delete("all")
        if self.active:
            fill, outline, fg = "#3b82f6", "#3b82f6", "#ffffff"
        elif self.hover:
            fill, outline, fg = "#e5e7eb", "#d1d5db", "#111827"
        else:
            fill, outline, fg = "#f9fafb", "#d1d5db", "#374151"
        radius = min(10, width / 2, height / 2)
        pad = 2
        points = [
            pad + radius, pad, width - pad - radius, pad, width - pad, pad,
            width - pad, pad + radius, width - pad, height - pad - radius,
            width - pad, height - pad, width - pad - radius, height - pad,
            pad + radius, height - pad, pad, height - pad, pad,
            height - pad - radius, pad, pad + radius, pad, pad,
        ]
        self.create_polygon(points, smooth=True, fill=fill, outline=outline, width=1)
        self.create_text(width / 2, height / 2, text=self.text, fill=fg, font=self.font, width=max(40, width - 18))

    def _on_enter(self, _event):
        self.hover = True
        self.config(cursor="hand2")
        self._redraw(self.winfo_width(), self.winfo_height())

    def _on_leave(self, _event):
        self.hover = False
        self.config(cursor="")
        self._redraw(self.winfo_width(), self.winfo_height())

    def _on_click(self, _event):
        if self.command:
            self.command()


class CustomScrollbar(tk.Canvas):
    def __init__(
        self,
        parent,
        width=14,
        height=14,
        orient=tk.VERTICAL,
        bg_color="#ffffff",
        track_color="#eef2f7",
        thumb_color="#cbd5e1",
        thumb_hover_color="#94a3b8",
        **kwargs,
    ):
        canvas_size = {"width": width} if orient == tk.VERTICAL else {"height": height}
        super().__init__(parent, highlightthickness=0, borderwidth=0, bg=bg_color, **canvas_size, **kwargs)
        self.orient = orient
        self.command = None
        self.track_color = track_color
        self.thumb_color = thumb_color
        self.thumb_hover_color = thumb_hover_color
        self.top = 0.0
        self.bottom = 1.0
        self.dragging = False
        self.drag_start_pos = 0
        self.drag_start_top = 0.0
        self.thumb_id = None
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda _event: self._set_thumb(self.thumb_hover_color))
        self.bind("<Leave>", lambda _event: self._set_thumb(self.thumb_color) if not self.dragging else None)
        self.bind("<Configure>", lambda _event: self._redraw())

    def set(self, lo, hi):
        self.top = float(lo)
        self.bottom = float(hi)
        self._redraw()

    def _set_thumb(self, color):
        if self.thumb_id:
            self.itemconfig(self.thumb_id, fill=color)

    def _redraw(self):
        height = self.winfo_height()
        width = self.winfo_width()
        if height <= 0 or width <= 0:
            return
        self.delete("all")
        pad = 3
        radius = 5
        self._rounded_rect(pad, pad, width - pad, height - pad, radius, self.track_color, "")
        if self.orient == tk.VERTICAL:
            y1 = height * self.top
            y2 = max(y1 + 20, height * self.bottom)
            self.thumb_id = self._rounded_rect(pad, y1, width - pad, min(height - pad, y2), radius, self.thumb_color, "")
        else:
            x1 = width * self.top
            x2 = max(x1 + 20, width * self.bottom)
            self.thumb_id = self._rounded_rect(x1, pad, min(width - pad, x2), height - pad, radius, self.thumb_color, "")

    def _rounded_rect(self, x1, y1, x2, y2, radius, fill, outline):
        if x2 <= x1 or y2 <= y1:
            return None
        radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, fill=fill, outline=outline)

    def _on_press(self, event):
        if self.command is None:
            return
        length = max(1, self.winfo_height() if self.orient == tk.VERTICAL else self.winfo_width())
        pos = event.y if self.orient == tk.VERTICAL else event.x
        p1 = length * self.top
        p2 = length * self.bottom
        if p1 <= pos <= p2:
            self.dragging = True
            self.drag_start_pos = pos
            self.drag_start_top = self.top
            self._set_thumb(self.thumb_hover_color)
        else:
            self.command("moveto", pos / length)

    def _on_drag(self, event):
        if self.dragging and self.command:
            pos = event.y if self.orient == tk.VERTICAL else event.x
            length = max(1, self.winfo_height() if self.orient == tk.VERTICAL else self.winfo_width())
            self.command("moveto", self.drag_start_top + (pos - self.drag_start_pos) / length)

    def _on_release(self, _event):
        self.dragging = False
        self._set_thumb(self.thumb_color)


class CustomScale(tk.Canvas):
    def __init__(
        self,
        parent,
        from_=0.0,
        to=100.0,
        variable=None,
        command=None,
        length=170,
        height=28,
        bg_color="#f3f4f6",
        track_color="#e5e7eb",
        active_color="#3b82f6",
        thumb_color="#ffffff",
        thumb_outline="#2563eb",
        **kwargs,
    ):
        super().__init__(parent, width=length, height=height, highlightthickness=0, borderwidth=0, bg=bg_color, **kwargs)
        self.from_ = float(from_)
        self.to = float(to)
        self.variable = variable
        self.command = command
        self.length = length
        self.control_height = height
        self.track_color = track_color
        self.active_color = active_color
        self.thumb_color = thumb_color
        self.thumb_outline = thumb_outline
        self.dragging = False
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda event: self._draw(event.width, event.height))
        if self.variable is not None:
            self.variable.trace_add("write", lambda *_args: self._draw(self.winfo_width() or self.length, self.winfo_height() or self.control_height))
        self._draw(length, height)

    def _value(self):
        if self.variable is None:
            return self.from_
        return max(self.from_, min(self.to, float(self.variable.get())))

    def _fraction(self):
        if self.to == self.from_:
            return 0.0
        return (self._value() - self.from_) / (self.to - self.from_)

    def _draw(self, width, height):
        self.delete("all")
        pad_x = 10
        center_y = height / 2
        track_h = 8
        x1 = pad_x
        x2 = max(pad_x + 1, width - pad_x)
        radius = track_h / 2
        thumb_r = min(9, max(7, height / 3))
        fill_x = x1 + (x2 - x1) * self._fraction()
        self._rounded_rect(x1, center_y - track_h / 2, x2, center_y + track_h / 2, radius, self.track_color, "")
        self._rounded_rect(x1, center_y - track_h / 2, fill_x, center_y + track_h / 2, radius, self.active_color, "")
        self.create_oval(fill_x - thumb_r, center_y - thumb_r, fill_x + thumb_r, center_y + thumb_r, fill=self.thumb_color, outline=self.thumb_outline, width=2)

    def _rounded_rect(self, x1, y1, x2, y2, radius, fill, outline):
        if x2 <= x1:
            x2 = x1 + 1
        radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, fill=fill, outline=outline)

    def _set_from_x(self, x):
        width = max(1, self.winfo_width())
        pad_x = 10
        x1 = pad_x
        x2 = max(pad_x + 1, width - pad_x)
        fraction = max(0.0, min(1.0, (x - x1) / (x2 - x1)))
        value = self.from_ + fraction * (self.to - self.from_)
        if self.variable is not None:
            self.variable.set(value)
        if self.command:
            self.command(str(value))
        self._draw(width, self.winfo_height() or self.control_height)

    def _on_press(self, event):
        self.dragging = True
        self.config(cursor="hand2")
        self._set_from_x(event.x)

    def _on_drag(self, event):
        if self.dragging:
            self._set_from_x(event.x)

    def _on_release(self, _event):
        self.dragging = False
        self.config(cursor="")


class LabUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа №4: задача Дирихле для уравнения Пуассона")
        self.geometry("1500x900")
        self.minsize(1220, 760)

        self.project_root = Path(__file__).resolve().parent.parent
        self.default_input = self.project_root / "input_examples" / "default_input.json"
        self.default_output = self.project_root / "output"
        self.default_output.mkdir(exist_ok=True)

        self.input_path_var = tk.StringVar(value=str(self.default_input))
        self.output_dir_var = tk.StringVar(value=str(self.default_output))
        self.solver_path_var = tk.StringVar(value=str(self._default_solver_path()))
        self.n_var = tk.StringVar(value="20")
        self.m_var = tk.StringVar(value="40")
        self.tolerance_var = tk.StringVar(value="5e-7")
        self.method_tolerance_var = tk.StringVar(value="1e-8")
        self.max_iterations_var = tk.StringVar(value="100000")
        self.max_n_var = tk.StringVar(value="80")
        self.max_m_var = tk.StringVar(value="160")
        self.stride_x_var = tk.StringVar(value="2")
        self.stride_y_var = tk.StringVar(value="4")
        self.omega_var = tk.StringVar(value="1.7")
        self.text_scale_var = tk.DoubleVar(value=100.0)
        self.text_scale_label_var = tk.StringVar(value="100%")

        self.result_data: dict | None = None
        self.task_data_by_id: dict[str, dict] = {}
        self.task_switch_buttons: dict[str, SegmentedTaskButton] = {}
        self.current_task_id = TASK_DEFINITIONS[0]["id"]
        self._scale_after_id: str | None = None
        self.config_card: RoundedFrame | None = None
        self.viz_card: RoundedFrame | None = None
        self.variant_card: RoundedFrame | None = None
        self.task_card: RoundedFrame | None = None
        self.summary_card: RoundedFrame | None = None

        self.style = ttk.Style(self)
        self._init_fonts()
        self._configure_style()
        self._build_ui()
        self._load_input_file(self.default_input, show_message=False)
        self.load_result_from_output(show_error=False)

    def _init_fonts(self):
        self.font_specs = {
            "header": {"family": "Segoe UI", "size": 20, "weight": "bold"},
            "subheader": {"family": "Segoe UI", "size": 10},
            "label": {"family": "Segoe UI", "size": 9, "weight": "bold"},
            "section": {"family": "Segoe UI", "size": 11, "weight": "bold"},
            "body": {"family": "Segoe UI", "size": 10},
            "button": {"family": "Segoe UI", "size": 9, "weight": "bold"},
            "mono": {"family": "Consolas", "size": 10},
            "table": {"family": "Consolas", "size": 9},
            "table_heading": {"family": "Segoe UI", "size": 9, "weight": "bold"},
        }
        self.fonts = {name: tkfont.Font(root=self, **spec) for name, spec in self.font_specs.items()}

    def _scaled_size(self, base_size: int) -> int:
        return max(8, int(round(base_size * self.text_scale_var.get() / 100)))

    def _configure_style(self):
        self.configure(bg="#f3f4f6")
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self._apply_font_scale()

    def _apply_font_scale(self):
        for name, spec in self.font_specs.items():
            self.fonts[name].configure(size=self._scaled_size(spec["size"]))
        self.text_scale_label_var.set(f"{int(round(self.text_scale_var.get()))}%")
        plt.rcParams["font.size"] = self.fonts["body"].cget("size")
        self._refresh_styles()
        self._resize_scaled_controls()

    def _refresh_styles(self):
        self.style.configure("TFrame", background="#f3f4f6")
        self.style.configure("Card.TFrame", background="#ffffff")
        self.style.configure("TLabel", background="#f3f4f6", foreground="#111827", font=self.fonts["body"])
        self.style.configure("Header.TLabel", font=self.fonts["header"], background="#f3f4f6", foreground="#111827")
        self.style.configure("Subheader.TLabel", font=self.fonts["subheader"], background="#f3f4f6", foreground="#6b7280")
        self.style.configure("Card.TLabel", background="#ffffff", foreground="#111827", font=self.fonts["body"])
        self.style.configure("Field.TLabel", font=self.fonts["label"], background="#ffffff", foreground="#374151")
        self.style.configure("Section.TLabel", font=self.fonts["section"], background="#ffffff", foreground="#111827")
        self.style.configure("TButton", font=self.fonts["body"])
        self.style.configure("TEntry", font=self.fonts["body"], fieldbackground="#f9fafb", foreground="#1f2937", padding=(8, 7))
        self.style.configure(
            "Treeview",
            font=self.fonts["table"],
            rowheight=self.fonts["table"].metrics("linespace") + 12,
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1f2937",
            borderwidth=0,
        )
        self.style.configure(
            "Treeview.Heading",
            font=self.fonts["table_heading"],
            background="#f3f4f6",
            foreground="#6b7280",
            relief="flat",
            padding=(8, 8),
        )

    def _resize_scaled_controls(self):
        scale = self.text_scale_var.get() / 100.0
        if hasattr(self, "sidebar_frame"):
            self.sidebar_frame.configure(width=int(round(430 * min(scale, 1.35))))

        card_heights = [
            ("viz_card", 190, 1.70),
            ("variant_card", 185, 1.75),
            ("task_card", 78, 1.30),
            ("summary_card", 240, 1.35),
        ]
        for attr, base_height, cap in card_heights:
            card = getattr(self, attr, None)
            if card is not None:
                card.configure(height=int(round(base_height * min(scale, cap))))

        def visit(widget):
            for child in widget.winfo_children():
                if isinstance(child, RoundedButton):
                    height = int(round(child.base_height * min(scale, 1.65)))
                    child.configure(height=height)
                    child._draw(child.winfo_width() or child.base_width, height)
                elif isinstance(child, SegmentedTaskButton):
                    height = int(round(child.base_height * min(scale, 1.55)))
                    child.configure(height=height)
                    child._redraw(child.winfo_width() or child.base_width, height)
                visit(child)

        if hasattr(self, "sidebar_frame"):
            visit(self)

    def _on_text_scale_changed(self, value: str):
        scale = max(100.0, min(160.0, float(value)))
        self.text_scale_label_var.set(f"{int(round(scale))}%")
        if self._scale_after_id is not None:
            self.after_cancel(self._scale_after_id)
        self._scale_after_id = self.after(80, self._apply_font_scale)

    def _build_ui(self):
        root = ttk.Frame(self, padding=14)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root)
        header.pack(fill=tk.X, pady=(0, 12))
        title_block = ttk.Frame(header)
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_block, text="Решение задачи Дирихле для уравнения Пуассона", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_block,
            text="Лабораторная работа №4, вариант 6. Команда №6.",
            style="Subheader.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        scale_box = ttk.Frame(header)
        scale_box.pack(side=tk.RIGHT, anchor=tk.NE)
        ttk.Label(scale_box, text="Масштаб текста", style="Subheader.TLabel").pack(anchor=tk.E)
        self.text_scale_slider = CustomScale(
            scale_box,
            from_=100,
            to=160,
            variable=self.text_scale_var,
            command=self._on_text_scale_changed,
            length=170,
            height=28,
            bg_color="#f3f4f6",
        )
        self.text_scale_slider.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(scale_box, textvariable=self.text_scale_label_var, style="Subheader.TLabel", width=5).pack(side=tk.LEFT)

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True)

        self.sidebar_frame = ttk.Frame(body, width=430)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        self.sidebar_frame.pack_propagate(False)

        self.sidebar_canvas = tk.Canvas(self.sidebar_frame, highlightthickness=0, borderwidth=0, bg="#f3f4f6")
        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sidebar_scrollbar = CustomScrollbar(self.sidebar_frame, width=12, orient=tk.VERTICAL, bg_color="#f3f4f6")
        sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar_scrollbar.command = self.sidebar_canvas.yview
        self.sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

        sidebar_content = ttk.Frame(self.sidebar_canvas)
        sidebar_window = self.sidebar_canvas.create_window(0, 0, window=sidebar_content, anchor="nw")
        sidebar_content.bind("<Configure>", lambda _event: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all")))
        self.sidebar_canvas.bind("<Configure>", lambda event: self.sidebar_canvas.itemconfigure(sidebar_window, width=event.width))
        self._bind_mousewheel_scroll(self.sidebar_canvas, self.sidebar_canvas)
        self._bind_mousewheel_scroll(sidebar_content, self.sidebar_canvas)

        self._build_sidebar(sidebar_content)

        content = ttk.Frame(body)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_content(content)
        self._resize_scaled_controls()

    def _build_sidebar(self, parent):
        self.config_card = RoundedFrame(parent, bg_color="#ffffff", corner_radius=10, padding=14, autoresize=True, bg="#f3f4f6")
        self.config_card.pack(fill=tk.X, pady=(0, 12))
        inner = self.config_card.inner_frame
        ttk.Label(inner, text="Конфигурация и ввод", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))
        self._path_row(inner, "Solver", self.solver_path_var, self.pick_solver)
        self._path_row(inner, "Input JSON", self.input_path_var, self.pick_input)
        self._path_row(inner, "Output dir", self.output_dir_var, self.pick_output)
        ttk.Label(inner, text="Параметры расчета", style="Section.TLabel").pack(anchor=tk.W, pady=(14, 10))
        self._param_row(inner, "n", self.n_var, "m", self.m_var)
        self._param_row(inner, "epsilon", self.tolerance_var, "epsilon_met", self.method_tolerance_var)
        self._param_row(inner, "Nmax", self.max_iterations_var, "omega", self.omega_var)
        self._param_row(inner, "maxN", self.max_n_var, "maxM", self.max_m_var)
        self._param_row(inner, "stride x", self.stride_x_var, "stride y", self.stride_y_var)
        RoundedButton(inner, "Запустить расчет", command=self.run_solver, width=390, height=38, font=self.fonts["button"]).pack(fill=tk.X, pady=(12, 8))
        RoundedButton(
            inner,
            "Загрузить готовый результат",
            command=lambda: self.load_result_from_output(show_error=True),
            width=390,
            height=38,
            bg_color="#e5e7eb",
            fg_color="#111827",
            hover_color="#d1d5db",
            font=self.fonts["button"],
        ).pack(fill=tk.X)

        self.viz_card = RoundedFrame(parent, height=190, bg_color="#ffffff", corner_radius=10, padding=14, autoresize=False, bg="#f3f4f6")
        self.viz_card.pack(fill=tk.X, pady=(0, 12))
        inner = self.viz_card.inner_frame
        ttk.Label(inner, text="Визуализация", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))
        RoundedButton(
            inner,
            "График решения",
            command=lambda: self.plot_task(self.current_task_id, "solution"),
            width=390,
            height=40,
            bg_color="#e5e7eb",
            fg_color="#111827",
            hover_color="#d1d5db",
            font=self.fonts["button"],
        ).pack(fill=tk.X, pady=(0, 8))
        RoundedButton(
            inner,
            "График разности",
            command=lambda: self.plot_task(self.current_task_id, "difference"),
            width=390,
            height=40,
            bg_color="#e5e7eb",
            fg_color="#111827",
            hover_color="#d1d5db",
            font=self.fonts["button"],
        ).pack(fill=tk.X, pady=(0, 8))
        RoundedButton(
            inner,
            "Сохранить input",
            command=self.save_input_dialog,
            width=390,
            height=40,
            bg_color="#0f9f8f",
            fg_color="#ffffff",
            hover_color="#0d8a7e",
            font=self.fonts["button"],
        ).pack(fill=tk.X)

        self.variant_card = RoundedFrame(parent, height=185, bg_color="#ffffff", corner_radius=10, padding=14, autoresize=False, bg="#f3f4f6")
        self.variant_card.pack(fill=tk.X)
        inner = self.variant_card.inner_frame
        ttk.Label(inner, text="Вариант 6", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))
        text = (
            "a=0, b=1, c=0, d=2\n"
            "f(x,y)=|x-y|\n"
            "mu1(y)=sin^2(pi*y)\n"
            "mu2(y)=|exp(sin(pi*y))-1|\n"
            "mu3(x)=x(1-x),  mu4(x)=x(1-x)exp(x)"
        )
        ttk.Label(inner, text=text, style="Card.TLabel", justify=tk.LEFT).pack(anchor=tk.W)

    def _build_content(self, parent):
        self.task_card = RoundedFrame(parent, height=78, bg_color="#ffffff", corner_radius=10, padding=12, autoresize=False, bg="#f3f4f6")
        self.task_card.pack(fill=tk.X, pady=(0, 12))
        inner = self.task_card.inner_frame
        ttk.Label(inner, text="Задание", style="Section.TLabel", width=10).pack(side=tk.LEFT, padx=(0, 12))
        for task_def in TASK_DEFINITIONS:
            button = SegmentedTaskButton(
                inner,
                text=task_def["tab"],
                command=lambda task_id=task_def["id"]: self.select_task(task_id),
                height=40,
                font=self.fonts["button"],
            )
            button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            self.task_switch_buttons[task_def["id"]] = button

        self.summary_card = RoundedFrame(parent, height=240, bg_color="#ffffff", corner_radius=10, padding=14, autoresize=False, bg="#f3f4f6")
        self.summary_card.pack(fill=tk.X, pady=(0, 12))
        inner = self.summary_card.inner_frame
        ttk.Label(inner, text="Сводка результатов", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.summary_text = tk.Text(inner, height=9, wrap="word", font=self.fonts["mono"], relief="flat", bg="#ffffff", fg="#1f2937")
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.configure(state=tk.DISABLED)

        table_card = RoundedFrame(parent, bg_color="#ffffff", corner_radius=10, padding=14, autoresize=False, bg="#f3f4f6")
        table_card.pack(fill=tk.BOTH, expand=True)
        inner = table_card.inner_frame
        title_row = ttk.Frame(inner, style="Card.TFrame")
        title_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(title_row, text="Таблица результатов", style="Section.TLabel").pack(side=tk.LEFT)
        self.dataset_label_var = tk.StringVar(value="Набор данных:")
        ttk.Label(title_row, textvariable=self.dataset_label_var, style="Field.TLabel").pack(side=tk.RIGHT)
        table_container = ttk.Frame(inner, style="Card.TFrame")
        table_container.pack(fill=tk.BOTH, expand=True)
        yscroll = CustomScrollbar(table_container, width=12, orient=tk.VERTICAL, bg_color="#ffffff")
        xscroll = CustomScrollbar(table_container, height=12, orient=tk.HORIZONTAL, bg_color="#ffffff")
        self.table = ttk.Treeview(table_container, show="headings", yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.command = self.table.yview
        xscroll.command = self.table.xview
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.select_task(self.current_task_id)

    def _path_row(self, parent, label, variable, command):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row, text=label, style="Field.TLabel", width=10).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=variable).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        ttk.Button(row, text="...", width=3, command=command).pack(side=tk.RIGHT)

    def _param_row(self, parent, label1, var1, label2=None, var2=None):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row, text=label1, style="Field.TLabel", width=11).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var1, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 12))
        if label2 and var2:
            ttk.Label(row, text=label2, style="Field.TLabel", width=11).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var2, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    def _default_solver_path(self) -> Path:
        candidates = [
            self.project_root / "build_local" / "Release" / "poisson_solver.exe",
            self.project_root / "build_local" / "poisson_solver.exe",
            self.project_root / "build_local" / "poisson_solver",
            self.project_root / "build" / "Release" / "poisson_solver.exe",
            self.project_root / "build" / "poisson_solver.exe",
            self.project_root / "build" / "poisson_solver",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _default_summary(self, task_def: dict) -> str:
        return (
            "Статус: ожидается запуск backend.\n"
            f"Задача: {task_def['title']}.\n"
            "Формат результата уже ожидает result.json от poisson_solver.\n"
            "После запуска backend вернет строки таблицы, справку, epsilon_1/epsilon_2 и данные для графиков."
        )

    def _build_input_payload(self) -> dict:
        try:
            payload = {
                "n": int(self.n_var.get()),
                "m": int(self.m_var.get()),
                "tolerance": float(self.tolerance_var.get()),
                "methodTolerance": float(self.method_tolerance_var.get()),
                "maxIterations": int(self.max_iterations_var.get()),
                "maxN": int(self.max_n_var.get()),
                "maxM": int(self.max_m_var.get()),
                "tableStrideX": int(self.stride_x_var.get()),
                "tableStrideY": int(self.stride_y_var.get()),
                "omega": float(self.omega_var.get()),
            }
        except ValueError as ex:
            raise ValueError("Проверьте числовые параметры расчета.") from ex
        if payload["n"] < 2 or payload["m"] < 2:
            raise ValueError("n и m должны быть не меньше 2.")
        if payload["tolerance"] <= 0 or payload["methodTolerance"] <= 0:
            raise ValueError("epsilon и epsilon_met должны быть положительными.")
        return payload

    def _load_input_file(self, path: Path, show_message=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as ex:
            if show_message:
                messagebox.showerror("Ошибка", f"Не удалось открыть input JSON:\n{ex}")
            return
        self.input_path_var.set(str(path))
        self.n_var.set(str(data.get("n", self.n_var.get())))
        self.m_var.set(str(data.get("m", self.m_var.get())))
        self.tolerance_var.set(str(data.get("tolerance", self.tolerance_var.get())))
        self.method_tolerance_var.set(str(data.get("methodTolerance", self.method_tolerance_var.get())))
        self.max_iterations_var.set(str(data.get("maxIterations", self.max_iterations_var.get())))
        self.max_n_var.set(str(data.get("maxN", self.max_n_var.get())))
        self.max_m_var.set(str(data.get("maxM", self.max_m_var.get())))
        self.stride_x_var.set(str(data.get("tableStrideX", self.stride_x_var.get())))
        self.stride_y_var.set(str(data.get("tableStrideY", self.stride_y_var.get())))
        self.omega_var.set(str(data.get("omega", self.omega_var.get())))

    def pick_solver(self):
        path = filedialog.askopenfilename(filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")])
        if path:
            self.solver_path_var.set(path)

    def pick_input(self):
        path = filedialog.askopenfilename(filetypes=[("Файлы JSON", "*.json")])
        if path:
            self._load_input_file(Path(path))

    def pick_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir_var.set(path)

    def save_input_dialog(self):
        try:
            payload = self._build_input_payload()
        except Exception as ex:
            messagebox.showerror("Ошибка ввода", str(ex))
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Файлы JSON", "*.json")])
        if not path:
            return
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.input_path_var.set(path)

    def run_solver(self):
        solver = Path(self.solver_path_var.get())
        if not solver.exists():
            messagebox.showerror("Ошибка", "Не найден poisson_solver. Сначала соберите проект через .\\run.ps1 -Mode build")
            return
        try:
            payload = self._build_input_payload()
        except Exception as ex:
            messagebox.showerror("Ошибка ввода", str(ex))
            return

        output_dir = Path(self.output_dir_var.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        input_json = output_dir / "_ui_runtime_input.json"
        input_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            completed = subprocess.run(
                [str(solver), str(input_json), str(output_dir)],
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError as ex:
            messagebox.showerror("Ошибка запуска", ex.stderr or ex.stdout or str(ex))
            return
        self.load_result_from_output(show_error=True)
        messagebox.showinfo("Готово", completed.stdout.strip() or "Расчет завершен.")

    def load_result_from_output(self, show_error=True):
        result_path = Path(self.output_dir_var.get()) / "result.json"
        try:
            self.result_data = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception as ex:
            if show_error:
                messagebox.showerror("Ошибка", f"Не удалось открыть result.json:\n{ex}")
            return
        self.task_data_by_id = {task["id"]: task for task in self.result_data.get("tasks", [])}
        self.refresh_task(self.current_task_id)

    def select_task(self, task_id: str):
        self.current_task_id = task_id
        for current_id, button in self.task_switch_buttons.items():
            button.set_active(current_id == task_id)
        self.refresh_task(task_id)

    def refresh_task(self, task_id: str):
        task_def = next(item for item in TASK_DEFINITIONS if item["id"] == task_id)
        task = self.task_data_by_id.get(task_id)

        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        if task is None:
            self.summary_text.insert(tk.END, self._default_summary(task_def))
            self._fill_table_placeholder(task_id)
            self.dataset_label_var.set("Набор данных:")
        else:
            self.summary_text.insert(tk.END, self._format_task_summary(task, task_def))
            self._fill_task_table(task)
            self.dataset_label_var.set(f"Набор данных: {task.get('shortTitle', task_def['tab'])}")
        self.summary_text.configure(state=tk.DISABLED)

    def _format_task_summary(self, task: dict, task_def: dict) -> str:
        return (
            f"Статус: {task.get('status', 'unknown')}\n"
            f"Задача: {task.get('title', task_def['title'])}\n"
            f"Тип: {task.get('problemKind', '')}\n"
            f"Метод: {task.get('method', '')}\n"
            f"Исполнитель: {task.get('ownerHint', task_def['owner'])}\n"
            f"Сетка: n={task.get('n', 0)}, m={task.get('m', 0)}, 2n={task.get('n2', 0)}, 2m={task.get('m2', 0)}\n"
            f"Строк таблицы: {len(task.get('rows', []))}\n\n"
            f"{task.get('note', '')}"
        )

    def _fill_table_placeholder(self, task_id: str):
        if task_id.startswith("test"):
            columns = [("j", "j", 70), ("i", "i", 70), ("x", "x_i", 120), ("y", "y_j", 120), ("u", "u*(x_i,y_j)", 160), ("v", "v(x_i,y_j)", 160), ("difference", "u*-v", 160)]
        else:
            columns = [("j", "j", 70), ("i", "i", 70), ("x", "x_i", 120), ("y", "y_j", 120), ("v", "v(x_i,y_j)", 170), ("v2", "v2(x_2i,y_2j)", 180), ("difference", "v-v2", 160)]
        self._setup_columns(columns)
        self.table.delete(*self.table.get_children())

    def _fill_task_table(self, task: dict):
        columns = [(column["key"], column["title"], 150) for column in task.get("columns", [])]
        if not columns:
            self._fill_table_placeholder(task.get("id", ""))
            return
        self._setup_columns(columns)
        self.table.delete(*self.table.get_children())
        for row in task.get("rows", []):
            values = [self._format_cell(row.get(key)) for key, _title, _width in columns]
            self.table.insert("", tk.END, values=values)

    def _setup_columns(self, columns):
        self.table["columns"] = [key for key, _title, _width in columns]
        for key, title, width in columns:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, stretch=True, anchor=tk.CENTER)

    def _bind_mousewheel_scroll(self, widget, canvas):
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        widget.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        widget.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))

    def _enable_plot_zoom(self, fig, axes):
        axes_list = list(axes if isinstance(axes, (list, tuple)) else [axes])
        initial_limits = []
        initial_views = []
        for axis in axes_list:
            zlim = axis.get_zlim() if hasattr(axis, "get_zlim") else None
            initial_limits.append((axis.get_xlim(), axis.get_ylim(), zlim))
            if getattr(axis, "name", "") == "3d":
                initial_views.append((axis.elev, axis.azim, getattr(axis, "roll", 0)))
            else:
                initial_views.append(None)

        drag_state = {"axis": None, "x": 0.0, "y": 0.0, "xlim": None, "ylim": None}

        def centered_limits(limits, center, scale):
            left, right = limits
            if center is None:
                center = (left + right) / 2.0
            new_width = (right - left) * scale
            rel = (right - center) / (right - left) if right != left else 0.5
            return center - new_width * (1 - rel), center + new_width * rel

        def on_scroll(event):
            if event.inaxes not in axes_list:
                return
            axis = event.inaxes
            scale = 0.8 if event.button == "up" else 1.25
            is_3d = getattr(axis, "name", "") == "3d"
            axis.set_xlim(*centered_limits(axis.get_xlim(), None if is_3d else event.xdata, scale))
            axis.set_ylim(*centered_limits(axis.get_ylim(), None if is_3d else event.ydata, scale))
            if hasattr(axis, "get_zlim") and hasattr(axis, "set_zlim"):
                z_left, z_right = axis.get_zlim()
                z_center = (z_left + z_right) / 2.0
                z_width = (z_right - z_left) * scale
                axis.set_zlim(z_center - z_width / 2.0, z_center + z_width / 2.0)
            fig.canvas.draw_idle()

        def on_press(event):
            if event.inaxes not in axes_list:
                return
            is_3d = getattr(event.inaxes, "name", "") == "3d"
            pan_button = 2 if is_3d else 1
            if event.button != pan_button:
                return
            drag_state["axis"] = event.inaxes
            drag_state["x"] = event.x
            drag_state["y"] = event.y
            drag_state["xlim"] = event.inaxes.get_xlim()
            drag_state["ylim"] = event.inaxes.get_ylim()

        def on_motion(event):
            axis = drag_state["axis"]
            if axis is None:
                return
            x_left, x_right = drag_state["xlim"]
            y_bottom, y_top = drag_state["ylim"]
            bbox = axis.get_window_extent()
            if bbox.width <= 0 or bbox.height <= 0:
                return
            dx = (event.x - drag_state["x"]) / bbox.width * (x_right - x_left)
            dy = (event.y - drag_state["y"]) / bbox.height * (y_top - y_bottom)
            axis.set_xlim(x_left - dx, x_right - dx)
            axis.set_ylim(y_bottom - dy, y_top - dy)
            fig.canvas.draw_idle()

        def on_release(_event):
            drag_state["axis"] = None

        def on_key(event):
            if event.key not in {"r", "к"}:
                return
            for axis, (xlim, ylim, zlim), view in zip(axes_list, initial_limits, initial_views):
                axis.set_xlim(xlim)
                axis.set_ylim(ylim)
                if zlim is not None and hasattr(axis, "set_zlim"):
                    axis.set_zlim(zlim)
                if view is not None:
                    elev, azim, roll = view
                    try:
                        axis.view_init(elev=elev, azim=azim, roll=roll)
                    except TypeError:
                        axis.view_init(elev=elev, azim=azim)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("scroll_event", on_scroll)
        fig.canvas.mpl_connect("button_press_event", on_press)
        fig.canvas.mpl_connect("motion_notify_event", on_motion)
        fig.canvas.mpl_connect("button_release_event", on_release)
        fig.canvas.mpl_connect("key_press_event", on_key)

    def plot_task(self, task_id: str, mode: str):
        task = self.task_data_by_id.get(task_id)
        if not task or not task.get("rows"):
            messagebox.showinfo("График", "Данные для графика появятся после реализации и запуска C++ расчета.")
            return

        rows = task["rows"]
        xs = [row["x"] for row in rows]
        ys = [row["y"] for row in rows]
        if mode == "difference":
            zs = [row.get("difference", 0.0) for row in rows]
            title = "Разность решений"
            zlabel = "difference"
        else:
            zs = [row.get("v", 0.0) for row in rows]
            title = "Численное решение"
            zlabel = "v"

        fig = plt.figure(num=task.get("shortTitle", "График"), figsize=(10, 6), clear=True)
        ax = fig.add_subplot(111, projection="3d")
        if len(rows) >= 4:
            ax.plot_trisurf(xs, ys, zs, cmap="viridis", linewidth=0.2, antialiased=True, alpha=0.95)
        ax.scatter(xs, ys, zs, color="#1d4ed8", s=12)
        ax.set_title(f"{task.get('title', '')}: {title}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel(zlabel)
        if xs and ys and zs:
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            z_min, z_max = min(zs), max(zs)

            def padded_limits(low, high):
                span = high - low
                if abs(span) < 1e-12:
                    span = 1.0
                pad = span * 0.06
                return low - pad, high + pad, span + 2 * pad

            x_low, x_high, x_span = padded_limits(x_min, x_max)
            y_low, y_high, y_span = padded_limits(y_min, y_max)
            z_low, z_high, z_span = padded_limits(z_min, z_max)
            ax.set_xlim(x_low, x_high)
            ax.set_ylim(y_low, y_high)
            ax.set_zlim(z_low, z_high)
            try:
                ax.set_box_aspect((x_span, y_span, max(z_span, min(x_span, y_span) * 0.25)))
            except AttributeError:
                pass
        ax.view_init(elev=28, azim=-135)
        ax.set_anchor("C")
        fig.suptitle(
            "Колесо мыши: приблизить/отдалить, левая кнопка: вращать, средняя кнопка: переместить, R: сброс",
            fontsize=self.fonts["body"].cget("size"),
        )
        self._enable_plot_zoom(fig, ax)
        plt.tight_layout()
        plt.show()

    @staticmethod
    def _format_cell(value) -> str:
        if value is None:
            return ""
        if isinstance(value, float):
            if abs(value) < 1e-12:
                return "0"
            return f"{value:.10g}"
        return str(value)


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent.parent)
    app = LabUI()
    app.mainloop()
