import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import bcrypt

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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password_hash = Column(String(200))

Base.metadata.create_all(bind=engine)

class RegistrationWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("User Registration")
        self.root.geometry("300x200")
        self.root.configure(bg="#f0f4f8")
        self.registered = False

        tk.Label(root, text="Register New User", font=("Segoe UI", 12, "bold"), bg="#f0f4f8").pack(pady=10)

        tk.Label(root, text="Username:", bg="#f0f4f8").pack()
        self.entry_username = tk.Entry(root)
        self.entry_username.pack()

        tk.Label(root, text="Password:", bg="#f0f4f8").pack()
        self.entry_password = tk.Entry(root, show="*")
        self.entry_password.pack()

        tk.Button(root, text="Register", command=self.register_user, bg="#4a90e2", fg="white").pack(pady=10)

    def register_user(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        session = SessionLocal()
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            messagebox.showerror("Error", "Username already exists.")
            session.close()
            return

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(username=username, password_hash=hashed.decode('utf-8'))
        session.add(new_user)
        session.commit()
        session.close()

        messagebox.showinfo("Success", "Registration successful.")
        self.registered = True
        self.root.destroy()

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("User Login")
        self.root.geometry("300x200")
        self.root.configure(bg="#f0f4f8")
        self.logged_in = False

        tk.Label(root, text="Login", font=("Segoe UI", 12, "bold"), bg="#f0f4f8").pack(pady=10)

        tk.Label(root, text="Username:", bg="#f0f4f8").pack()
        self.entry_username = tk.Entry(root)
        self.entry_username.pack()

        tk.Label(root, text="Password:", bg="#f0f4f8").pack()
        self.entry_password = tk.Entry(root, show="*")
        self.entry_password.pack()

        tk.Button(root, text="Login", command=self.login_user, bg="#4a90e2", fg="white").pack(pady=10)

    def login_user(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both fields.")
            return

        session = SessionLocal()
        user = session.query(User).filter(User.username == username).first()
        session.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            messagebox.showinfo("Success", "Login successful.")
            self.logged_in = True
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials.")

class StartWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Welcome")
        self.root.geometry("300x200")
        self.root.configure(bg="#f0f4f8")
        self.logged_in = False

        tk.Label(root, text="Employee Attrition App", font=("Segoe UI", 14, "bold"), bg="#f0f4f8").pack(pady=20)

        tk.Button(root, text="Login", width=20, command=self.open_login, bg="#4a90e2", fg="white").pack(pady=10)
        tk.Button(root, text="Register", width=20, command=self.open_register, bg="#4a90e2", fg="white").pack(pady=10)

    def open_register(self):
        reg_window = tk.Toplevel(self.root)
        reg_app = RegistrationWindow(reg_window)
        reg_window.wait_window()
        if reg_app.registered:
            self.logged_in = True
            self.root.destroy()

    def open_login(self):
        login_window = tk.Toplevel(self.root)
        login_app = LoginWindow(login_window)
        login_window.wait_window()
        if login_app.logged_in:
            self.logged_in = True
            self.root.destroy()

class EmployeeAttritionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Attrition Analysis")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f4f8")

        self.df = None
        self.canvas_pie = None
        self.canvas_bar = None

        self.frame_top = tk.Frame(root, bg="#dbe9f4", pady=10)
        self.frame_top.pack(fill=tk.X)

        self.btn_load_csv = tk.Button(self.frame_top, text="Load CSV", command=self.load_csv, bg="#4a90e2", fg="white")
        self.btn_load_csv.pack(side=tk.LEFT, padx=10)

        self.btn_save_db = tk.Button(self.frame_top, text="Save to DB", command=self.save_to_db, bg="#4a90e2", fg="white")
        self.btn_save_db.pack(side=tk.LEFT, padx=10)

        self.btn_load_db = tk.Button(self.frame_top, text="Load from DB", command=self.load_from_db, bg="#4a90e2", fg="white")
        self.btn_load_db.pack(side=tk.LEFT, padx=10)

        self.summary_label = tk.Label(root, text="", font=("Arial", 14), bg="#f0f4f8", fg="#333")
        self.summary_label.pack(pady=10)

        self.frame_charts = tk.Frame(root, bg="#f0f4f8")
        self.frame_charts.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        self.frame_pie = tk.LabelFrame(self.frame_charts, text="Attrition Distribution", bg="white", font=("Arial", 12, "bold"))
        self.frame_pie.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.frame_bar = tk.LabelFrame(self.frame_charts, text="OverTime by Attrition", bg="white", font=("Arial", 12, "bold"))
        self.frame_bar.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    def load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        self.df = pd.read_csv(filepath)
        self.show_summary()
        self.plot_charts()

    def save_to_db(self):
        if self.df is None:
            return
        session = SessionLocal()
        for _, row in self.df.iterrows():
            emp = EmployeeAttrition(
                EmployeeID=int(row["EmployeeID"]),
                Attrition=row["Attrition"],
                Department=row["Department"],
                JobRole=row["JobRole"],
                OverTime=row["OverTime"]
            )
            session.merge(emp)
        session.commit()
        session.close()
        messagebox.showinfo("Saved", "Data saved to database.")

    def load_from_db(self):
        session = SessionLocal()
        results = session.query(EmployeeAttrition).all()
        session.close()
        data = {"EmployeeID": [], "Attrition": [], "Department": [], "JobRole": [], "OverTime": []}
        for r in results:
            data["EmployeeID"].append(r.EmployeeID)
            data["Attrition"].append(r.Attrition)
            data["Department"].append(r.Department)
            data["JobRole"].append(r.JobRole)
            data["OverTime"].append(r.OverTime)
        self.df = pd.DataFrame(data)
        self.show_summary()
        self.plot_charts()

    def show_summary(self):
        counts = self.df['Attrition'].value_counts()
        self.summary_label.config(text=f"Attrition - Yes: {counts.get('Yes', 0)} | No: {counts.get('No', 0)}")

    def plot_charts(self):
        if self.canvas_pie:
            self.canvas_pie.get_tk_widget().destroy()
        if self.canvas_bar:
            self.canvas_bar.get_tk_widget().destroy()

        pie_fig, ax1 = plt.subplots(figsize=(4, 4))
        counts = self.df['Attrition'].value_counts()
        ax1.pie(counts.values, labels=counts.index, autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
        ax1.set_title("Attrition Distribution")
        self.canvas_pie = FigureCanvasTkAgg(pie_fig, master=self.frame_pie)
        self.canvas_pie.draw()
        self.canvas_pie.get_tk_widget().pack(expand=True, fill=tk.BOTH)

        bar_fig, ax2 = plt.subplots(figsize=(5, 4))
        df_group = self.df.groupby(['Attrition', 'OverTime']).size().unstack(fill_value=0)
        df_group.plot(kind='bar', ax=ax2)
        ax2.set_title("OverTime by Attrition")
        self.canvas_bar = FigureCanvasTkAgg(bar_fig, master=self.frame_bar)
        self.canvas_bar.draw()
        self.canvas_bar.get_tk_widget().pack(expand=True, fill=tk.BOTH)

if __name__ == "__main__":
    start_root = tk.Tk()
    start_app = StartWindow(start_root)
    start_root.mainloop()

    if start_app.logged_in:
        root = tk.Tk()
        app = EmployeeAttritionApp(root)
        root.mainloop()
