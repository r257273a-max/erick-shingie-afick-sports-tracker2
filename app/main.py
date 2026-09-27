import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from models import Player
import storage
from metrics import efficiency, performance_summary

APP_NAME = "ERICK SHINGIE AFICK SPORTS TRACKER"
POSITIONS = ["Goalkeeper", "Defender", "Midfielder", "Forward", "Other"]
MEDICAL = ["Fit", "Under Observation", "Injured", "Recovering"]
CONTRACTS = ["Active", "Expired", "Pending", "Released"]

def clean_float(value, field):
    try:
        n = float(value)
        if not 0 <= n <= 100:
            raise ValueError
        return n
    except ValueError:
        raise ValueError(f"{field} must be a number between 0 and 100.")

def clean_int(value, field, minimum=0):
    try:
        n = int(value)
        if n < minimum:
            raise ValueError
        return n
    except ValueError:
        raise ValueError(f"{field} must be a whole number >= {minimum}.")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1250x760")
        self.minsize(1050, 680)
        self.players = storage.load_players()
        self.filtered = list(self.players)
        self.selected_id = None
        self.configure(bg="#eef2f7")
        self._build_style()
        self._build_ui()
        self.refresh()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="white")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TButton", padding=(10, 7))
        style.configure("Danger.TButton", padding=(10, 7))
        style.configure("Metric.TLabel", font=("Segoe UI", 17, "bold"))

    def _build_ui(self):
        header = ttk.Frame(self, padding=18)
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Offline player administration • file-based storage • performance analytics",
            style="Sub.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        metrics = ttk.Frame(self, padding=(18, 0, 18, 12))
        metrics.pack(fill="x")
        self.card_vars = [tk.StringVar(value="0") for _ in range(4)]
        labels = ["Players", "Fit", "Injured", "Avg. Efficiency"]
        for i, label in enumerate(labels):
            card = ttk.Frame(metrics, style="Card.TFrame", padding=12)
            card.grid(row=0, column=i, sticky="ew", padx=5)
            metrics.columnconfigure(i, weight=1)
            ttk.Label(card, text=label).pack(anchor="w")
            ttk.Label(card, textvariable=self.card_vars[i], style="Metric.TLabel").pack(anchor="w")

        controls = ttk.Frame(self, padding=(18, 0, 18, 10))
        controls.pack(fill="x")
        ttk.Label(controls, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(controls, textvariable=self.search_var, width=30).pack(side="left", padx=6)

        ttk.Label(controls, text="Position:").pack(side="left", padx=(12, 3))
        self.position_filter = ttk.Combobox(controls, values=["All"] + POSITIONS, state="readonly", width=14)
        self.position_filter.set("All")
        self.position_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.position_filter.pack(side="left")

        ttk.Label(controls, text="Min Fitness:").pack(side="left", padx=(12, 3))
        self.fitness_filter = ttk.Combobox(controls, values=["All", "50", "60", "70", "80", "90"], state="readonly", width=8)
        self.fitness_filter.set("All")
        self.fitness_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.fitness_filter.pack(side="left")

        ttk.Button(controls, text="Add Player", command=self.add_player).pack(side="right", padx=3)
        ttk.Button(controls, text="Export CSV", command=self.export_csv).pack(side="right", padx=3)
        ttk.Button(controls, text="Export JSON", command=self.export_json).pack(side="right", padx=3)

        table_frame = ttk.Frame(self, padding=(18, 0, 18, 10))
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "name", "age", "position", "team", "fitness", "matches", "goals", "assists", "medical", "eff")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "id":"ID", "name":"Player Name", "age":"Age", "position":"Position",
            "team":"Team", "fitness":"Fitness", "matches":"Matches",
            "goals":"Goals", "assists":"Assists", "medical":"Medical", "eff":"Efficiency"
        }
        widths = {"id":95, "name":180, "age":55, "position":100, "team":110, "fitness":75,
                  "matches":70, "goals":60, "assists":65, "medical":115, "eff":80}
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="center")
        self.tree.column("name", anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        bottom = ttk.Frame(self, padding=(18, 0, 18, 18))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Edit Selected", command=self.edit_selected).pack(side="left", padx=3)
        ttk.Button(bottom, text="Performance Summary", command=self.show_summary).pack(side="left", padx=3)
        ttk.Button(bottom, text="Injury History", command=self.show_injuries).pack(side="left", padx=3)
        ttk.Button(bottom, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=3)
        ttk.Button(bottom, text="Refresh", command=self.refresh).pack(side="right", padx=3)

    def refresh(self):
        q = self.search_var.get().strip().lower()
        pos = self.position_filter.get()
        mf = self.fitness_filter.get()
        min_fit = None if mf == "All" else float(mf)
        self.filtered = []
        for p in self.players:
            hay = " ".join([str(p.get("player_id","")), str(p.get("full_name","")),
                            str(p.get("position","")), str(p.get("team",""))]).lower()
            if q and q not in hay:
                continue
            if pos != "All" and p.get("position") != pos:
                continue
            if min_fit is not None and float(p.get("fitness_score", 0)) < min_fit:
                continue
            self.filtered.append(p)

        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in self.filtered:
            self.tree.insert("", "end", iid=p["player_id"], values=(
                p["player_id"], p["full_name"], p["age"], p["position"], p["team"],
                f"{float(p['fitness_score']):.1f}", p["matches_played"], p["goals"],
                p["assists"], p["medical_status"], f"{efficiency(p):.1f}"
            ))

        total = len(self.players)
        fit = sum(1 for p in self.players if p.get("medical_status") == "Fit")
        injured = sum(1 for p in self.players if p.get("medical_status") in ("Injured", "Recovering"))
        avg = sum(efficiency(p) for p in self.players) / total if total else 0
        self.card_vars[0].set(str(total))
        self.card_vars[1].set(str(fit))
        self.card_vars[2].set(str(injured))
        self.card_vars[3].set(f"{avg:.1f}")

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(APP_NAME, "Select a player first.")
            return None
        pid = sel[0]
        return next((p for p in self.players if p["player_id"] == pid), None)

    def add_player(self):
        self.player_form()

    def edit_selected(self):
        p = self.selected()
        if p:
            self.player_form(p)

    def player_form(self, player=None):
        win = tk.Toplevel(self)
        win.title(("Edit" if player else "Add") + " Player")
        win.geometry("650x700")
        win.transient(self)
        win.grab_set()

        frm = ttk.Frame(win, padding=18)
        frm.pack(fill="both", expand=True)
        fields = [
            ("Player ID", "player_id", "entry"),
            ("Full Name", "full_name", "entry"),
            ("Age", "age", "entry"),
            ("Position", "position", "combo"),
            ("Team", "team", "entry"),
            ("Phone", "phone", "entry"),
            ("Email", "email", "entry"),
            ("Fitness Score (0-100)", "fitness_score", "entry"),
            ("Matches Played", "matches_played", "entry"),
            ("Goals", "goals", "entry"),
            ("Assists", "assists", "entry"),
            ("Training Attendance %", "training_attendance", "entry"),
            ("Contract Start", "contract_start", "entry"),
            ("Contract End", "contract_end", "entry"),
            ("Contract Status", "contract_status", "contract"),
            ("Medical Status", "medical_status", "medical"),
        ]
        vars_ = {}
        for r, (label, key, typ) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=str(player.get(key, "")) if player else "")
            vars_[key] = var
            if typ == "combo":
                w = ttk.Combobox(frm, textvariable=var, values=POSITIONS, state="readonly")
            elif typ == "medical":
                w = ttk.Combobox(frm, textvariable=var, values=MEDICAL, state="readonly")
                if not var.get(): var.set("Fit")
            elif typ == "contract":
                w = ttk.Combobox(frm, textvariable=var, values=CONTRACTS, state="readonly")
                if not var.get(): var.set("Active")
            else:
                w = ttk.Entry(frm, textvariable=var)
            w.grid(row=r, column=1, sticky="ew", pady=5, padx=(10, 0))
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Training Notes").grid(row=len(fields), column=0, sticky="nw", pady=5)
        notes = tk.Text(frm, height=5, width=45)
        notes.grid(row=len(fields), column=1, sticky="ew", pady=5, padx=(10, 0))
        if player:
            notes.insert("1.0", player.get("training_notes", ""))

        def save():
            try:
                pid = vars_["player_id"].get().strip()
                name = vars_["full_name"].get().strip()
                team = vars_["team"].get().strip()
                if not re.match(r"^[A-Za-z0-9_-]{2,30}$", pid):
                    raise ValueError("Player ID must contain 2-30 letters, numbers, _ or -.")
                if not name:
                    raise ValueError("Full Name is required.")
                if not team:
                    raise ValueError("Team is required.")
                duplicate = next((p for p in self.players if p["player_id"] == pid and p is not player), None)
                if duplicate:
                    raise ValueError("Player ID already exists.")
                data = {
                    "player_id": pid,
                    "full_name": name,
                    "age": clean_int(vars_["age"].get(), "Age", 10),
                    "position": vars_["position"].get() or "Other",
                    "team": team,
                    "phone": vars_["phone"].get().strip(),
                    "email": vars_["email"].get().strip(),
                    "fitness_score": clean_float(vars_["fitness_score"].get(), "Fitness Score"),
                    "matches_played": clean_int(vars_["matches_played"].get(), "Matches Played"),
                    "goals": clean_int(vars_["goals"].get(), "Goals"),
                    "assists": clean_int(vars_["assists"].get(), "Assists"),
                    "training_attendance": clean_float(vars_["training_attendance"].get(), "Training Attendance"),
                    "contract_start": vars_["contract_start"].get().strip(),
                    "contract_end": vars_["contract_end"].get().strip(),
                    "contract_status": vars_["contract_status"].get() or "Active",
                    "medical_status": vars_["medical_status"].get() or "Fit",
                    "injuries": player.get("injuries", []) if player else [],
                    "training_notes": notes.get("1.0", "end").strip(),
                }
                if player:
                    idx = self.players.index(player)
                    self.players[idx] = data
                else:
                    self.players.append(data)
                storage.save_players(self.players)
                self.refresh()
                win.destroy()
            except ValueError as e:
                messagebox.showerror("Validation", str(e), parent=win)

        ttk.Button(frm, text="Save Player", command=save).grid(row=len(fields)+1, column=1, sticky="e", pady=18)

    def delete_selected(self):
        p = self.selected()
        if not p:
            return
        if not messagebox.askyesno(APP_NAME, f"Delete {p['full_name']}? This action is recorded only through the automatic file backup."):
            return
        self.players = [x for x in self.players if x["player_id"] != p["player_id"]]
        storage.save_players(self.players)
        self.refresh()

    def show_summary(self):
        p = self.selected()
        if not p:
            return
        win = tk.Toplevel(self)
        win.title("Performance Summary")
        win.geometry("600x500")
        txt = tk.Text(win, wrap="word", padx=15, pady=15)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", performance_summary(p))
        txt.configure(state="disabled")
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)

    def show_injuries(self):
        p = self.selected()
        if not p:
            return
        win = tk.Toplevel(self)
        win.title("Injury History")
        win.geometry("650x500")
        frame = ttk.Frame(win, padding=15)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("date","injury","status","notes"), show="headings")
        for c, h, w in [("date","Date",100),("injury","Injury",180),("status","Status",130),("notes","Notes",210)]:
            tree.heading(c, text=h)
            tree.column(c, width=w)
        tree.pack(fill="both", expand=True)
        for x in p.get("injuries", []):
            tree.insert("", "end", values=(x.get("date",""), x.get("injury",""), x.get("status",""), x.get("notes","")))
        def add():
            dlg = tk.Toplevel(win)
            dlg.title("Add Injury")
            dlg.geometry("500x350")
            f = ttk.Frame(dlg, padding=15); f.pack(fill="both", expand=True)
            v = {}
            for r, (lab, key) in enumerate([("Date","date"),("Injury","injury"),("Status","status"),("Notes","notes")]):
                ttk.Label(f, text=lab).grid(row=r, column=0, sticky="w", pady=5)
                v[key] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d") if key=="date" else "")
                ttk.Entry(f, textvariable=v[key]).grid(row=r, column=1, sticky="ew", pady=5)
            f.columnconfigure(1, weight=1)
            def save():
                if not v["injury"].get().strip():
                    messagebox.showerror("Validation", "Injury description is required.", parent=dlg); return
                p.setdefault("injuries", []).append({k: v[k].get().strip() for k in v})
                storage.save_players(self.players)
                tree.insert("", "end", values=(v["date"].get(),v["injury"].get(),v["status"].get(),v["notes"].get()))
                self.refresh()
                dlg.destroy()
            ttk.Button(f, text="Save", command=save).grid(row=4,column=1,sticky="e",pady=15)
        ttk.Button(win, text="Add Injury Record", command=add).pack(pady=8)

    def export_csv(self):
        try:
            path = storage.export_csv(self.players)
            messagebox.showinfo(APP_NAME, f"CSV exported to:\n{path}")
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def export_json(self):
        try:
            path = storage.export_json(self.players)
            messagebox.showinfo(APP_NAME, f"JSON exported to:\n{path}")
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

if __name__ == "__main__":
    storage.ensure_dirs()
    App().mainloop()
