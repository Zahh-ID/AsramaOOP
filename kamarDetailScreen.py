from baseScreen import BaseScreen
from tombol import tbl
from tkinter import ttk
import tkinter as tk


class KamarDetailScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id = self.screen_manager.current_asrama_id_context
        self.asrama_nama = self.screen_manager.current_asrama_nama_context
        self.kamar_id = kamar_id
        self.penghuni_treeview = None
        self.treeview_scrollbar = None

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Custom.Treeview", background="#E1E1E1", fieldbackground="#FFFFFF", foreground="black")
        style.configure("Custom.Treeview.Heading", background="yellow", foreground="black", font=('Arial', 10, 'bold'), relief="flat")
        style.map("Custom.Treeview.Heading", background=[('active', '#FFD700')])

        self.create_canvas_text(self.app_instance.appwidth / 2, 80, text=f"Asrama {self.asrama_nama} - Kamar {self.kamar_id}", fill="#F4F0FF", font=("Cooper Black", 22, "bold"))
        info_text_x = self.app_instance.appwidth / 2
        info_text_y = 120
        jml_penghuni = self.db_service.get_jumlah_penghuni(self.kamar_id, self.asrama_id)
        kapasitas = self.db_service.get_kapasitas_kamar(self.kamar_id, self.asrama_id)
        self.create_canvas_text(info_text_x, info_text_y, text=f"Data Penghuni ({jml_penghuni}/{kapasitas})", fill="#F4F0FF", font=("Cooper Black", 18, "bold"))

        table_padding_horizontal = 50
        table_padding_top = 20
        table_padding_bottom = 70 
        table_x = table_padding_horizontal
        table_y = info_text_y + table_padding_top + 20
        table_container_width = self.app_instance.appwidth - (2 * table_padding_horizontal)
        scrollbar_width = 20
        treeview_actual_width = table_container_width - scrollbar_width
        treeview_display_height = self.app_instance.appheight - table_y - table_padding_bottom - 120 

        columns = ("no", "nim", "nama", "fakultas")
        self.penghuni_treeview = ttk.Treeview(self.canvas, columns=columns, show='headings', style="Custom.Treeview")
        self.penghuni_treeview.heading("no", text="No.")
        self.penghuni_treeview.heading("nim", text="NIM")
        self.penghuni_treeview.heading("nama", text="Nama Mahasiswa")
        self.penghuni_treeview.heading("fakultas", text="Fakultas")
        self.penghuni_treeview.column("no", width=int(treeview_actual_width * 0.05), anchor=tk.CENTER, stretch=tk.NO)
        self.penghuni_treeview.column("nim", width=int(treeview_actual_width * 0.25), anchor=tk.W, stretch=tk.YES)
        self.penghuni_treeview.column("nama", width=int(treeview_actual_width * 0.40), anchor=tk.W, stretch=tk.YES)
        self.penghuni_treeview.column("fakultas", width=int(treeview_actual_width * 0.30), anchor=tk.W, stretch=tk.YES)
        
        self.treeview_scrollbar = ttk.Scrollbar(self.canvas, orient="vertical", command=self.penghuni_treeview.yview)
        self.penghuni_treeview.configure(yscrollcommand=self.treeview_scrollbar.set)

        _, daftar_penghuni = self.db_service.get_penghuni_in_kamar(self.kamar_id, self.asrama_id)
        for item in self.penghuni_treeview.get_children(): self.penghuni_treeview.delete(item)
        if daftar_penghuni and not (isinstance(daftar_penghuni[0], str) and daftar_penghuni[0].startswith("Info:")):
            for i, penghuni in enumerate(daftar_penghuni):
                fakultas_str = penghuni['fakultas'] if penghuni['fakultas'] else "N/A"
                self.penghuni_treeview.insert("", tk.END, values=(i+1, penghuni['nim'], penghuni['nama_penghuni'], fakultas_str))
        else:
            if not self.penghuni_treeview.get_children(): self.penghuni_treeview.insert("", tk.END, values=("", "Belum ada penghuni.", "", ""))

        self.add_widget(self.penghuni_treeview)
        self.add_widget(self.treeview_scrollbar)
        self.canvas.create_window(table_x, table_y, anchor=tk.NW, window=self.penghuni_treeview, width=treeview_actual_width, height=treeview_display_height)
        self.canvas.create_window(table_x + treeview_actual_width, table_y, anchor=tk.NW, window=self.treeview_scrollbar, height=treeview_display_height)

        y_buttons = 15
        tbl(self.canvas, 50, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", lambda: self.screen_manager.show_kamar_list(self.asrama_id, self.asrama_nama))
        tbl(self.canvas,293, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "#F47B07", "Tambah Data", lambda: self.screen_manager.show_insert_data_form(self.kamar_id))
        tbl(self.canvas,600, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "#F47B07", "Ubah Data", lambda: self.screen_manager.show_update_data_form(self.kamar_id))
        tbl(self.canvas,880, y_buttons, 150, 50, 10, 10, 90, 180, 270, 360, "#F47B07", "Hapus Data", lambda: self.screen_manager.show_delete_data_form(self.kamar_id))
        
        y_pindah_button = table_y + treeview_display_height + 25 
        lebar_tombol_pindah = 200
        x_tombol_pindah = (self.app_instance.appwidth / 2) - (lebar_tombol_pindah / 2) 
        tbl(self.canvas, x_tombol_pindah , y_pindah_button, lebar_tombol_pindah, 50, 10,10, 90, 180, 270, 360, "blue", "Pindah Kamar", 
            lambda: self.screen_manager.show_pindah_kamar_form(self.kamar_id))


    def clear_screen_elements(self):
        super().clear_screen_elements()
        self.penghuni_treeview = None
        self.treeview_scrollbar = None