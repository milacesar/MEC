import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Typical NZ Tier 2 values
tier2_defaults = {
    "Cattle": {
        "Mature dairy cow": {"BW":500,"GE":200,"Ym":6.5},
        "Heifer": {"BW":350,"GE":160,"Ym":6.5},
        "Mature bull": {"BW":700,"GE":250,"Ym":6.5},
        "Steer": {"BW":400,"GE":170,"Ym":6.5},
        "Calf": {"BW":100,"GE":50,"Ym":6.5}
    },
    "Sheep": {
        "Mature ewes": {"BW":70,"GE":12,"Ym":6.5},
        "Ram": {"BW":90,"GE":15,"Ym":6.5},
        "Lamb": {"BW":25,"GE":6,"Ym":6.5}
    }
}

# Help text
help_text = """Tier 2 Variables:
- BW (kg): Average body weight of the animal.
- GE (MJ/day): Daily gross energy intake of the animal.
- Ym (%): Methane conversion factor, % of gross energy converted to CH4.
- N: Number of animals in this category.
- Manure management: Optional additional CH4 emissions from manure storage and handling."""

class Tier2App:
    def __init__(self, root):
        self.root = root
        self.root.title("Tier 2 Multi-Category Methane Calculator")
        self.root.geometry("1100x600")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.herd_list = []

        main_frame = ttk.Frame(root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Input Frame
        input_frame = ttk.LabelFrame(main_frame, text="Add Animal Category", padding=10)
        input_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=5)
        input_frame.columnconfigure(1, weight=1)

        # Species Combobox
        ttk.Label(input_frame, text="Species:").grid(row=0, column=0, sticky="w")
        self.species_cb = ttk.Combobox(input_frame, values=list(tier2_defaults.keys()), state="readonly")
        self.species_cb.grid(row=0, column=1, sticky="ew")
        self.species_cb.set("Cattle")
        self.species_cb.bind("<<ComboboxSelected>>", self.update_category_cb)

        # Category Combobox
        ttk.Label(input_frame, text="Category:").grid(row=1, column=0, sticky="w")
        self.category_cb = ttk.Combobox(input_frame, values=[], state="readonly")
        self.category_cb.grid(row=1, column=1, sticky="ew")
        self.update_category_cb()  # initialize categories

        # Number of animals
        ttk.Label(input_frame, text="Number of animals:").grid(row=2, column=0, sticky="w")
        self.n_entry = ttk.Entry(input_frame)
        self.n_entry.grid(row=2, column=1, sticky="ew")
        self.n_entry.insert(0,"0")

        # Advanced inputs
        self.adv_var = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Enable advanced inputs", variable=self.adv_var, command=self.toggle_advanced).grid(row=3, column=0, columnspan=2, sticky="w")
        self.adv_frame = ttk.Frame(input_frame)
        self.adv_entries = {}
        adv_labels = ["BW (kg)", "GE (MJ/day)", "Ym (%)"]
        for i, label in enumerate(adv_labels):
            ttk.Label(self.adv_frame, text=label).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(self.adv_frame)
            entry.grid(row=i, column=1, sticky="ew")
            self.adv_entries[label] = entry
        self.adv_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.toggle_advanced()  # start hidden

        # Manure management
        self.manure_var = tk.BooleanVar()
        self.manure_check = ttk.Checkbutton(input_frame, text="Include manure management CH4", variable=self.manure_var)
        self.manure_check.grid(row=5, column=0, columnspan=2, sticky="w")

        # Buttons frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        ttk.Button(button_frame, text="Calculate", command=self.calculate_results).grid(row=0, column=0, sticky="ew")
        ttk.Button(button_frame, text="Save", command=self.save_results).grid(row=0, column=1, sticky="ew", padx=20)
        ttk.Button(button_frame, text="Reset", command=self.reset_app).grid(row=0, column=2, sticky="ew")

        # Results frame
        result_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        result_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.results_text = tk.Text(result_frame, wrap="word")
        self.results_text.grid(row=0, column=0, sticky="nsew")

        # Help button
        ttk.Button(input_frame, text="Help", command=self.show_help).grid(row=7, column=0, columnspan=2, pady=5)

    def update_category_cb(self, event=None):
        species = self.species_cb.get()
        categories = list(tier2_defaults[species].keys())
        self.category_cb['values'] = categories
        self.category_cb.set(categories[0])

    def toggle_advanced(self):
        if self.adv_var.get():
            self.adv_frame.grid()
        else:
            self.adv_frame.grid_remove()

    def add_category_to_list(self):
        species = self.species_cb.get()
        category = self.category_cb.get()
        try:
            N = float(self.n_entry.get())
        except ValueError:
            messagebox.showerror("Error","Enter valid number of animals.")
            return None

        if self.adv_var.get():
            try:
                BW = float(self.adv_entries["BW (kg)"].get())
                GE = float(self.adv_entries["GE (MJ/day)"].get())
                Ym = float(self.adv_entries["Ym (%)"].get())
            except ValueError:
                messagebox.showerror("Error","Enter valid advanced values.")
                return None
        else:
            defaults = tier2_defaults[species][category]
            BW = defaults["BW"]
            GE = defaults["GE"]
            Ym = defaults["Ym"]

        return {"species":species,"category":category,"N":N,"BW":BW,"GE":GE,"Ym":Ym}

    def calculate_results(self):
        entry = self.add_category_to_list()
        if entry:
            self.herd_list.append(entry)

        self.results_text.delete(1.0, tk.END)
        total_CH4 = 0
        for item in self.herd_list:
            EF = (item["GE"] * (item["Ym"]/100) * 365)/55.65
            enteric = EF * item["N"]
            manure = 0
            if self.manure_var.get():
                manure = 0.1 * enteric
            total = enteric + manure
            total_CH4 += total
            self.results_text.insert(tk.END,f"{item['species']} - {item['category']} ({item['N']} animals): {total:.2f} kg CH4/year (enteric {enteric:.2f} + manure {manure:.2f})\n")
        self.results_text.insert(tk.END, f"\nTotal CH4 emissions: {total_CH4:.2f} kg/year\n")

    def save_results(self):
        file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt"),("All files","*.*")])
        if file:
            with open(file, "w") as f:
                f.write(self.results_text.get(1.0, tk.END))
            messagebox.showinfo("Saved","Results saved successfully.")

    def reset_app(self):
        self.herd_list.clear()
        self.results_text.delete(1.0, tk.END)
        self.n_entry.delete(0, tk.END)
        self.n_entry.insert(0,"0")
        self.adv_var.set(False)
        self.toggle_advanced()
        self.manure_var.set(False)

    def show_help(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("Help - Tier 2 Variables")
        tk.Label(help_win, text=help_text, justify="left", wraplength=400, padx=10, pady=10).pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = Tier2App(root)
    root.mainloop()
