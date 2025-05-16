from baseScreen import BaseScreen
from tombol import tbl

class AsramaSelectionScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(540, 360, text="PILIH ASRAMA", fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        asramas_data = self.db_service.get_all_asrama()
        positions = [
            (50, 100), (420, 100), (780, 100), (50, 290),
            (50, 500), (780, 290), (420, 500), (780, 500)
        ]
        if not asramas_data:
            self.create_canvas_text(540, 250, text="Tidak ada data asrama ditemukan.", fill="red", font=("Arial", 16))
        for i, asrama_row in enumerate(asramas_data):
            if i < len(positions):
                x_pos, y_pos = positions[i]
                nama_asrama = asrama_row['nama_asrama']
                asrama_id = asrama_row['asrama_id']
                tbl(self.canvas, x_pos, y_pos, 250, 120, 20, 20, 90, 180, 270, 360, "#F47B07",
                    nama_asrama,
                    lambda aid=asrama_id, aname=nama_asrama: self.screen_manager.show_kamar_list(aid, aname))
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali",
            self.screen_manager.show_main_menu)