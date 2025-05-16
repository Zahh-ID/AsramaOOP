from baseScreen import BaseScreen
from mainMenuScreen import MainMenuScreen
from asramaSelectionScreen import AsramaSelectionScreen
from kamarListScreen import KamarListScreen
from kamarDetailScreen import KamarDetailScreen
from insertDataScreen import InsertDataScreen
from updateDataScreen import UpdateDataScreen
from deleteDataScreen import DeleteDataScreen
from pindahKamarScreen import PindahKamarScreen
from riwayatScreen import RiwayatAktivitasScreen
from tkinter import messagebox

class ScreenManager:
    def __init__(self, app, db_service):
        self.app = app 
        self.db_service = db_service
        self.current_screen_instance = None
        self.current_asrama_id_context = None
        self.current_asrama_nama_context = None

    def _display_screen(self, screen_class, *args):
        if self.current_screen_instance: self.current_screen_instance.clear_screen_elements()
        self.app._clear_canvas_for_new_screen()
        self.app._draw_background() 
        self.current_screen_instance = screen_class(self, self.db_service, *args)
        self.current_screen_instance.setup_ui() 

    def show_main_menu(self): self._display_screen(MainMenuScreen)
    def show_asrama_selection(self):
        self.current_asrama_id_context = None 
        self.current_asrama_nama_context = None
        self._display_screen(AsramaSelectionScreen)
    def show_kamar_list(self, asrama_id, asrama_nama):
        self.current_asrama_id_context = asrama_id
        self.current_asrama_nama_context = asrama_nama
        self._display_screen(KamarListScreen, asrama_id, asrama_nama)
    def show_kamar_detail(self, kamar_id): 
        if self.current_asrama_id_context is None:
            messagebox.showerror("Kesalahan Navigasi", "Konteks asrama tidak ditemukan.")
            self.show_asrama_selection()
            return
        self._display_screen(KamarDetailScreen, kamar_id)
    def show_insert_data_form(self, kamar_id): self._display_screen(InsertDataScreen, kamar_id)
    def show_update_data_form(self, kamar_id): self._display_screen(UpdateDataScreen, kamar_id)
    def show_delete_data_form(self, kamar_id): self._display_screen(DeleteDataScreen, kamar_id)
    def show_pindah_kamar_form(self, kamar_id_asal): 
        self._display_screen(PindahKamarScreen, kamar_id_asal)
    def show_riwayat_aktivitas(self): 
        self._display_screen(RiwayatAktivitasScreen)