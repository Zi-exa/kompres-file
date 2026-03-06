"""
Kompres File - Video & Photo Compressor
Aplikasi kompresi file video dan foto dengan GUI modern.
Dapat dipanggil dari Windows Context Menu.
Mendukung multi-file: beberapa file dikompres dalam satu window.
"""

import sys
import os
import subprocess
import threading
import socket
import json
import time
import ctypes
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# ============================================================
# KONFIGURASI
# ============================================================

VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}

QUALITY_PRESETS = {
    'video': {
        'Rendah (file kecil)':   {'crf': 32, 'preset': 'fast'},
        'Sedang (seimbang)':     {'crf': 26, 'preset': 'medium'},
        'Tinggi (kualitas bagus)': {'crf': 20, 'preset': 'slow'},
    },
    'image': {
        'Rendah (file kecil)':   {'quality': 30, 'resize': 0.5},
        'Sedang (seimbang)':     {'quality': 60, 'resize': 0.75},
        'Tinggi (kualitas bagus)': {'quality': 85, 'resize': 1.0},
    }
}

# Port untuk single-instance mechanism
INSTANCE_PORT = 39517
# Waktu tunggu (detik) untuk mengumpulkan file dari context menu multi-select
COLLECT_DELAY = 0.8

# ============================================================
# WARNA TEMA DARK
# ============================================================
COLORS = {
    'bg':          '#1a1a2e',
    'bg_card':     '#16213e',
    'bg_input':    '#0f3460',
    'accent':      '#e94560',
    'accent_hover':'#ff6b81',
    'text':        '#eaeaea',
    'text_dim':    '#8892b0',
    'success':     '#00d2d3',
    'border':      '#233554',
    'progress_bg': '#0f3460',
    'progress_fg': '#e94560',
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_file_type(filepath):
    """Mendeteksi apakah file adalah video atau foto."""
    ext = Path(filepath).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    elif ext in IMAGE_EXTENSIONS:
        return 'image'
    return None


def format_size(size_bytes):
    """Format ukuran file menjadi string yang mudah dibaca."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024**2):.1f} MB"
    else:
        return f"{size_bytes / (1024**3):.2f} GB"


def get_output_path(input_path):
    """Generate output file path dengan suffix _compressed."""
    p = Path(input_path)
    stem = p.stem
    ext = p.suffix
    output = p.parent / f"{stem}_compressed{ext}"
    counter = 1
    while output.exists():
        output = p.parent / f"{stem}_compressed_{counter}{ext}"
        counter += 1
    return str(output)


# ============================================================
# SINGLE INSTANCE MANAGEMENT
# ============================================================

def try_send_to_existing(filepaths):
    """Kirim file paths ke instance yang sudah berjalan via socket."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(('127.0.0.1', INSTANCE_PORT))
        data = json.dumps(filepaths).encode('utf-8')
        sock.sendall(data)
        sock.close()
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


# Mailbox: temp directory untuk mengumpulkan file paths dari semua instance
MAILBOX_DIR = os.path.join(tempfile.gettempdir(), 'kompres_file_mailbox')
MUTEX_NAME = "KompresFile_SingleInstance"


def add_to_mailbox(filepaths):
    """Tulis file paths ke mailbox (satu file per proses)."""
    os.makedirs(MAILBOX_DIR, exist_ok=True)
    fname = f"batch_{os.getpid()}_{time.time_ns()}.json"
    fpath = os.path.join(MAILBOX_DIR, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(filepaths, f)


def collect_mailbox():
    """Baca semua file paths dari mailbox, lalu bersihkan."""
    result = []
    if not os.path.exists(MAILBOX_DIR):
        return result
    for name in os.listdir(MAILBOX_DIR):
        fpath = os.path.join(MAILBOX_DIR, name)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                items = json.load(f)
            result.extend(items)
            os.remove(fpath)
        except Exception:
            try:
                os.remove(fpath)
            except Exception:
                pass
    # Dedupe, preserve order
    seen = set()
    deduped = []
    for fp in result:
        if fp not in seen:
            seen.add(fp)
            deduped.append(fp)
    return deduped


def try_create_mutex():
    """Coba buat named mutex. Return handle jika berhasil, None jika sudah ada."""
    ERROR_ALREADY_EXISTS = 183
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return handle


class FileServer:
    """Server socket untuk menerima file paths dari instance lain."""

    def __init__(self):
        self.files = []
        self.lock = threading.Lock()
        self.server = None
        self.running = False
        self.on_files_added = None  # callback(new_files_list)

    def start(self):
        """Start the server. Returns True if successfully bound, False otherwise."""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('127.0.0.1', INSTANCE_PORT))
            self.server.listen(20)
            self.server.settimeout(1)
            self.running = True
            thread = threading.Thread(target=self._listen, daemon=True)
            thread.start()
            return True
        except OSError:
            return False

    def _listen(self):
        while self.running:
            try:
                conn, _ = self.server.accept()
                data = b''
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                conn.close()

                files = json.loads(data.decode('utf-8'))
                new_files = []
                with self.lock:
                    for f in files:
                        if f not in self.files and os.path.isfile(f):
                            self.files.append(f)
                            new_files.append(f)

                if new_files and self.on_files_added:
                    self.on_files_added(new_files)
            except socket.timeout:
                continue
            except Exception:
                continue

    def add_files(self, files):
        with self.lock:
            for f in files:
                if f not in self.files:
                    self.files.append(f)

    def stop(self):
        self.running = False
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass


# ============================================================
# FUNGSI KOMPRESI
# ============================================================

def compress_video(input_path, output_path, quality_name, progress_callback=None, done_callback=None):
    """Kompres video menggunakan FFmpeg."""
    preset = QUALITY_PRESETS['video'][quality_name]
    crf = preset['crf']
    speed = preset['preset']

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', 'libx264',
        '-crf', str(crf),
        '-preset', speed,
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        output_path
    ]

    try:
        # Dapatkan durasi video untuk progress
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            total_duration = float(result.stdout.strip())
        except (ValueError, AttributeError):
            total_duration = 0

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        for line in process.stderr:
            if 'time=' in line and total_duration > 0:
                try:
                    time_str = line.split('time=')[1].split(' ')[0]
                    parts = time_str.split(':')
                    current_time = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    progress = min(current_time / total_duration * 100, 99)
                    if progress_callback:
                        progress_callback(progress)
                except (IndexError, ValueError):
                    pass

        process.wait()

        if process.returncode == 0:
            if progress_callback:
                progress_callback(100)
            if done_callback:
                done_callback(True, output_path)
        else:
            if done_callback:
                done_callback(False, "FFmpeg error - pastikan FFmpeg sudah terinstall")

    except FileNotFoundError:
        if done_callback:
            done_callback(False, "FFmpeg tidak ditemukan!\nInstall FFmpeg dan tambahkan ke PATH.")
    except Exception as e:
        if done_callback:
            done_callback(False, str(e))


