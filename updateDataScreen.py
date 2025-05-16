from baseScreen import BaseScreen
from tombol import tbl
from tkinter import * 
import tkinter as tk
from tkinter import messagebox,ttk


class UpdateDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id = self.screen_manager.current_asrama_id_context
        self.asrama_nama = self.screen_manager.current_asrama_nama_context
        self.kamar_id = kamar_id
        self.selected_mahasiswa_nim_original = None
        self.nim_baru_entry = None
        self.nama_baru_entry = None
        self.fakultas_baru_pilihan = StringVar()
        self.plh_mahasiswa_var = StringVar()
        self.data_lengkap_mahasiswa_cache = []

    def setup_ui(self):
        self.create_canvas_text(560, 50, text=f"Ubah Data Kamar {self.kamar_id} Asrama {self.asrama_nama}", fill="#F4FEFF", font=("Cooper Black", 20, "bold"))
        opsi_display_db, self.data_lengkap_mahasiswa_cache = self.db_service.get_penghuni_in_kamar(self.kamar_id, self.asrama_id)
        self.create_canvas_text(413, 100, text="Pilih Mahasiswa (NIM - Nama)", fill="#F4FEFF", font=("Arial", 12, "bold"))
        mahasiswa_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.plh_mahasiswa_var, font=("Arial",15), state="readonly", values=opsi_display_db, width=34))
        mahasiswa_dropdown.place(x=350, y=120)
        mahasiswa_dropdown.bind("<<ComboboxSelected>>", self._on_mahasiswa_selected)
        self.create_canvas_text(386, 178, text="NIM Baru (Kosongkan jika tidak diubah)", fill="#F4FEFF", font=("Arial", 10, "bold"))
        self.nim_baru_entry = self.add_widget(Entry(self.canvas, width=30, font=("Arial", 18), bg="#F4FEFF"))
        self.nim_baru_entry.place(x=350, y=190)
        self.create_canvas_text(391, 258, text="Nama Baru (Kosongkan jika tidak diubah)", fill="#F4FEFF", font=("Arial", 10, "bold"))
        self.nama_baru_entry = self.add_widget(Entry(self.canvas, width=30, font=("Arial", 18), bg="#F4FEFF"))
        self.nama_baru_entry.place(x=350, y=270)
        fakultas_list = ["","Teknik", "Ekonomi Bisnis", "Ilmu Sosial", "Kedokteran", "Sastra", "MIPA", "Ilmu Komputer", "Ilmu Keolahragaan", "Vokasi","Ilmu Pendidikan"]
        self.create_canvas_text(405, 328, text="Fakultas Baru", fill="#F4FEFF", font=("Arial", 12, "bold"))
        fakultas_dropdown_widget = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.fakultas_baru_pilihan, values=fakultas_list,width=29, font=("Arial", 18), state="readonly"))
        fakultas_dropdown_widget.place(x=350, y=350)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:") and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0])
            self._on_mahasiswa_selected()
        elif opsi_display_db and (opsi_display_db[0].startswith("Info:") or opsi_display_db[0].startswith("Kesalahan:")):
             self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:
            self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
            if self.nim_baru_entry: self.nim_baru_entry.delete(0, tk.END)
            if self.nama_baru_entry: self.nama_baru_entry.delete(0, tk.END)
            self.fakultas_baru_pilihan.set("")
        tbl(self.canvas, 300, 430, 200, 70, 20, 20, 90, 180, 270, 360, "#F47B07", "Ubah", self._update_data_action)
        tbl(self.canvas, 600, 430, 200, 70, 20, 20, 90, 180, 270, 360,"red","Batal", lambda: self.screen_manager.show_kamar_detail(self.kamar_id))

    def _get_nim_from_selection(self, selection_string):
        if " - " in selection_string: return selection_string.split(" - ")[0]
        return None
    def _on_mahasiswa_selected(self, event=None):
        if not all([self.nim_baru_entry, self.nama_baru_entry, hasattr(self.fakultas_baru_pilihan, 'set')]): return
        selected_display_string = self.plh_mahasiswa_var.get()
        nim_original = self._get_nim_from_selection(selected_display_string)
        self.selected_mahasiswa_nim_original = nim_original
        self.nim_baru_entry.delete(0, tk.END)
        self.nama_baru_entry.delete(0, tk.END)
        self.fakultas_baru_pilihan.set("")
        if nim_original and self.data_lengkap_mahasiswa_cache:
            for data_mhs in self.data_lengkap_mahasiswa_cache:
                if str(data_mhs['nim']) == str(nim_original):
                    self.nama_baru_entry.insert(0, str(data_mhs['nama_penghuni']))
                    self.fakultas_baru_pilihan.set(str(data_mhs['fakultas']) if data_mhs['fakultas'] else "")
                    break
    def _update_data_action(self):
        if not self.selected_mahasiswa_nim_original:
            messagebox.showwarning("Peringatan", "Pilih mahasiswa yang akan diubah datanya.")
            return
        nim_baru = self.nim_baru_entry.get().strip()
        nama_baru = self.nama_baru_entry.get().strip()
        fakultas_baru = self.fakultas_baru_pilihan.get()
        current_nama_entry_val = self.nama_baru_entry.get()
        if not nama_baru and any(char.isalnum() for char in current_nama_entry_val):
             messagebox.showwarning("Input Tidak Valid", "Nama baru tidak boleh dikosongkan jika field diisi.")
             return
        current_nim_entry_val = self.nim_baru_entry.get()
        if not nim_baru and any(char.isalnum() for char in current_nim_entry_val):
             messagebox.showwarning("Input Tidak Valid", "NIM baru tidak boleh dikosongkan jika field diisi.")
             return
        if self.db_service.update_penghuni(self.selected_mahasiswa_nim_original, nim_baru, nama_baru, fakultas_baru):
            self.screen_manager.show_kamar_detail(self.kamar_id)