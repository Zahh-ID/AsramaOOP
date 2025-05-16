from baseScreen import BaseScreen
from tombol import tbl
from tkinter import ttk, messagebox, StringVar


class DeleteDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id = self.screen_manager.current_asrama_id_context
        self.asrama_nama = self.screen_manager.current_asrama_nama_context
        self.kamar_id = kamar_id
        self.plh_mahasiswa_var = StringVar()
        self.selected_mahasiswa_nim_to_delete = None
    def setup_ui(self):
        self.create_canvas_text(560, 50, text=f"Hapus Data Kamar {self.kamar_id} Asrama {self.asrama_nama}", fill="#F4FEFF", font=("Cooper Black", 20, "bold"))
        opsi_display_db, _ = self.db_service.get_penghuni_in_kamar(self.kamar_id, self.asrama_id)
        self.create_canvas_text(520, 290, text="Pilih Mahasiswa (NIM - Nama) untuk Dihapus", fill="#F4FEFF", font=("Arial", 12, "bold"))
        mahasiswa_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.plh_mahasiswa_var,font=("Arial",15),state="readonly", values=opsi_display_db,width=34))
        mahasiswa_dropdown.place(x=350, y=310)
        mahasiswa_dropdown.bind("<<ComboboxSelected>>", self._on_mahasiswa_selected)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:") and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0])
            self._on_mahasiswa_selected()
        elif opsi_display_db and (opsi_display_db[0].startswith("Info:") or opsi_display_db[0].startswith("Kesalahan:")):
             self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:
            self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
        tbl(self.canvas, 300, 430, 200, 70, 20, 20, 90, 180, 270, 360, "red", "Hapus", self._delete_data_action)
        tbl(self.canvas, 600, 430, 200, 70, 20, 20, 90, 180, 270, 360,"#F47B07","Batal", lambda: self.screen_manager.show_kamar_detail(self.kamar_id))

    def _get_nim_from_selection(self, selection_string):
        if " - " in selection_string: return selection_string.split(" - ")[0]
        return None
    def _on_mahasiswa_selected(self, event=None):
        selected_display_string = self.plh_mahasiswa_var.get()
        self.selected_mahasiswa_nim_to_delete = self._get_nim_from_selection(selected_display_string)
    def _delete_data_action(self):
        if not self.selected_mahasiswa_nim_to_delete:
            messagebox.showwarning("Peringatan", "Pilih mahasiswa yang akan dihapus.")
            return
        konfirmasi = messagebox.askyesno("Konfirmasi Hapus", f"Anda yakin ingin menghapus penghuni dengan NIM {self.selected_mahasiswa_nim_to_delete}?")
        if konfirmasi:
            if self.db_service.delete_penghuni(self.selected_mahasiswa_nim_to_delete):
                self.screen_manager.show_kamar_detail(self.kamar_id)