def compress_image(input_path, output_path, quality_name, progress_callback=None, done_callback=None):
    """Kompres foto menggunakan Pillow."""
    try:
        from PIL import Image
    except ImportError:
        if done_callback:
            done_callback(False, "Pillow belum terinstall!\nJalankan: pip install Pillow")
        return

    preset = QUALITY_PRESETS['image'][quality_name]
    quality = preset['quality']
    resize_factor = preset['resize']

    try:
        if progress_callback:
            progress_callback(10)

        img = Image.open(input_path)

        if progress_callback:
            progress_callback(30)

        if resize_factor < 1.0:
            new_width = int(img.width * resize_factor)
            new_height = int(img.height * resize_factor)
            img = img.resize((new_width, new_height), Image.LANCZOS)

        if progress_callback:
            progress_callback(60)

        ext = Path(output_path).suffix.lower()
        if ext in ('.jpg', '.jpeg') and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        save_kwargs = {}
        if ext in ('.jpg', '.jpeg'):
            save_kwargs = {'quality': quality, 'optimize': True}
        elif ext == '.png':
            save_kwargs = {'optimize': True}
        elif ext == '.webp':
            save_kwargs = {'quality': quality, 'method': 6}
        else:
            save_kwargs = {'quality': quality} if quality else {}

        if progress_callback:
            progress_callback(80)

        img.save(output_path, **save_kwargs)

        if progress_callback:
            progress_callback(100)

        if done_callback:
            done_callback(True, output_path)

    except Exception as e:
        if done_callback:
            done_callback(False, str(e))


