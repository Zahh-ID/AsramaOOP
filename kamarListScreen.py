from baseScreen import BaseScreen
from tombol import tbl

class KamarListScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, asrama_id, asrama_nama):
        super().__init__(screen_manager, db_service)
        self.asrama_id = asrama_id
        self.asrama_nama = asrama_nama
    def setup_ui(self):
        self.create_canvas_text(540, 50, text=f"Asrama {self.asrama_nama}", fill="#F4FEFF", font=("Cooper Black", 24, "bold"))
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali",
            self.screen_manager.show_asrama_selection)
        kamars_layout = [
            ("Kamar 101", 101, 50, 100), ("Kamar 102", 102, 420, 100), ("Kamar 103", 103, 780, 100),
            ("Kamar 201", 201, 50, 300), ("Kamar 202", 202, 420, 300), ("Kamar 203", 203, 780, 300),
            ("Kamar 301", 301, 50, 500), ("Kamar 302", 302, 420, 500), ("Kamar 303", 303, 780, 500),
        ]
        for nama_kamar, id_kamar, x, y in kamars_layout:
            tbl(self.canvas, x, y, 250, 120, 20, 20, 90, 180, 270, 360, "#F47B07",
                nama_kamar,
                lambda kid=id_kamar: self.screen_manager.show_kamar_detail(kid))