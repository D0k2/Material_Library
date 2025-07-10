Отлично, я
помогу
вам
с
этим.Для
добавления
графиков, которые
обновляются
в
реальном
времени, нам
нужно
будет
внести
изменения
в
нескольких
местах:

1. ** `create_editable_treeview` **: Добавим
в
эту
функцию
`callback`(обратный
вызов), который
будет
срабатывать
каждый
раз, когда
значение
в
ячейке
изменяется.
2. ** `PropertyEditorTab` ** (для Физических свойств): Мы
изменим
компоновку
этой
вкладки, разделив
её
на
две
части: слева — поля
для
ввода, справа — график.Затем
добавим
логику
для
отрисовки
и
обновления
этого
графика.
3. ** `MechanicalPropertiesTab` ** (для Механических свойств): Применим
точно
такой
же
подход, как
и
для
физических
свойств.

Ниже
приведены
только
те
части
кода, которые
требуют
изменений
или
добавления.Просто
замените
существующие
классы
и
функции
в
вашем
файле
на
эти
обновленные
версии.

### 1. Вспомогательная функция `create_editable_treeview`

Добавим
параметр
`on_update_callback`, который
будет
вызываться
после
изменения
данных.

```python


# --- Вспомогательная функция для редактирования ячеек Treeview ---
def create_editable_treeview(parent_frame, on_update_callback=None):
    """Создает Treeview и добавляет к нему логику редактирования ячеек."""
    tree = ttk.Treeview(parent_frame)

    def on_tree_double_click(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item_id = tree.focus()
        column = tree.identify_column(event.x)

        # Получаем геометрию ячейки
        x, y, width, height = tree.bbox(item_id, column)

        # Создаем временное поле для ввода
        entry_var = tk.StringVar()
        entry = ttk.Entry(tree, textvariable=entry_var)

        # Получаем текущее значение и устанавливаем его в поле
        current_value = tree.set(item_id, column)
        entry_var.set(current_value)

        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.selection_range(0, tk.END)

        def on_focus_out(event):
            tree.set(item_id, column, entry_var.get())
            entry.destroy()
            # Вызываем callback, если он был передан
            if on_update_callback:
                on_update_callback()

        def on_enter_press(event):
            on_focus_out(event)

        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", on_enter_press)

    tree.bind("<Double-1>", on_tree_double_click)
    return tree


```

### 2. Класс `PropertyEditorTab` (Вкладка "Физические свойства")

Этот
класс
будет
значительно
переработан, чтобы
включить
в
себя
графики.