# ============================================================
# GUI APPLICATION (MULTI-FILE)
# ============================================================

class CompressorApp:
    ST_PENDING = 'pending'
    ST_ACTIVE = 'active'
    ST_DONE = 'done'
    ST_ERROR = 'error'

    ST_ICONS = {
        'pending':  '\u2B1C',   # white square
        'active':   '\u23F3',   # hourglass
        'done':     '\u2705',   # check
        'error':    '\u274C',   # cross
    }

    def __init__(self, server):
        self.server = server
        self.filepaths = []
        self.file_status = {}
        self.file_result = {}
        self.file_widgets = {}
        self.is_compressing = False
        self.current_index = 0

        # Ambil file dari server
        with server.lock:
            for f in server.files:
                if get_file_type(f) and f not in self.filepaths:
                    self.filepaths.append(f)
                    self.file_status[f] = self.ST_PENDING

        if not self.filepaths:
            messagebox.showerror("Error", "Tidak ada file video/foto yang valid.")
            server.stop()
            sys.exit(1)

        # Callback untuk file baru dari instance lain
        server.on_files_added = self._on_server_files

        # Set taskbar icon identity
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('kompresfile.compressor')
        except Exception:
            pass

        self.root = tk.Tk()
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ----------------------------------------------------------
    # WINDOW SETUP
    # ----------------------------------------------------------

    def _setup_window(self):
        count = len(self.filepaths)
        self.root.title(f"Kompres File ({count})")
        self.root.configure(bg=COLORS['bg'])
        self.root.resizable(False, False)

        icon_path = Path(__file__).parent / 'kompres.ico'
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

        width, height = 550, 720
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+{(sx-width)//2}+{(sy-height)//2}")

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('Card.TFrame', background=COLORS['bg_card'])
        s.configure('Dark.TFrame', background=COLORS['bg'])
        s.configure('Title.TLabel', background=COLORS['bg'],
                    foreground=COLORS['text'], font=('Segoe UI', 18, 'bold'))
        s.configure('Subtitle.TLabel', background=COLORS['bg'],
                    foreground=COLORS['text_dim'], font=('Segoe UI', 10))
        s.configure('CardTitle.TLabel', background=COLORS['bg_card'],
                    foreground=COLORS['text'], font=('Segoe UI', 11, 'bold'))
        s.configure('CardText.TLabel', background=COLORS['bg_card'],
                    foreground=COLORS['text_dim'], font=('Segoe UI', 10))
        s.configure('CardValue.TLabel', background=COLORS['bg_card'],
                    foreground=COLORS['accent'], font=('Segoe UI', 10, 'bold'))
        s.configure('Result.TLabel', background=COLORS['bg_card'],
                    foreground=COLORS['success'], font=('Segoe UI', 12, 'bold'))
        s.configure('ResultDetail.TLabel', background=COLORS['bg_card'],
                    foreground=COLORS['text_dim'], font=('Segoe UI', 10))
        s.configure('Custom.Horizontal.TProgressbar',
                    troughcolor=COLORS['progress_bg'],
                    background=COLORS['progress_fg'], thickness=8)
        s.configure('Card.TRadiobutton', background=COLORS['bg_card'],
                    foreground=COLORS['text'], font=('Segoe UI', 10))
        s.map('Card.TRadiobutton',
              background=[('active', COLORS['bg_card'])],
              foreground=[('active', COLORS['accent'])])

    # ----------------------------------------------------------
    # CREATE WIDGETS
    # ----------------------------------------------------------

    def _create_widgets(self):
        main = ttk.Frame(self.root, style='Dark.TFrame')
        main.pack(fill='both', expand=True, padx=20, pady=15)

        # --- HEADER ---
        self.header_label = ttk.Label(
            main, text=f"Kompres {len(self.filepaths)} File", style='Title.TLabel')
        self.header_label.pack(anchor='w')
        ttk.Label(main, text="Pilih beberapa file, kompres dalam satu window",
                  style='Subtitle.TLabel').pack(anchor='w', pady=(2, 15))

        # --- FILE LIST CARD ---
        files_card = ttk.Frame(main, style='Card.TFrame')
        files_card.pack(fill='x', pady=(0, 10))
        files_inner = ttk.Frame(files_card, style='Card.TFrame')
        files_inner.pack(fill='both', padx=16, pady=14)

        self.files_title = ttk.Label(
            files_inner, text=f"Files ({len(self.filepaths)})", style='CardTitle.TLabel')
        self.files_title.pack(anchor='w')
        tk.Frame(files_inner, bg=COLORS['border'], height=1).pack(fill='x', pady=(8, 8))

        # Scrollable list area
        list_box = tk.Frame(files_inner, bg=COLORS['bg_card'])
        list_box.pack(fill='both')

        max_visible = min(len(self.filepaths), 5)
        canvas_h = max_visible * 28

        self.files_canvas = tk.Canvas(
            list_box, bg=COLORS['bg_card'], highlightthickness=0, height=canvas_h)
        self.scrollbar = ttk.Scrollbar(
            list_box, orient='vertical', command=self.files_canvas.yview)
        self.files_frame = tk.Frame(self.files_canvas, bg=COLORS['bg_card'])

        self.files_frame.bind(
            '<Configure>',
            lambda e: self.files_canvas.configure(scrollregion=self.files_canvas.bbox('all')))

        self.canvas_window = self.files_canvas.create_window(
            (0, 0), window=self.files_frame, anchor='nw')
        self.files_canvas.bind(
            '<Configure>',
            lambda e: self.files_canvas.itemconfig(self.canvas_window, width=e.width))
        self.files_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.files_canvas.pack(side='left', fill='both', expand=True)
        if len(self.filepaths) > 5:
            self.scrollbar.pack(side='right', fill='y')

        # Mouse wheel
        def _wheel(event):
            self.files_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        self.files_canvas.bind('<MouseWheel>', _wheel)
        self.files_frame.bind('<MouseWheel>', _wheel)

        for fp in self.filepaths:
            self._create_file_row(fp)

        # --- QUALITY CARD ---
        q_card = ttk.Frame(main, style='Card.TFrame')
        q_card.pack(fill='x', pady=(0, 10))
        q_inner = ttk.Frame(q_card, style='Card.TFrame')
        q_inner.pack(fill='x', padx=16, pady=14)

        ttk.Label(q_inner, text="Kualitas Kompresi", style='CardTitle.TLabel').pack(anchor='w')
        tk.Frame(q_inner, bg=COLORS['border'], height=1).pack(fill='x', pady=(8, 8))

        self.quality_var = tk.StringVar(value='Sedang (seimbang)')
        for name in ['Rendah (file kecil)', 'Sedang (seimbang)', 'Tinggi (kualitas bagus)']:
            ttk.Radiobutton(q_inner, text=name, variable=self.quality_var,
                            value=name, style='Card.TRadiobutton').pack(anchor='w', pady=2)

        # --- PROGRESS CARD ---
        p_card = ttk.Frame(main, style='Card.TFrame')
        p_card.pack(fill='x', pady=(0, 10))
        p_inner = ttk.Frame(p_card, style='Card.TFrame')
        p_inner.pack(fill='x', padx=16, pady=14)

        self.cur_label = ttk.Label(p_inner, text="Siap untuk mengompres",
                                   style='CardText.TLabel')
        self.cur_label.pack(anchor='w')
        self.cur_bar = ttk.Progressbar(p_inner, mode='determinate',
                                       style='Custom.Horizontal.TProgressbar')
        self.cur_bar.pack(fill='x', pady=(6, 2))
        self.cur_pct = ttk.Label(p_inner, text="0%", style='CardValue.TLabel')
        self.cur_pct.pack(anchor='e')

        tk.Frame(p_inner, bg=COLORS['border'], height=1).pack(fill='x', pady=(6, 6))

        self.all_label = ttk.Label(p_inner, text=f"Total: 0 / {len(self.filepaths)}",
                                   style='CardText.TLabel')
        self.all_label.pack(anchor='w')
        self.all_bar = ttk.Progressbar(p_inner, mode='determinate',
                                       style='Custom.Horizontal.TProgressbar')
        self.all_bar.pack(fill='x', pady=(6, 2))
        self.all_pct = ttk.Label(p_inner, text="0%", style='CardValue.TLabel')
        self.all_pct.pack(anchor='e')

        # Result (hidden initially)
        self.result_frame = ttk.Frame(p_inner, style='Card.TFrame')
        self.result_label = ttk.Label(self.result_frame, text="", style='Result.TLabel')
        self.result_label.pack(anchor='w')
        self.result_detail = ttk.Label(self.result_frame, text="", style='ResultDetail.TLabel')
        self.result_detail.pack(anchor='w', pady=(4, 0))

        # --- BUTTONS ---
        btn_frame = ttk.Frame(main, style='Dark.TFrame')
        btn_frame.pack(fill='x', pady=(5, 0))

        self.compress_btn = tk.Button(
            btn_frame, text="Mulai Kompres",
            font=('Segoe UI', 12, 'bold'),
            bg=COLORS['accent'], fg='white',
            activebackground=COLORS['accent_hover'], activeforeground='white',
            relief='flat', cursor='hand2', bd=0, padx=20, pady=10,
            command=self.start_compress_all)
        self.compress_btn.pack(fill='x')

        self.open_btn = tk.Button(
            btn_frame, text="Buka Folder Hasil",
            font=('Segoe UI', 10),
            bg=COLORS['bg_input'], fg=COLORS['text'],
            activebackground=COLORS['border'], activeforeground=COLORS['text'],
            relief='flat', cursor='hand2', bd=0, padx=10, pady=8,
            command=self.open_output_folder)
        # open_btn ditampilkan setelah selesai

    # ----------------------------------------------------------
    # FILE LIST ROWS
    # ----------------------------------------------------------

    def _create_file_row(self, filepath):
        row = tk.Frame(self.files_frame, bg=COLORS['bg_card'])
        row.pack(fill='x', pady=1)
        row.bind('<MouseWheel>',
                 lambda e: self.files_canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

        ftype = get_file_type(filepath)
        tag = "VID" if ftype == 'video' else "IMG"
        tag_color = '#6c5ce7' if ftype == 'video' else '#00b894'

        status_lbl = tk.Label(row, text=self.ST_ICONS[self.ST_PENDING],
                              bg=COLORS['bg_card'], fg=COLORS['text_dim'],
                              font=('Segoe UI', 9), width=3)
        status_lbl.pack(side='left')

        tag_lbl = tk.Label(row, text=tag, bg=tag_color, fg='white',
                           font=('Segoe UI', 7, 'bold'), padx=4, pady=0)
        tag_lbl.pack(side='left', padx=(0, 6))

        name = Path(filepath).name
        disp = name if len(name) <= 32 else name[:29] + "..."
        name_lbl = tk.Label(row, text=disp, bg=COLORS['bg_card'],
                            fg=COLORS['text_dim'], font=('Segoe UI', 9), anchor='w')
        name_lbl.pack(side='left', fill='x', expand=True)

        result_lbl = tk.Label(row, text="", bg=COLORS['bg_card'],
                              fg=COLORS['success'], font=('Segoe UI', 8, 'bold'))
        result_lbl.pack(side='right', padx=(4, 0))

        size = os.path.getsize(filepath)
        size_lbl = tk.Label(row, text=format_size(size), bg=COLORS['bg_card'],
                            fg=COLORS['accent'], font=('Segoe UI', 8, 'bold'))
        size_lbl.pack(side='right')

        self.file_widgets[filepath] = {
            'row': row, 'status': status_lbl, 'name': name_lbl,
            'size': size_lbl, 'result': result_lbl,
        }

    def _update_row_status(self, filepath, status, result_text=""):
        self.file_status[filepath] = status
        w = self.file_widgets.get(filepath)
        if not w:
            return
        w['status'].configure(text=self.ST_ICONS[status])
        if status == self.ST_ACTIVE:
            w['name'].configure(fg=COLORS['text'])
        elif status == self.ST_DONE:
            w['name'].configure(fg=COLORS['success'])
            if result_text:
                w['result'].configure(text=result_text, fg=COLORS['success'])
        elif status == self.ST_ERROR:
            w['name'].configure(fg='#ff6b6b')
            w['result'].configure(text="Error", fg='#ff6b6b')

    def _update_header(self):
        n = len(self.filepaths)
        self.header_label.configure(text=f"Kompres {n} File")
        self.files_title.configure(text=f"Files ({n})")
        self.root.title(f"Kompres File ({n})")

    # ----------------------------------------------------------
    # SERVER FILES CALLBACK
    # ----------------------------------------------------------

    def _on_server_files(self, new_files):
        self.root.after(0, self._add_new_files, new_files)

    def _add_new_files(self, new_files):
        for f in new_files:
            if f not in self.file_status and get_file_type(f):
                self.filepaths.append(f)
                self.file_status[f] = self.ST_PENDING
                self._create_file_row(f)
        self._update_header()
        # Update total label
        done = sum(1 for s in self.file_status.values() if s in (self.ST_DONE, self.ST_ERROR))
        self.all_label.configure(text=f"Total: {done} / {len(self.filepaths)}")

        # Bawa window ke depan
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(300, lambda: self.root.attributes('-topmost', False))

    # ----------------------------------------------------------
    # COMPRESSION LOGIC
    # ----------------------------------------------------------

    def start_compress_all(self):
        if self.is_compressing:
            return

        self.is_compressing = True
        self.compress_btn.configure(state='disabled', bg=COLORS['border'])
        self.result_frame.pack_forget()
        try:
            self.open_btn.pack_forget()
        except Exception:
            pass
        self.current_index = 0

        # Reset semua status
        for f in self.filepaths:
            self._update_row_status(f, self.ST_PENDING)

        self._compress_next()

    def _compress_next(self):
        # Cari file pending berikutnya
        while self.current_index < len(self.filepaths):
            fp = self.filepaths[self.current_index]
            if self.file_status[fp] == self.ST_PENDING:
                break
            self.current_index += 1

        if self.current_index >= len(self.filepaths):
            self._all_done()
            return

        fp = self.filepaths[self.current_index]
        ftype = get_file_type(fp)
        quality = self.quality_var.get()
        output = get_output_path(fp)

        self._update_row_status(fp, self.ST_ACTIVE)

        fname = Path(fp).name
        idx = self.current_index + 1
        total = len(self.filepaths)
        self.cur_label.configure(text=f"Mengompres: {fname} ({idx}/{total})")
        self.cur_bar['value'] = 0
        self.cur_pct.configure(text="0%")

        def progress_cb(pct):
            self.root.after(0, self._update_progress, pct)

        def done_cb(success, result):
            self.root.after(0, self._on_file_done, fp, output, success, result)

        if ftype == 'video':
            t = threading.Thread(target=compress_video,
                                 args=(fp, output, quality, progress_cb, done_cb), daemon=True)
        else:
            t = threading.Thread(target=compress_image,
                                 args=(fp, output, quality, progress_cb, done_cb), daemon=True)
        t.start()

    def _update_progress(self, pct):
        self.cur_bar['value'] = pct
        self.cur_pct.configure(text=f"{pct:.0f}%")

        done = sum(1 for s in self.file_status.values() if s in (self.ST_DONE, self.ST_ERROR))
        total = len(self.filepaths)
        overall = (done + pct / 100) / total * 100
        self.all_bar['value'] = overall
        self.all_pct.configure(text=f"{overall:.0f}%")
        self.all_label.configure(text=f"Total: {done} / {total}")

    def _on_file_done(self, filepath, output_path, success, result):
        if success:
            orig = os.path.getsize(filepath)
            comp = os.path.getsize(result)
            saved = orig - comp
            pct = (saved / orig * 100) if orig > 0 else 0
            self._update_row_status(filepath, self.ST_DONE, f"-{pct:.0f}%")
            self.file_result[filepath] = {
                'output': result, 'saved': saved, 'saved_pct': pct,
                'original': orig, 'compressed': comp
            }
        else:
            self._update_row_status(filepath, self.ST_ERROR)
            self.file_result[filepath] = {'error': str(result)}

        self.current_index += 1
        self._compress_next()

    def _all_done(self):
        self.is_compressing = False

        ok = sum(1 for s in self.file_status.values() if s == self.ST_DONE)
        fail = sum(1 for s in self.file_status.values() if s == self.ST_ERROR)
        total = len(self.filepaths)
        total_saved = sum(r.get('saved', 0) for r in self.file_result.values() if 'saved' in r)

        self.cur_label.configure(text="Semua file selesai diproses!")
        self.cur_bar['value'] = 100
        self.cur_pct.configure(text="100%")
        self.all_bar['value'] = 100
        self.all_pct.configure(text="100%")
        self.all_label.configure(text=f"Total: {total} / {total}")

        self.result_frame.pack(fill='x', pady=(10, 0))
        self.result_label.configure(text=f"Selesai! {ok} berhasil, {fail} gagal")
        self.result_detail.configure(text=f"Total hemat: {format_size(total_saved)}")

        # Ganti tombol "Mulai Kompres" menjadi "Selesai - Tutup"
        self.compress_btn.configure(
            state='normal',
            text="Selesai - Tutup",
            bg=COLORS['success'], fg='white',
            activebackground='#00b5b5',
            command=self._on_close)

        if ok > 0:
            self.open_btn.pack(fill='x', pady=(8, 0))

    # ----------------------------------------------------------
    # MISC
    # ----------------------------------------------------------

    def open_output_folder(self):
        for fp in self.filepaths:
            r = self.file_result.get(fp)
            if r and 'output' in r and os.path.exists(r['output']):
                subprocess.Popen(f'explorer /select,"{r["output"]}"',
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                return

    def _on_close(self):
        self.server.stop()
        self.root.destroy()


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        messagebox.showerror(
            "Error",
            "Tidak ada file yang dipilih.\nGunakan klik kanan pada file untuk mengompres."
        )
        sys.exit(1)

    filepaths = [f for f in sys.argv[1:] if os.path.isfile(f)]

    if not filepaths:
        messagebox.showerror("Error", "File tidak ditemukan.")
        sys.exit(1)

    # Step 1: Tulis file kita ke mailbox
    add_to_mailbox(filepaths)

    # Step 2: Coba jadi instance utama via named mutex (atomic, no race condition)
    mutex_handle = try_create_mutex()

    if mutex_handle is None:
        # Instance lain sudah jadi primary - file kita sudah di mailbox
        # Coba kirim via socket juga (untuk kasus GUI sudah berjalan lama)
        for _ in range(5):
            if try_send_to_existing(filepaths):
                break
            time.sleep(0.3)
        sys.exit(0)

    # Kita adalah instance utama!
    # Tunggu instance lain menulis ke mailbox
    time.sleep(COLLECT_DELAY)

    # Kumpulkan semua file dari mailbox
    all_files = collect_mailbox()
    if not all_files:
        all_files = filepaths  # Fallback

    # Start socket server untuk file yang datang saat GUI sudah berjalan
    server = FileServer()
    server.add_files(all_files)
    server.start()

    # Jalankan GUI
    app = CompressorApp(server)

    # Cleanup mutex
    kernel32 = ctypes.windll.kernel32
    kernel32.ReleaseMutex(mutex_handle)
    kernel32.CloseHandle(mutex_handle)
