import tkinter as tk
import sqlite3

# ================= DATABASE =================
conn = sqlite3.connect("calc_history.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expression TEXT
)
""")
conn.commit()

# ================= COLORS =================
BG = "#000000"
DISPLAY_BG = "#000000"
NUM_BTN = "#333333"
OP_BTN = "#FF9500"
UTIL_BTN = "#A5A5A5"
WHITE = "#FFFFFF"
BLACK = "#000000"

# ================= LOGIC =================
current = "0"
prev = None
op = None
reset = False

def update_display(val):
    # 🔥 FIX: always BIG font, no shrinking
    display.config(text=val, font=("SF Pro Display", 80, "bold"))

def press(n):
    global current, reset
    if reset:
        current = "0"
        reset = False

    if n == "." and "." in current:
        return

    if current == "0" and n != ".":
        current = n
    else:
        current += n

    update_display(current)

def clear():
    global current, prev, op, reset
    current, prev, op, reset = "0", None, None, False
    history_label.config(text="")
    update_display(current)

def toggle():
    global current
    if current != "0":
        current = current[1:] if current.startswith("-") else "-" + current
        update_display(current)

def percent():
    global current
    current = str(float(current) / 100).rstrip("0").rstrip(".")
    update_display(current)

def set_op(o):
    global prev, op, reset
    prev = float(current)
    op = o
    reset = True
    # ❌ operator NOT shown on LED

def calculate():
    global current, prev, op, reset
    if not op:
        return

    a, b = prev, float(current)
    res = eval(f"{a}{op}{b}")
    res = str(int(res)) if res == int(res) else str(round(res, 8)).rstrip("0").rstrip(".")

    sym = {"+":"+","-":"−","*":"×","/":"÷"}
    expr = f"{a:g} {sym[op]} {b:g} = {res}"

    cursor.execute("INSERT INTO history (expression) VALUES (?)", (expr,))
    conn.commit()

    history_label.config(text=expr)

    current, prev, op, reset = res, None, None, True
    update_display(current)

# ================= SCROLLABLE HISTORY =================
def show_history():
    win = tk.Toplevel(root)
    win.geometry("360x520")
    win.configure(bg="#1C1C1E")

    tk.Label(win, text="History",
             fg="white", bg="#1C1C1E",
             font=("SF Pro Display", 20, "bold")).pack(pady=10)

    container = tk.Frame(win, bg="#1C1C1E")
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg="#1C1C1E", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, command=canvas.yview)
    frame = tk.Frame(canvas, bg="#1C1C1E")

    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    cursor.execute("SELECT expression FROM history ORDER BY id DESC")
    rows = cursor.fetchall()

    if not rows:
        tk.Label(frame, text="No History",
                 fg="#8E8E93", bg="#1C1C1E",
                 font=("SF Pro Display", 16)).pack(pady=40)
        return

    for (exp,) in rows:
        card = tk.Frame(frame, bg="#2C2C2E", padx=14, pady=12)
        card.pack(fill="x", padx=12, pady=6)
        tk.Label(card, text=exp,
                 fg="white", bg="#2C2C2E",
                 font=("SF Pro Display", 16, "bold"),
                 anchor="w", justify="left").pack(fill="x")

# ================= UI =================
root = tk.Tk()
root.geometry("390x700")
root.configure(bg=BG)
root.resizable(False, False)

top = tk.Frame(root, bg=DISPLAY_BG, height=200)
top.pack(fill="x", padx=20, pady=(40,10))
top.pack_propagate(False)

tk.Button(top, text="🕘", bg=DISPLAY_BG, fg="#FF9500",
          bd=0, font=("SF Pro Display", 20),
          command=show_history).pack(anchor="nw")

history_label = tk.Label(top, text="", fg="#A5A5A5",
                         bg=DISPLAY_BG,
                         font=("SF Pro Display", 22),
                         anchor="w")
history_label.pack(fill="x")

display = tk.Label(top, text="0", fg=WHITE, bg=DISPLAY_BG,
                   font=("SF Pro Display", 80, "bold"),
                   anchor="e")
display.pack(fill="both", expand=True)

frame = tk.Frame(root, bg=BG)
frame.pack(pady=20)

layout = [
    ["AC","±","%","÷"],
    ["7","8","9","×"],
    ["4","5","6","−"],
    ["1","2","3","+"],
    ["0",".","="]
]

def btn(txt, r, c, span=1):
    bg = OP_BTN if txt in "+−×÷=" else UTIL_BTN if txt in ["AC","±","%"] else NUM_BTN
    fg = BLACK if txt in ["AC","±","%"] else WHITE
    w,h = 70,70
    width = w*span + (span-1)*8

    cv = tk.Canvas(frame, width=width, height=h, bg=BG, highlightthickness=0)
    cv.create_oval(5,5,h,h,fill=bg,outline="")
    cv.create_oval(width-h,5,width-5,h,fill=bg,outline="")
    cv.create_rectangle(h//2,5,width-h//2,h,fill=bg,outline="")
    cv.create_text(width//2,h//2,text=txt,fill=fg,
                   font=("SF Pro Display",32,"bold"))

    def click(e):
        if txt=="AC": clear()
        elif txt=="±": toggle()
        elif txt=="%": percent()
        elif txt in "+−×÷": set_op({"+":"+","−":"-","×":"*","÷":"/"}[txt])
        elif txt=="=": calculate()
        else: press(txt)

    cv.bind("<Button-1>", click)
    cv.grid(row=r,column=c,columnspan=span,padx=8,pady=8)

for r,row in enumerate(layout):
    col=0
    for t in row:
        if t=="0":
            btn(t,r,col,span=2); col+=2
        else:
            btn(t,r,col); col+=1

root.mainloop()