```python


class PropertyEditorTab(ttk.Frame):
    """Универсальная вкладка для редактирования набора свойств с графиком в реальном времени."""

    def __init__(self, parent, prop_group_key, prop_map):
        super().__init__(parent)
        self.prop_group_key = prop_group_key
        self.prop_map = prop_map
        self.prop_widgets = {}
        self._setup_widgets()

    def _on_mousewheel(self, event, widget):
        if event.num == 4 or event.delta > 0:
            widget.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            widget.yview_scroll(1, "units")

    def _setup_widgets(self):
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        on_scroll = lambda e: self._on_mousewheel(e, canvas)
        canvas.bind("<MouseWheel>", on_scroll)
        scrollable_frame.bind("<MouseWheel>", on_scroll)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for prop_key, prop_info in self.prop_map.items():
            frame = ttk.LabelFrame(scrollable_frame, text=f"{prop_info['name']} ({prop_info['symbol']})", padding=10)
            frame.pack(fill="x", expand=True, padx=10, pady=5)
            frame.bind("<MouseWheel>", on_scroll)

            # --- Разделение на левую (данные) и правую (график) панели ---
            content_frame = ttk.Frame(frame)
            content_frame.pack(fill="both", expand=True)

            left_panel = ttk.Frame(content_frame)
            left_panel.pack(side="left", fill="y", padx=(0, 10))

            right_panel = ttk.Frame(content_frame)
            right_panel.pack(side="right", fill="both", expand=True)

            # Создаем коллбэк-функцию с замыканием на prop_key
            update_callback = lambda p_key=prop_key: self.update_graph(p_key)

            widgets = self._create_prop_fields(left_panel, update_callback)

            # --- Настройка графика ---
            fig = Figure(figsize=(4, 3), dpi=90)
            ax = fig.add_subplot(111)
            graph_canvas = FigureCanvasTkAgg(fig, master=right_panel)
            graph_canvas.get_tk_widget().pack(fill="both", expand=True)
            widgets.update({'fig': fig, 'ax': ax, 'canvas': graph_canvas})

            self.prop_widgets[prop_key] = widgets

    def _create_prop_fields(self, parent_frame, on_update_callback):
        parent_frame.columnconfigure(1, weight=1)
        widgets = {}
        # ... (поля source, subsource, comment без изменений)
        ttk.Label(parent_frame, text="Источник:").grid(row=0, column=0, sticky="w", pady=2)
        widgets["source"] = ttk.Entry(parent_frame)
        widgets["source"].grid(row=0, column=1, columnspan=2, sticky="we")

        ttk.Label(parent_frame, text="Под-источник:").grid(row=1, column=0, sticky="w", pady=2)
        widgets["subsource"] = ttk.Entry(parent_frame)
        widgets["subsource"].grid(row=1, column=1, columnspan=2, sticky="we")

        ttk.Label(parent_frame, text="Комментарий:").grid(row=2, column=0, sticky="w", pady=2)
        widgets["comment"] = ttk.Entry(parent_frame)
        widgets["comment"].grid(row=2, column=1, columnspan=2, sticky="we")

        table_frame = ttk.Frame(parent_frame)
        table_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=5)
        table_frame.columnconfigure(0, weight=1)

        # Передаем callback в create_editable_treeview
        tree = create_editable_treeview(table_frame, on_update_callback=on_update_callback)
        tree["columns"] = ("temp", "value")
        tree.heading("temp", text="Температура, °C");
        tree.column("temp", width=100)
        tree.heading("value", text="Значение");
        tree.column("value", width=100)
        tree.grid(row=0, column=0, sticky="nsew")
        widgets["tree"] = tree

        btn_frame = ttk.Frame(table_frame)
        btn_frame.grid(row=0, column=1, sticky="ns", padx=5)

        # Обновляем команды кнопок, чтобы они тоже вызывали callback
        add_cmd = lambda t=tree, cb=on_update_callback: (t.insert("", "end", values=["0", "0"]), cb() if cb else None)
        del_cmd = lambda t=tree, cb=on_update_callback: (t.delete(t.selection()), cb() if cb else None)

        ttk.Button(btn_frame, text="+", width=2, command=add_cmd).pack(pady=2)
        ttk.Button(btn_frame, text="-", width=2, command=del_cmd).pack(pady=2)

        return widgets

    def update_graph(self, prop_key):
        """Обновляет график для конкретного свойства."""
        widgets = self.prop_widgets.get(prop_key)
        if not widgets: return

        tree = widgets['tree']
        ax = widgets['ax']
        canvas = widgets['canvas']

        points = []
        for item_id in tree.get_children():
            values = tree.set(item_id)
            try:
                temp = float(values["temp"])
                val = float(values["value"])
                points.append((temp, val))
            except (ValueError, KeyError):
                continue

        # Сортируем точки по температуре для корректного отображения линии
        points.sort(key=lambda p: p[0])
        temps = [p[0] for p in points]
        values = [p[1] for p in points]

        ax.clear()
        if temps and values:
            ax.plot(temps, values, marker='o', linestyle='-', markersize=4)

        prop_info = self.prop_map[prop_key]
        ax.set_title(f"{prop_info['name']}", fontsize=9)
        ax.set_xlabel("t, °C", fontsize=8)
        ax.set_ylabel(f"{prop_info['unit']}", fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', which='major', labelsize=8)
        widgets['fig'].tight_layout(pad=0.5)

        canvas.draw()

    def populate_form(self, material):
        prop_group = material.data.get(self.prop_group_key, {})
        for prop_key, widgets in self.prop_widgets.items():
            prop_data = prop_group.get(prop_key, {})
            widgets["source"].delete(0, tk.END)
            widgets["source"].insert(0, prop_data.get("property_source", ""))
            widgets["subsource"].delete(0, tk.END)
            widgets["subsource"].insert(0, prop_data.get("property_subsource", ""))
            widgets["comment"].delete(0, tk.END)
            widgets["comment"].insert(0, prop_data.get("comment", ""))

            tree = widgets["tree"]
            for i in tree.get_children(): tree.delete(i)
            for temp, val in prop_data.get("temperature_value_pairs", []):
                tree.insert("", "end", values=[temp, val])

            # Обновляем график после заполнения таблицы
            self.update_graph(prop_key)

    def collect_data(self, material):
        if self.prop_group_key not in material.data:
            material.data[self.prop_group_key] = {}
        prop_group = material.data[self.prop_group_key]

        for prop_key, widgets in self.prop_widgets.items():
            pairs = []
            for item_id in widgets["tree"].get_children():
                values = widgets["tree"].set(item_id)
                try:
                    pairs.append([float(values["temp"]), float(values["value"])])
                except (ValueError, KeyError):
                    continue

            source = widgets["source"].get()
            subsource = widgets["subsource"].get()
            comment = widgets["comment"].get()

            if pairs or source or subsource or comment:
                prop_data = prop_group.setdefault(prop_key, {})
                prop_data["property_source"] = source
                prop_data["property_subsource"] = subsource
                prop_data["comment"] = comment
                prop_data["temperature_value_pairs"] = pairs
                if "property_name" not in prop_data:
                    prop_info = self.prop_map[prop_key]
                    prop_data["property_name"] = prop_info["name"]
                    prop_data["property_unit"] = prop_info["unit"]
            elif prop_key in prop_group:
                del prop_group[prop_key]


```

