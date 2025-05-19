from baseScreen import BaseScreen
from tombol import tbl
from tkinter import ttk
import tkinter as tk

class RiwayatAktivitasScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview = None
        self.log_scrollbar = None

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Riwayat.Treeview", background="#F0F0F0", fieldbackground="#FFFFFF", foreground="black", rowheight=25) 
        style.configure("Riwayat.Treeview.Heading", background="#BFBFBF", foreground="black", font=('Arial', 10, 'bold'), relief="flat")
        style.map("Riwayat.Treeview.Heading", background=[('active', '#A0A0A0')])

        self.create_canvas_text(self.app_instance.appwidth / 2, 50, text="Riwayat Perubahan Data", fill="#F4F0FF", font=("Cooper Black", 24, "bold"))

        table_padding_horizontal = 30
        table_padding_top = 90 
        table_padding_bottom = 70 
        table_x = table_padding_horizontal
        table_y = table_padding_top
        table_container_width = self.app_instance.appwidth - (2 * table_padding_horizontal)
        scrollbar_width = 20
        treeview_actual_width = table_container_width - scrollbar_width
        treeview_display_height = self.app_instance.appheight - table_y - table_padding_bottom - 20

        columns = ("log_id", "waktu", "aksi", "nim", "nama", "detail_kamar", "keterangan")
        self.log_treeview = ttk.Treeview(self.canvas, columns=columns, show='headings', style="Riwayat.Treeview")

        self.log_treeview.heading("log_id", text="ID")
        self.log_treeview.heading("waktu", text="Waktu")
        self.log_treeview.heading("aksi", text="Aksi")
        self.log_treeview.heading("nim", text="NIM")
        self.log_treeview.heading("nama", text="Nama Terkait")
        self.log_treeview.heading("detail_kamar", text="Detail Kamar")
        self.log_treeview.heading("keterangan", text="Keterangan")

        self.log_treeview.column("log_id", width=int(treeview_actual_width * 0.04), anchor=tk.CENTER, stretch=tk.NO)
        self.log_treeview.column("waktu", width=int(treeview_actual_width * 0.15), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("aksi", width=int(treeview_actual_width * 0.07), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("nim", width=int(treeview_actual_width * 0.12), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("nama", width=int(treeview_actual_width * 0.18), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("detail_kamar", width=int(treeview_actual_width * 0.22), anchor=tk.W, stretch=tk.YES)
        self.log_treeview.column("keterangan", width=int(treeview_actual_width * 0.22), anchor=tk.W, stretch=tk.YES)
        
        self.log_scrollbar = ttk.Scrollbar(self.canvas, orient="vertical", command=self.log_treeview.yview)
        self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)

        daftar_log = self.db_service.get_audit_log_penghuni(limit=200) 
        for item in self.log_treeview.get_children(): self.log_treeview.delete(item)
        if daftar_log:
            for log_entry in daftar_log:
                self.log_treeview.insert("", tk.END, values=(
                    log_entry['log_id'],
                    log_entry['waktu_aksi_formatted'],
                    log_entry['aksi'],
                    log_entry['nim'],
                    log_entry['nama_terkait'],
                    log_entry['detail_perubahan'],
                    log_entry['keterangan_tambahan']
                ))
        else:
            self.log_treeview.insert("", tk.END, values=("", "Belum ada riwayat aktivitas.", "", "", "", "", ""))

        self.add_widget(self.log_treeview)
        self.add_widget(self.log_scrollbar)
        
        self.canvas.create_window(table_x, table_y, anchor=tk.NW,
                                  window=self.log_treeview,
                                  width=treeview_actual_width, height=treeview_display_height)
        self.canvas.create_window(table_x + treeview_actual_width, table_y, anchor=tk.NW,
                                  window=self.log_scrollbar,
                                  height=treeview_display_height)

        y_button_kembali = self.app_instance.appheight - 50
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali",
            self.screen_manager.show_main_menu)

    def clear_screen_elements(self):
        super().clear_screen_elements()
        self.log_treeview = None
        self.log_scrollbar = None