from dbService import DatabaseService
from tkinter import Tk, Canvas, messagebox, NW
import tkinter as tk
from PIL import Image, ImageTk
from screenManager import ScreenManager

class App:
    def __init__(self, root_window):
        self.window = root_window
        self.window.title("Manajemen Asrama")
        self.appwidth = 1080
        self.appheight = 700
        self._setup_window_geometry()
        self.canvas = Canvas(self.window, width=self.appwidth, height=self.appheight)
        self.canvas.place(x=0, y=0)
        self.bg_image_tk = None
        self.blur_image_tk = None 
        self._load_assets()
        MYSQL_HOST = "localhost"
        MYSQL_USER = "root"
        MYSQL_PASSWORD = ""
        MYSQL_DB_NAME = "asrama_db" 
        self.db_service = DatabaseService(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database_name=MYSQL_DB_NAME)
        self.screen_manager = ScreenManager(self, self.db_service)
        if self.db_service.conn and self.db_service.conn.is_connected():
            self._draw_background()
            self.screen_manager.show_main_menu()
        else:
            self.canvas.create_text(self.appwidth / 2, self.appheight / 2, text="Koneksi ke Database Gagal.\nPeriksa konfigurasi dan server MySQL Anda.\nAplikasi tidak dapat dimulai.", font=("Arial", 16, "bold"), fill="red", justify=tk.CENTER)

    def _setup_window_geometry(self):
        screen_width = self.window.winfo_screenwidth()
        x_pos = (screen_width / 2) - (self.appwidth / 2)
        y_pos = 0
        self.window.geometry(f"{self.appwidth}x{self.appheight}+{int(x_pos)}+{int(y_pos)}")
        self.window.resizable(False, False)
    def _load_assets(self):
        try:
            bg_img_pil = Image.open("./assets/um.png").resize((self.appwidth, self.appheight))
            self.bg_image_tk = ImageTk.PhotoImage(bg_img_pil)
            # bgs_pil_blur = Image.open("./assets/um.png").resize((880,500)) 
            # blur_pil = bgs_pil_blur.filter(ImageFilter.GaussianBlur(radius=10))
            # self.blur_image_tk = ImageTk.PhotoImage(blur_pil) 
        except FileNotFoundError: messagebox.showerror("Aset Tidak Ditemukan", "Pastikan file './assets/um.png' ada.")
        except Exception as e: messagebox.showerror("Kesalahan Aset", f"Gagal memuat gambar: {e}")
    def _draw_background(self):
        if self.bg_image_tk: self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor=NW, tags="app_background")
        else: self.canvas.create_rectangle(0,0, self.appwidth, self.appheight, fill="#CCCCCC", tags="app_background")
    def _clear_canvas_for_new_screen(self):
        all_items = self.canvas.find_all()
        for item in all_items:
            if "app_background" not in self.canvas.gettags(item): self.canvas.delete(item)
    def quit(self):
        if messagebox.askokcancel("Keluar", "Anda yakin ingin keluar dari aplikasi?"):
            if self.db_service: self.db_service._close()
            self.window.quit()
            self.window.destroy()