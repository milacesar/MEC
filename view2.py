# view.py
import tkinter as tk
from tkinter import ttk, messagebox

SPECIES_OPTIONS = ["Cattle", "Sheep"]
CATEGORY_OPTIONS = {
    "Cattle": ["Mature dairy", "Mature beef", "Heifer", "Steer", "Calf"],
    "Sheep": ["Ewe", "Mature sheep", "Lamb"]
}
STAGE_OPTIONS = {
    "Cattle": ["lactating", "dry", "maintenance", "growing", "beef"],
    "Sheep": ["lactating", "dry", "maintenance", "growing"]
}

class MethaneGUI:
    def __init__(self, root, controller):
        self.controller = controller
        self.root = root
        root.title("Methane Emissions Estimator")
        self.columns = ["Species","Category","Stage","N","BW","Milk","Tier1 CH4","Tier2 Simplified CH4","Tier2 Advanced CH4"]
        self.tree = ttk.Treeview(root, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Add Row", command=self.add_row_popup).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Calculate", command=self.calculate_all).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Exit", command=root.quit).pack(side="right", padx=5)

    def add_row_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add Animal Category")
        entries = {}

        # Species dropdown
        tk.Label(popup,text="Species").grid(row=0,column=0)
        species_cb = ttk.Combobox(popup, values=SPECIES_OPTIONS, state="readonly")
        species_cb.grid(row=0,column=1)
        entries["Species"] = species_cb

        # Category dropdown (will update when species changes)
        tk.Label(popup,text="Category").grid(row=1,column=0)
        category_cb = ttk.Combobox(popup, values=[], state="readonly")
        category_cb.grid(row=1,column=1)
        entries["Category"] = category_cb

        # Stage dropdown (will update when category changes)
        tk.Label(popup,text="Stage").grid(row=2,column=0)
        stage_cb = ttk.Combobox(popup, values=[], state="readonly")
        stage_cb.grid(row=2,column=1)
        entries["Stage"] = stage_cb

        # Other inputs
        for i, field in enumerate(["N","BW","Milk"], start=3):
            tk.Label(popup,text=field).grid(row=i,column=0)
            var = tk.StringVar()
            tk.Entry(popup,textvariable=var).grid(row=i,column=1)
            entries[field] = var

        # Update Category options based on Species
        def update_category(event):
            species = species_cb.get()
            category_cb["values"] = CATEGORY_OPTIONS.get(species, [])
            category_cb.set("")
            stage_cb.set("")
        species_cb.bind("<<ComboboxSelected>>", update_category)

        # Update Stage options based on Species
        def update_stage(event):
            species = species_cb.get()
            stage_cb["values"] = STAGE_OPTIONS.get(species, [])
            stage_cb.set("")
        category_cb.bind("<<ComboboxSelected>>", update_stage)

        def add_to_table():
            vals = []
            for col in ["Species","Category","Stage","N","BW","Milk"]:
                val = entries[col].get()
                if val == "":
                    val = None
                vals.append(val)
            self.tree.insert("", "end", values=vals + ["","",""])
            popup.destroy()

        tk.Button(popup,text="Add", command=add_to_table).grid(row=6,column=0,columnspan=2)

    def calculate_all(self):
        for iid in self.tree.get_children():
            vals = self.tree.item(iid)["values"]
            # Call controller to compute CH4
            results = self.controller.compute_ch4(vals)
            self.tree.item(iid, values=vals[:6] + results)
