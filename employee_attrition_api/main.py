import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# --- MySQL setup ---
DATABASE_URL = "mysql+pymysql://root:2002@localhost/employee_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class EmployeeAttrition(Base):
    __tablename__ = "employee_attrition"
    EmployeeID = Column(Integer, primary_key=True, index=True)
    Attrition = Column(String(10))
    Department = Column(String(100))
    JobRole = Column(String(100))
    OverTime = Column(String(10))

Base.metadata.create_all(bind=engine)

# --- Tkinter App ---

class EmployeeAttritionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Attrition Analysis")
        self.root.geometry("950x650")
        self.root.configure(bg="#f5f7fa")

        self.df = None
        self.canvas_pie = None
        self.canvas_bar = None

        # Styling
        self.primary_color = "#3f72af"
        self.secondary_color = "#dbe9f4"
        self.accent_color = "#112d4e"
        self.btn_hover_color = "#27496d"
        self.font_main = ("Segoe UI", 11)
        self.font_bold = ("Segoe UI", 11, "bold")
        self.font_title = ("Segoe UI", 13, "bold")

        # Top Frame for buttons
        self.frame_top = tk.Frame(root, bg=self.secondary_color, pady=15, padx=10)
        self.frame_top.pack(fill=tk.X, padx=10, pady=(10, 5))

        btn_style = {
            "font": self.font_bold,
            "bg": self.primary_color,
            "fg": "white",
            "activebackground": self.btn_hover_color,
            "activeforeground": "white",
            "relief": tk.FLAT,
            "bd": 0,
            "width": 28,
            "cursor": "hand2",
            "pady": 8,
            "padx": 5,
        }

        self.btn_load_csv = tk.Button(self.frame_top, text="Load Employee Attrition CSV", command=self.load_csv, **btn_style)
        self.btn_load_csv.pack(side=tk.LEFT, padx=8)
        self._add_hover(self.btn_load_csv, self.primary_color, self.btn_hover_color)

        self.btn_save_db = tk.Button(self.frame_top, text="Save Data to MySQL DB", command=self.save_to_db, **btn_style)
        self.btn_save_db.pack(side=tk.LEFT, padx=8)
        self._add_hover(self.btn_save_db, self.primary_color, self.btn_hover_color)

        self.btn_load_db = tk.Button(self.frame_top, text="Load Data from MySQL DB", command=self.load_from_db, **btn_style)
        self.btn_load_db.pack(side=tk.LEFT, padx=8)
        self._add_hover(self.btn_load_db, self.primary_color, self.btn_hover_color)

        # Summary Label
        self.summary_label = tk.Label(root, text="", font=self.font_title, bg="#f5f7fa", fg=self.accent_color, justify=tk.LEFT)
        self.summary_label.pack(pady=(10,15), anchor="w", padx=20)

        # Frame for charts side by side
        self.frame_charts = tk.Frame(root, bg="#f5f7fa")
        self.frame_charts.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        # Pie Chart Frame
        self.frame_pie = tk.LabelFrame(self.frame_charts, text="Attrition Distribution (Pie Chart)",
                                       bg="white", fg=self.accent_color, font=self.font_bold, labelanchor='n', bd=2, relief=tk.GROOVE)
        self.frame_pie.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Bar Chart Frame
        self.frame_bar = tk.LabelFrame(self.frame_charts, text="OverTime by Attrition (Bar Chart)",
                                       bg="white", fg=self.accent_color, font=self.font_bold, labelanchor='n', bd=2, relief=tk.GROOVE)
        self.frame_bar.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    def _add_hover(self, widget, color_normal, color_hover):
        def on_enter(e):
            widget['bg'] = color_hover
        def on_leave(e):
            widget['bg'] = color_normal
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def load_csv(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filepath:
            return
        try:
            self.df = pd.read_csv(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
            return

        required_cols = {"EmployeeID", "Attrition", "Department", "JobRole", "OverTime"}
        if not required_cols.issubset(set(self.df.columns)):
            messagebox.showerror("Error", f"CSV missing required columns:\n{required_cols}")
            self.df = None
            return

        self.show_summary()
        self.plot_attrition_pie()
        self.plot_overtime_bar()

    def save_to_db(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Load CSV data first before saving.")
            return

        session = SessionLocal()
        try:
            for _, row in self.df.iterrows():
                emp = EmployeeAttrition(
                    EmployeeID=int(row["EmployeeID"]),
                    Attrition=row["Attrition"],
                    Department=row["Department"],
                    JobRole=row["JobRole"],
                    OverTime=row["OverTime"]
                )
                session.merge(emp)  # insert or update
            session.commit()
            messagebox.showinfo("Success", f"{len(self.df)} records saved to database.")
        except Exception as e:
            session.rollback()
            messagebox.showerror("DB Error", str(e))
        finally:
            session.close()

    def load_from_db(self):
        session = SessionLocal()
        try:
            results = session.query(EmployeeAttrition).all()
            if not results:
                messagebox.showinfo("Info", "No data found in database.")
                return

            data = {
                "EmployeeID": [],
                "Attrition": [],
                "Department": [],
                "JobRole": [],
                "OverTime": []
            }

            for row in results:
                data["EmployeeID"].append(row.EmployeeID)
                data["Attrition"].append(row.Attrition)
                data["Department"].append(row.Department)
                data["JobRole"].append(row.JobRole)
                data["OverTime"].append(row.OverTime)

            self.df = pd.DataFrame(data)
            self.show_summary()
            self.plot_attrition_pie()
            self.plot_overtime_bar()
            messagebox.showinfo("Success", f"Loaded {len(self.df)} records from database.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            session.close()

    def show_summary(self):
        counts = self.df['Attrition'].value_counts()
        summary_text = "Attrition Counts:\n"
        for val in ['Yes', 'No']:
            summary_text += f"  {val}: {counts.get(val, 0)}\n"
        self.summary_label.config(text=summary_text)

    def plot_attrition_pie(self):
        counts = self.df['Attrition'].value_counts()
        labels = counts.index.tolist()
        sizes = counts.values.tolist()

        fig, ax = plt.subplots(figsize=(4, 4), dpi=80)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
               colors=['#ff6b6b','#4ecdc4'], textprops={'fontsize': 12})
        ax.set_title("Attrition Distribution", fontsize=14, fontweight='bold')

        if self.canvas_pie:
            self.canvas_pie.get_tk_widget().destroy()

        self.canvas_pie = FigureCanvasTkAgg(fig, master=self.frame_pie)
        self.canvas_pie.draw()
        self.canvas_pie.get_tk_widget().pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    def plot_overtime_bar(self):
        # Count OverTime grouped by Attrition
        df_counts = self.df.groupby(['Attrition', 'OverTime']).size().unstack(fill_value=0)
        # Ensure columns order: Yes, No
        df_counts = df_counts[['Yes', 'No']] if all(x in df_counts.columns for x in ['Yes', 'No']) else df_counts

        fig, ax = plt.subplots(figsize=(5, 4), dpi=80)
        df_counts.plot(kind='bar', stacked=False, ax=ax, color=['#1fab89', '#ff6f59'])

        ax.set_title("OverTime Count by Attrition", fontsize=14, fontweight='bold')
        ax.set_xlabel("Attrition", fontsize=12)
        ax.set_ylabel("Count", fontsize=12)
        ax.legend(title="OverTime", fontsize=10, title_fontsize=11)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        if self.canvas_bar:
            self.canvas_bar.get_tk_widget().destroy()

        self.canvas_bar = FigureCanvasTkAgg(fig, master=self.frame_bar)
        self.canvas_bar.draw()
        self.canvas_bar.get_tk_widget().pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeAttritionApp(root)
    root.mainloop()
