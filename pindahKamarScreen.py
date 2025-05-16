from baseScreen import BaseScreen
from tombol import tbl
from tkinter import *
from tkinter import messagebox,ttk
class PindahKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id_asal):
        super().__init__(screen_manager, db_service)
        self.kamar_id_asal = kamar_id_asal 
        self.asrama_id_asal = self.screen_manager.current_asrama_id_context
        self.asrama_nama_asal = self.screen_manager.current_asrama_nama_context

        self.selected_nim_var = StringVar()
        self.selected_asrama_tujuan_var = StringVar() 
        self.selected_kamar_tujuan_var = StringVar()

        self.penghuni_asal_options = []
        self.asrama_tujuan_options_map = {} 
        self.kamar_tujuan_options = []

    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth / 2, 50,
                                text=f"Pindah Kamar dari {self.asrama_nama_asal} - Kamar {self.kamar_id_asal}",
                                fill="#F4FEFF", font=("Cooper Black", 20, "bold"))

        y_current = 200
        label_width = 150
        dropdown_width_chars = 30 
        
        estimated_dropdown_pixel_width = dropdown_width_chars * 7 

        form_content_width = label_width + 10 + estimated_dropdown_pixel_width 
        x_label = (self.app_instance.appwidth - form_content_width) / 2
        x_dropdown = x_label + label_width + 10


        self.create_canvas_text(x_label, y_current + 10, text="Pilih Penghuni:", fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="w")
        opsi_penghuni_asal, _ = self.db_service.get_penghuni_in_kamar(self.kamar_id_asal, self.asrama_id_asal)
        self.penghuni_asal_options = opsi_penghuni_asal if not (opsi_penghuni_asal and opsi_penghuni_asal[0].startswith("Info:")) else ["Tidak ada penghuni"]
        
        penghuni_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.selected_nim_var,
                                                        values=self.penghuni_asal_options, width=dropdown_width_chars, state="readonly", font=("Arial", 14)))
        penghuni_dropdown.place(x=x_dropdown, y=y_current)
        if self.penghuni_asal_options and self.penghuni_asal_options[0] != "Tidak ada penghuni":
            self.selected_nim_var.set(self.penghuni_asal_options[0])
        y_current += 50

        self.create_canvas_text(x_label, y_current + 10, text="Asrama Tujuan:", fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="w")
        all_asrama_db = self.db_service.get_all_asrama()
        self.asrama_tujuan_options_map = {asrama['nama_asrama']: asrama['asrama_id'] for asrama in all_asrama_db}
        asrama_display_options = list(self.asrama_tujuan_options_map.keys())

        asrama_tujuan_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.selected_asrama_tujuan_var,
                                                            values=asrama_display_options, width=dropdown_width_chars, state="readonly", font=("Arial", 14)))
        asrama_tujuan_dropdown.place(x=x_dropdown, y=y_current)
        asrama_tujuan_dropdown.bind("<<ComboboxSelected>>", self._on_asrama_tujuan_selected)
        y_current += 50

        self.create_canvas_text(x_label, y_current + 10, text="Kamar Tujuan:", fill="#F4FEFF", font=("Arial", 12, "bold"), anchor="w")
        self.kamar_tujuan_dropdown = self.add_widget(ttk.Combobox(self.canvas, textvariable=self.selected_kamar_tujuan_var,
                                                                values=[], width=dropdown_width_chars, state="disabled", font=("Arial", 14)))
        self.kamar_tujuan_dropdown.place(x=x_dropdown, y=y_current)
        y_current += 100

        button_width = 200
        x_button_pindah = self.app_instance.appwidth / 2 - button_width - 10
        x_button_batal = self.app_instance.appwidth / 2 + 10

        tbl(self.canvas, x_button_pindah, y_current, button_width, 50, 10,10,90,180,270,360, "blue", "Pindahkan", self._proses_pindah_kamar)
        tbl(self.canvas, x_button_batal, y_current, button_width, 50, 10,10,90,180,270,360, "red", "Batal",
            lambda: self.screen_manager.show_kamar_detail(self.kamar_id_asal)) 

    def _on_asrama_tujuan_selected(self, event=None):
        selected_nama_asrama = self.selected_asrama_tujuan_var.get()
        asrama_id_tujuan = self.asrama_tujuan_options_map.get(selected_nama_asrama)
        
        if asrama_id_tujuan:
            kamars_in_asrama = self.db_service.get_all_kamar_in_asrama(asrama_id_tujuan)
            self.kamar_tujuan_options = [k['nomor_kamar'] for k in kamars_in_asrama]
            self.kamar_tujuan_dropdown['values'] = self.kamar_tujuan_options
            if self.kamar_tujuan_options:
                self.selected_kamar_tujuan_var.set(self.kamar_tujuan_options[0])
                self.kamar_tujuan_dropdown['state'] = "readonly"
            else:
                self.selected_kamar_tujuan_var.set("Tidak ada kamar")
                self.kamar_tujuan_dropdown['state'] = "disabled"
        else:
            self.kamar_tujuan_options = []
            self.kamar_tujuan_dropdown['values'] = []
            self.selected_kamar_tujuan_var.set("")
            self.kamar_tujuan_dropdown['state'] = "disabled"

    def _proses_pindah_kamar(self):
        nim_str_selection = self.selected_nim_var.get()
        if not nim_str_selection or nim_str_selection == "Tidak ada penghuni":
            messagebox.showwarning("Peringatan", "Pilih penghuni yang akan dipindahkan.")
            return
        
        nim_to_move = nim_str_selection.split(" - ")[0] 

        selected_nama_asrama_tujuan = self.selected_asrama_tujuan_var.get()
        asrama_id_tujuan = self.asrama_tujuan_options_map.get(selected_nama_asrama_tujuan)
        
        nomor_kamar_tujuan_str = self.selected_kamar_tujuan_var.get()

        if not asrama_id_tujuan or not nomor_kamar_tujuan_str or nomor_kamar_tujuan_str == "Tidak ada kamar":
            messagebox.showwarning("Peringatan", "Pilih asrama dan kamar tujuan.")
            return
        
        try:
            nomor_kamar_tujuan = int(nomor_kamar_tujuan_str)
        except ValueError:
            messagebox.showerror("Kesalahan", "Nomor kamar tujuan tidak valid.")
            return

        success, message = self.db_service.pindah_kamar_penghuni(nim_to_move, nomor_kamar_tujuan, asrama_id_tujuan)
        if success:
            self.screen_manager.show_kamar_detail(self.kamar_id_asal)