from baseScreen import BaseScreen
from tombol import tbl
from tkinter import *
from tkinter import messagebox,ttk
class InsertDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id = self.screen_manager.current_asrama_id_context
        self.asrama_nama = self.screen_manager.current_asrama_nama_context
        self.kamar_id = kamar_id
        self.nim_entry = None
        self.nama_entry = None
        self.fakultas_pilihan = StringVar()
    def setup_ui(self):
        self.create_canvas_text(560, 50, text=f"Insert Data Kamar {self.kamar_id} Asrama {self.asrama_nama}", fill="#F4F0FF", font=("Cooper Black", 24, "bold"))
        self.create_canvas_text(365, 188, text="NIM", fill="#F4FEFF", font=("Arial", 12, "bold"))
        self.nim_entry = self.add_widget(Entry(self.canvas, width=30, font=("Arial", 18), bg="#F4FEFF"))
        self.nim_entry.place(x=350, y=200)
        self.create_canvas_text(374, 270, text="Nama", fill="#F4FEFF", font=("Arial", 12, "bold"))
        self.nama_entry = self.add_widget(Entry(self.canvas, width=30, font=("Arial", 18), bg="#F4FEFF"))
        self.nama_entry.place(x=350, y=280)
        fakultas_list = ["","Teknik", "Ekonomi Bisnis", "Ilmu Sosial", "Kedokteran", "Sastra", "MIPA", "Ilmu Komputer", "Ilmu Keolahragaan", "Vokasi","Ilmu Pendidikan"]
        self.fakultas_pilihan.set(fakultas_list[0])
        self.create_canvas_text(385, 340, text="Fakultas", fill="#F4FEFF", font=("Arial", 12, "bold"))
        dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.fakultas_pilihan, values=fakultas_list,width=29, font=("Arial", 18), state="readonly"))
        dropdown.place(x=350, y=360)
        tbl(self.canvas, 300, 430, 200, 70, 20, 20, 90, 180, 270, 360, "#F47B07", "Simpan", self._save_data)
        tbl(self.canvas, 600, 430, 200, 70, 20, 20, 90, 180, 270, 360, "red", "Batal",
            lambda: self.screen_manager.show_kamar_detail(self.kamar_id))

    def _save_data(self):
        nim = self.nim_entry.get()
        nama = self.nama_entry.get()
        fakultas = self.fakultas_pilihan.get()
        if not nim or not nama:
            messagebox.showwarning("Input Tidak Lengkap", "NIM dan Nama tidak boleh kosong.")
            return
        if self.db_service.add_penghuni(nim, nama, fakultas, self.kamar_id, self.asrama_id): 
            self.screen_manager.show_kamar_detail(self.kamar_id) 