### 3. Класс `MechanicalPropertiesTab` (Вкладка "Механические свойства")

Здесь
мы
применим
ту
же
логику, что
и
в
предыдущем
классе.

```python


class MechanicalPropertiesTab(ttk.Frame):
    """Вкладка для редактирования механических свойств по категориям прочности с графиками."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.material = None
        self.current_category_idx = -1
        self.prop_widgets = {}
        self._setup_widgets()

    def _on_mousewheel(self, event, widget):
        if event.num == 4 or event.delta > 0:
            widget.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            widget.yview_scroll(1, "units")

    def _setup_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))
        # ... (код для top_frame без изменений)
        ttk.Label(top_frame, text="Категория прочности:").pack(side="left", padx=(0, 5))
        self.category_combo = ttk.Combobox(top_frame, state="readonly", width=40)
        self.category_combo.pack(side="left", fill="x", expand=True)
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_select)
        ttk.Button(top_frame, text="+", width=3, command=self._add_category).pack(side="left", padx=5)
        ttk.Button(top_frame, text="-", width=3, command=self._delete_category).pack(side="left")

        self.editor_content_frame = ttk.Frame(self)
        self.editor_content_frame.pack(fill="both", expand=True)
        self.editor_content_frame.pack_forget()

        name_frame = ttk.Frame(self.editor_content_frame)
        name_frame.pack(fill="x", pady=5)
        ttk.Label(name_frame, text="Название категории:").pack(side="left")
        self.category_name_entry = ttk.Entry(name_frame)
        self.category_name_entry.pack(side="left", fill="x", expand=True, padx=5)

        prop_canvas = tk.Canvas(self.editor_content_frame)
        scrollbar = ttk.Scrollbar(self.editor_content_frame, orient="vertical", command=prop_canvas.yview)
        scrollable_frame = ttk.Frame(prop_canvas)

        scrollable_frame.bind("<Configure>", lambda e: prop_canvas.configure(scrollregion=prop_canvas.bbox("all")))
        prop_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        prop_canvas.configure(yscrollcommand=scrollbar.set)

        on_scroll = lambda e: self._on_mousewheel(e, prop_canvas)
        prop_canvas.bind("<MouseWheel>", on_scroll)
        scrollable_frame.bind("<MouseWheel>", on_scroll)

        prop_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for prop_key, prop_info in MECHANICAL_PROPERTIES_MAP.items():
            frame = ttk.LabelFrame(scrollable_frame, text=f"{prop_info['name']} ({prop_info['symbol']})", padding=10)
            frame.pack(fill="x", expand=True, padx=10, pady=5)
            frame.bind("<MouseWheel>", on_scroll)

            content_frame = ttk.Frame(frame)
            content_frame.pack(fill="both", expand=True)
            left_panel = ttk.Frame(content_frame);
            left_panel.pack(side="left", fill="y", padx=(0, 10))
            right_panel = ttk.Frame(content_frame);
            right_panel.pack(side="right", fill="both", expand=True)

            update_callback = lambda p_key=prop_key: self.update_mech_graph(p_key)
            widgets = self._create_prop_fields_for_editor(left_panel, update_callback)

            fig = Figure(figsize=(4, 3), dpi=90)
            ax = fig.add_subplot(111)
            graph_canvas = FigureCanvasTkAgg(fig, master=right_panel)
            graph_canvas.get_tk_widget().pack(fill="both", expand=True)
            widgets.update({'fig': fig, 'ax': ax, 'canvas': graph_canvas})

            self.prop_widgets[prop_key] = widgets

        hardness_frame = ttk.LabelFrame(scrollable_frame, text="Твердость (Hardness)", padding=10)
        hardness_frame.pack(fill="x", expand=True, padx=10, pady=5)
        hardness_frame.bind("<MouseWheel>", on_scroll)
        self.hardness_tree = self._create_hardness_table(hardness_frame)

    def _create_prop_fields_for_editor(self, parent_frame, on_update_callback):
        parent_frame.columnconfigure(1, weight=1)
        widgets = {}
        # ... (поля source, subsource, comment без изменений) ...
        ttk.Label(parent_frame, text="Источник:").grid(row=0, column=0, sticky="w", pady=2)
        widgets["source"] = ttk.Entry(parent_frame);
        widgets["source"].grid(row=0, column=1, columnspan=2, sticky="we")
        ttk.Label(parent_frame, text="Под-источник:").grid(row=1, column=0, sticky="w", pady=2)
        widgets["subsource"] = ttk.Entry(parent_frame);
        widgets["subsource"].grid(row=1, column=1, columnspan=2, sticky="we")
        ttk.Label(parent_frame, text="Комментарий:").grid(row=2, column=0, sticky="w", pady=2)
        widgets["comment"] = ttk.Entry(parent_frame);
        widgets["comment"].grid(row=2, column=1, columnspan=2, sticky="we")

        table_frame = ttk.Frame(parent_frame)
        table_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=5)
        table_frame.columnconfigure(0, weight=1)

        tree = create_editable_treeview(table_frame, on_update_callback=on_update_callback)
        tree["columns"] = ("temp", "value")
        tree.heading("temp", text="Температура, °C");
        tree.column("temp", width=100)
        tree.heading("value", text="Значение");
        tree.column("value", width=100)
        tree.grid(row=0, column=0, sticky="nsew")
        widgets["tree"] = tree

        btn_frame = ttk.Frame(table_frame)
        btn_frame.grid(row=0, column=1, sticky="ns", padx=5)

        add_cmd = lambda t=tree, cb=on_update_callback: (t.insert("", "end", values=["0", "0"]), cb() if cb else None)
        del_cmd = lambda t=tree, cb=on_update_callback: (t.delete(t.selection()), cb() if cb else None)

        ttk.Button(btn_frame, text="+", width=2, command=add_cmd).pack(pady=2)
        ttk.Button(btn_frame, text="-", width=2, command=del_cmd).pack(pady=2)
        return widgets

    def _create_hardness_table(self, parent_frame):
        # Эта функция остается без изменений
        parent_frame.columnconfigure(0, weight=1)
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill="both", expand=True)
        table_frame.columnconfigure(0, weight=1)
        tree = create_editable_treeview(table_frame)
        tree["columns"] = ("source", "subsource", "min", "max", "unit")
        tree.heading("source", text="Источник");
        tree.column("source", width=150)
        tree.heading("subsource", text="Под-источник");
        tree.column("subsource", width=100)
        tree.heading("min", text="Min");
        tree.column("min", width=60)
        tree.heading("max", text="Max");
        tree.column("max", width=60)
        tree.heading("unit", text="Ед. изм.");
        tree.column("unit", width=60)
        tree.pack(side="left", fill="both", expand=True)
        btn_frame = ttk.Frame(table_frame);
        btn_frame.pack(side="left", fill="y", padx=5)
        ttk.Button(btn_frame, text="+", width=2,
                   command=lambda: tree.insert("", "end", values=["", "", "", "", ""])).pack(pady=2)
        ttk.Button(btn_frame, text="-", width=2, command=lambda: tree.delete(tree.selection())).pack(pady=2)
        return tree

    def update_mech_graph(self, prop_key):
        """Обновляет график для конкретного механического свойства."""
        widgets = self.prop_widgets.get(prop_key)
        if not widgets: return

        tree = widgets['tree']
        ax = widgets['ax']
        canvas = widgets['canvas']

        points = []
        for item_id in tree.get_children():
            values = tree.set(item_id)
            try:
                points.append((float(values["temp"]), float(values["value"])))
            except (ValueError, KeyError):
                continue

        points.sort(key=lambda p: p[0])
        temps = [p[0] for p in points]
        values = [p[1] for p in points]

        ax.clear()
        if temps and values:
            ax.plot(temps, values, marker='o', linestyle='-', markersize=4)

        prop_info = MECHANICAL_PROPERTIES_MAP[prop_key]
        ax.set_title(f"{prop_info['name']}", fontsize=9, wrap=True)
        ax.set_xlabel("t, °C", fontsize=8)
        ax.set_ylabel(f"{prop_info['unit']}", fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', which='major', labelsize=8)
        widgets['fig'].tight_layout(pad=0.5)

        canvas.draw()

    def _populate_category_fields(self, category_data):
        self.category_name_entry.delete(0, tk.END)
        self.category_name_entry.insert(0, category_data.get("value_strength_category", ""))

        for prop_key, widgets in self.prop_widgets.items():
            prop_data = category_data.get(prop_key, {})
            widgets["source"].delete(0, tk.END);
            widgets["source"].insert(0, prop_data.get("property_source", ""))
            widgets["subsource"].delete(0, tk.END);
            widgets["subsource"].insert(0, prop_data.get("property_subsource", ""))
            widgets["comment"].delete(0, tk.END);
            widgets["comment"].insert(0, prop_data.get("comment", ""))

            tree = widgets["tree"]
            for i in tree.get_children(): tree.delete(i)
            for temp, val in prop_data.get("temperature_value_pairs", []):
                tree.insert("", "end", values=[temp, val])
            # Обновляем график для этого свойства
            self.update_mech_graph(prop_key)

        for i in self.hardness_tree.get_children(): self.hardness_tree.delete(i)
        for h_data in category_data.get("hardness", []):
            self.hardness_tree.insert("", "end", values=[
                h_data.get("property_source", ""), h_data.get("property_subsource", ""),
                h_data.get("min_value", ""), h_data.get("max_value", ""), h_data.get("unit_value", "")
            ])

    # Методы populate_form, _on_category_select, _add_category, _delete_category,
    # _save_current_category, collect_data остаются без изменений в своей логике,
    # так как они вызывают _populate_category_fields, который теперь сам обновляет графики.
    # Поэтому их код можно не менять.
    # Оставим только populate_form для ясности

    def populate_form(self, material):
        if self.material and self.material != material:
            self._save_current_category()

        self.material = material
        self.current_category_idx = -1

        categories = material.data.get("mechanical_properties", {}).get("strength_category", [])
        category_names = [cat.get("value_strength_category", f"Категория {i + 1}") for i, cat in enumerate(categories)]
        self.category_combo["values"] = category_names

        if categories:
            self.current_category_idx = 0
            self.category_combo.current(0)
            self._populate_category_fields(categories[0])
            self.editor_content_frame.pack(fill="both", expand=True)
        else:
            self.category_combo.set("")
            # Очищаем все поля и графики, если категорий нет
            self._populate_category_fields({})
            self.editor_content_frame.pack_forget()


```