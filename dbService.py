import mysql.connector
from tkinter import messagebox
class DatabaseService:
    """
    Mengenkapsulasi semua interaksi dengan database MySQL.
    Menyediakan metode untuk operasi CRUD pada entitas Asrama, Kamar, dan Penghuni.
    Menggunakan View dan Stored Procedure.
    Otomatis mencoba membuat skema database jika belum ada.
    """
    def __init__(self, host, user, password, database_name):
        self.host = host
        self.user = user
        self.password = password
        self.database_name = database_name
        self.conn = None
        self.cursor = None
        self._connect()
        if self.conn:
            self._initialize_database_schema() # Membuat semua objek DB
            self._populate_initial_master_data_if_empty() # Mengisi data master awal jika perlu

    def _connect(self):
        """Membuat koneksi ke database MySQL."""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
                # Database akan dipilih setelah dibuat jika belum ada
            )
            self.cursor = self.conn.cursor(dictionary=True)
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name}")
            self.cursor.execute(f"USE {self.database_name}")
            print(f"Berhasil terhubung ke database MySQL dan menggunakan database '{self.database_name}'.")
        except mysql.connector.Error as err:
            print(f"Kesalahan koneksi database MySQL: {err}")
            messagebox.showerror("Kesalahan Database", f"Tidak dapat terhubung ke MySQL: {err}\n\nPastikan server MySQL berjalan dan detail koneksi benar.")
            self.conn = None
            self.cursor = None

    def _close(self):
        """Menutup koneksi database."""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("Koneksi MySQL ditutup.")

    def _execute_single_ddl(self, ddl_statement):
        """Mengeksekusi satu pernyataan DDL."""
        try:
            self.cursor.execute(ddl_statement)
            self.conn.commit() # Commit setelah setiap DDL berhasil
        except mysql.connector.Error as err:
            # Beberapa error DDL mungkin karena objek sudah ada dengan cara yang berbeda,
            # atau masalah hak akses.
            print(f"Peringatan saat menjalankan DDL: {err}\nDDL: {ddl_statement[:200]}...") # Print sebagian DDL untuk debug
            # Tidak menampilkan messagebox untuk setiap DDL agar tidak terlalu banyak popup saat inisialisasi.
            # Jika ada error kritis, koneksi awal biasanya sudah gagal.
            # self.conn.rollback() # Tidak perlu rollback untuk DDL biasanya

    def _initialize_database_schema(self):
        """Membuat semua tabel, view, trigger, dan stored procedure jika belum ada."""
        if not self.conn or not self.conn.is_connected():
            print("Inisialisasi skema dibatalkan: Tidak ada koneksi database.")
            return

        print("Memulai inisialisasi skema database...")

        # 1. Buat Tabel Utama
        tables_ddl = [
            """CREATE TABLE IF NOT EXISTS Asrama (
                asrama_id INTEGER PRIMARY KEY,
                nama_asrama VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Fakultas (
                fakultas_id INT AUTO_INCREMENT PRIMARY KEY,
                nama_fakultas VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Kamar (
                kamar_id_internal INTEGER PRIMARY KEY AUTO_INCREMENT,
                nomor_kamar INTEGER NOT NULL,
                asrama_id INTEGER NOT NULL,
                kapasitas INTEGER NOT NULL DEFAULT 2,
                FOREIGN KEY (asrama_id) REFERENCES Asrama(asrama_id) ON DELETE CASCADE,
                UNIQUE (nomor_kamar, asrama_id)
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS Penghuni (
                nim VARCHAR(50) PRIMARY KEY, nama_penghuni VARCHAR(255) NOT NULL,
                fakultas_id INT NULL DEFAULT NULL, kamar_id_internal INTEGER NOT NULL,
                FOREIGN KEY (kamar_id_internal) REFERENCES Kamar(kamar_id_internal) ON DELETE CASCADE,
                FOREIGN KEY (fakultas_id) REFERENCES Fakultas(fakultas_id) ON DELETE SET NULL ON UPDATE CASCADE
            ) ENGINE=InnoDB;""",
            """CREATE TABLE IF NOT EXISTS AuditLogAktivitasPenghuni (
                log_id INT AUTO_INCREMENT PRIMARY KEY, nim VARCHAR(50),
                nama_penghuni_lama VARCHAR(255) DEFAULT NULL, nama_penghuni_baru VARCHAR(255) DEFAULT NULL,
                fakultas_lama VARCHAR(255) DEFAULT NULL, fakultas_baru VARCHAR(255) DEFAULT NULL,
                kamar_id_internal_lama INT DEFAULT NULL, kamar_id_internal_baru INT DEFAULT NULL,
                nomor_kamar_lama INT DEFAULT NULL, nama_asrama_lama VARCHAR(255) DEFAULT NULL,
                nomor_kamar_baru INT DEFAULT NULL, nama_asrama_baru VARCHAR(255) DEFAULT NULL,
                aksi VARCHAR(10) NOT NULL, waktu_aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                keterangan_tambahan TEXT DEFAULT NULL
            ) ENGINE=InnoDB;"""
        ]
        for ddl in tables_ddl:
            self._execute_single_ddl(ddl)
        print("Tabel utama telah diperiksa/dibuat.")

        # 2. Buat Views
        views_ddl = [
            """CREATE OR REPLACE VIEW vw_DetailKamarPenghuni AS
            SELECT
                K.nomor_kamar, A.nama_asrama, K.asrama_id, K.kapasitas,
                (SELECT COUNT(*) FROM Penghuni P WHERE P.kamar_id_internal = K.kamar_id_internal) AS jumlah_penghuni_sekarang,
                K.kamar_id_internal
            FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id;""",
            """CREATE OR REPLACE VIEW vw_DaftarPenghuniLengkap AS
            SELECT
                P.nim, P.nama_penghuni, F.nama_fakultas AS fakultas, 
                K.nomor_kamar, A.nama_asrama, K.asrama_id AS id_asrama_penghuni,
                A.asrama_id AS id_asrama_kamar, K.kamar_id_internal, P.fakultas_id
            FROM Penghuni P
            JOIN Kamar K ON P.kamar_id_internal = K.kamar_id_internal
            JOIN Asrama A ON K.asrama_id = A.asrama_id
            LEFT JOIN Fakultas F ON P.fakultas_id = F.fakultas_id;"""
        ]
        for ddl in views_ddl:
            self._execute_single_ddl(ddl)
        print("View telah diperiksa/dibuat.")

        # 3. Buat Triggers
        # Pastikan DELIMITER tidak ada di string Python
        trigger_insert_ddl = """
        CREATE TRIGGER IF NOT EXISTS trg_LogInsertPenghuni
        AFTER INSERT ON Penghuni
        FOR EACH ROW
        BEGIN
            DECLARE v_nomor_kamar INT;
            DECLARE v_nama_asrama VARCHAR(255);
            DECLARE v_nama_fakultas VARCHAR(255) DEFAULT NULL;

            SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar, v_nama_asrama
            FROM Kamar K
            JOIN Asrama A ON K.asrama_id = A.asrama_id
            WHERE K.kamar_id_internal = NEW.kamar_id_internal;

            IF NEW.fakultas_id IS NOT NULL THEN
                SELECT nama_fakultas INTO v_nama_fakultas FROM Fakultas WHERE fakultas_id = NEW.fakultas_id;
            END IF;

            INSERT INTO AuditLogAktivitasPenghuni (
                nim, nama_penghuni_baru, fakultas_baru,
                kamar_id_internal_baru, nomor_kamar_baru, nama_asrama_baru,
                aksi, keterangan_tambahan
            )
            VALUES (
                NEW.nim, NEW.nama_penghuni, v_nama_fakultas,
                NEW.kamar_id_internal, v_nomor_kamar, v_nama_asrama,
                'INSERT', CONCAT('Penghuni baru ditambahkan ke kamar ', v_nomor_kamar, ' Asrama ', v_nama_asrama)
            );
        END""" # Hapus $$ dan DELIMITER ; dari sini
        
        trigger_update_ddl = """
        CREATE TRIGGER IF NOT EXISTS trg_LogUpdatePenghuni
        AFTER UPDATE ON Penghuni
        FOR EACH ROW
        BEGIN
            DECLARE v_nomor_kamar_lama INT DEFAULT NULL; DECLARE v_nama_asrama_lama VARCHAR(255) DEFAULT NULL;
            DECLARE v_nama_fakultas_lama VARCHAR(255) DEFAULT NULL; DECLARE v_nomor_kamar_baru INT DEFAULT NULL;
            DECLARE v_nama_asrama_baru VARCHAR(255) DEFAULT NULL; DECLARE v_nama_fakultas_baru VARCHAR(255) DEFAULT NULL;
            DECLARE v_keterangan TEXT DEFAULT 'Data penghuni diubah.';

            IF OLD.kamar_id_internal IS NOT NULL THEN
                SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar_lama, v_nama_asrama_lama
                FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = OLD.kamar_id_internal;
            END IF;
            IF OLD.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nama_fakultas_lama FROM Fakultas WHERE fakultas_id = OLD.fakultas_id; END IF;
            IF NEW.kamar_id_internal IS NOT NULL THEN
                SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar_baru, v_nama_asrama_baru
                FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = NEW.kamar_id_internal;
            END IF;
            IF NEW.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nama_fakultas_baru FROM Fakultas WHERE fakultas_id = NEW.fakultas_id; END IF;

            IF OLD.kamar_id_internal != NEW.kamar_id_internal THEN
                SET v_keterangan = CONCAT('Penghuni pindah dari kamar ', IFNULL(v_nomor_kamar_lama, 'N/A'), ' Asrama ', IFNULL(v_nama_asrama_lama, 'N/A'), 
                                        ' ke kamar ', IFNULL(v_nomor_kamar_baru, 'N/A'), ' Asrama ', IFNULL(v_nama_asrama_baru, 'N/A'), '.');
            ELSEIF OLD.fakultas_id != NEW.fakultas_id OR (OLD.fakultas_id IS NULL AND NEW.fakultas_id IS NOT NULL) OR (OLD.fakultas_id IS NOT NULL AND NEW.fakultas_id IS NULL) THEN
                SET v_keterangan = CONCAT('Fakultas diubah dari ', IFNULL(v_nama_fakultas_lama, 'N/A'), ' menjadi ', IFNULL(v_nama_fakultas_baru, 'N/A'), '.');
            ELSEIF OLD.nama_penghuni != NEW.nama_penghuni THEN SET v_keterangan = CONCAT('Nama diubah dari ', OLD.nama_penghuni, ' menjadi ', NEW.nama_penghuni, '.');
            END IF;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_lama, nama_penghuni_baru, fakultas_lama, fakultas_baru, kamar_id_internal_lama, kamar_id_internal_baru, nomor_kamar_lama, nama_asrama_lama, nomor_kamar_baru, nama_asrama_baru, aksi, keterangan_tambahan)
            VALUES (OLD.nim, OLD.nama_penghuni, NEW.nama_penghuni, v_nama_fakultas_lama, v_nama_fakultas_baru, OLD.kamar_id_internal, NEW.kamar_id_internal, v_nomor_kamar_lama, v_nama_asrama_lama, v_nomor_kamar_baru, v_nama_asrama_baru, 'UPDATE', v_keterangan);
        END"""
        
        trigger_delete_ddl = """
        CREATE TRIGGER IF NOT EXISTS trg_LogDeletePenghuni
        AFTER DELETE ON Penghuni
        FOR EACH ROW
        BEGIN
            DECLARE v_nomor_kamar INT DEFAULT NULL; DECLARE v_nama_asrama VARCHAR(255) DEFAULT NULL; DECLARE v_nama_fakultas VARCHAR(255) DEFAULT NULL;
            IF OLD.kamar_id_internal IS NOT NULL THEN
                SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar, v_nama_asrama
                FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = OLD.kamar_id_internal;
            END IF;
            IF OLD.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nama_fakultas FROM Fakultas WHERE fakultas_id = OLD.fakultas_id; END IF;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_lama, fakultas_lama, kamar_id_internal_lama, nomor_kamar_lama, nama_asrama_lama, aksi, keterangan_tambahan)
            VALUES (OLD.nim, OLD.nama_penghuni, v_nama_fakultas, OLD.kamar_id_internal, v_nomor_kamar, v_nama_asrama, 'DELETE', CONCAT('Penghuni dihapus dari kamar ', IFNULL(v_nomor_kamar, 'N/A'), ' Asrama ', IFNULL(v_nama_asrama, 'N/A')));
        END"""
        
        # Hapus trigger lama sebelum membuat yang baru untuk menghindari error jika sudah ada
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogInsertPenghuni")
        self._execute_single_ddl(trigger_insert_ddl)
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogUpdatePenghuni")
        self._execute_single_ddl(trigger_update_ddl)
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogDeletePenghuni")
        self._execute_single_ddl(trigger_delete_ddl)
        print("Trigger telah diperiksa/dibuat.")

        # 4. Buat Stored Procedures
        sp_tambah_penghuni_ddl = """
        CREATE PROCEDURE IF NOT EXISTS sp_TambahPenghuni (
            IN p_nim VARCHAR(50), IN p_nama_penghuni VARCHAR(255), IN p_nama_fakultas_input VARCHAR(255), 
            IN p_nomor_kamar INT, IN p_asrama_id INT, OUT p_status_code INT, OUT p_status_message VARCHAR(255)
        )
        BEGIN
            DECLARE v_kamar_id_internal INT; DECLARE v_kapasitas_kamar INT; DECLARE v_jumlah_penghuni_saat_ini INT;
            DECLARE v_fakultas_id INT DEFAULT NULL;
            SET p_status_code = 4; SET p_status_message = 'Terjadi kesalahan tidak diketahui.';
            IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN
                SET p_status_code = 5; SET p_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
            ELSE
                IF p_nama_fakultas_input IS NOT NULL AND p_nama_fakultas_input != '' THEN
                    SELECT fakultas_id INTO v_fakultas_id FROM Fakultas WHERE nama_fakultas = p_nama_fakultas_input;
                    IF v_fakultas_id IS NULL THEN INSERT INTO Fakultas (nama_fakultas) VALUES (p_nama_fakultas_input); SET v_fakultas_id = LAST_INSERT_ID(); END IF;
                END IF;
                SELECT kamar_id_internal INTO v_kamar_id_internal FROM Kamar WHERE nomor_kamar = p_nomor_kamar AND asrama_id = p_asrama_id;
                IF v_kamar_id_internal IS NULL THEN SET p_status_code = 1; SET p_status_message = 'Gagal: Kamar tidak ditemukan.';
                ELSE
                    SELECT kapasitas INTO v_kapasitas_kamar FROM Kamar WHERE kamar_id_internal = v_kamar_id_internal;
                    SELECT COUNT(*) INTO v_jumlah_penghuni_saat_ini FROM Penghuni WHERE kamar_id_internal = v_kamar_id_internal;
                    IF v_jumlah_penghuni_saat_ini >= v_kapasitas_kamar THEN SET p_status_code = 2; SET p_status_message = 'Gagal: Kamar sudah penuh.';
                    ELSE
                        IF EXISTS (SELECT 1 FROM Penghuni WHERE nim = p_nim) THEN SET p_status_code = 3; SET p_status_message = CONCAT('Gagal: NIM ', p_nim, ' sudah terdaftar.');
                        ELSE INSERT INTO Penghuni (nim, nama_penghuni, fakultas_id, kamar_id_internal) VALUES (p_nim, p_nama_penghuni, v_fakultas_id, v_kamar_id_internal); SET p_status_code = 0; SET p_status_message = 'Sukses: Penghuni berhasil ditambahkan.';
                        END IF;
                    END IF;
                END IF;
            END IF;
        END""" # Tanpa SELECT OUT di sini, akan diambil via argumen list

        sp_pindah_kamar_ddl = """
        CREATE PROCEDURE IF NOT EXISTS sp_PindahKamarPenghuni (
            IN p_nim VARCHAR(50), IN p_nomor_kamar_baru INT, IN p_asrama_id_baru INT,
            OUT p_status_code INT, OUT p_status_message VARCHAR(255)
        )
        BEGIN
            DECLARE v_k_id_lama INT; DECLARE v_k_id_baru INT; DECLARE v_kap_k_baru INT; DECLARE v_jml_p_k_baru INT;
            DECLARE v_p_exists INT DEFAULT 0;
            SET p_status_code = 4; SET p_status_message = 'Terjadi kesalahan tidak diketahui.';
            IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN SET p_status_code = 5; SET p_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
            ELSE
                SELECT COUNT(*), kamar_id_internal INTO v_p_exists, v_k_id_lama FROM Penghuni WHERE nim = p_nim;
                IF v_p_exists = 0 THEN SET p_status_code = 1; SET p_status_message = 'Gagal: Penghuni dengan NIM tersebut tidak ditemukan.';
                ELSE
                    SELECT kamar_id_internal INTO v_k_id_baru FROM Kamar WHERE nomor_kamar = p_nomor_kamar_baru AND asrama_id = p_asrama_id_baru;
                    IF v_k_id_baru IS NULL THEN SET p_status_code = 2; SET p_status_message = 'Gagal: Kamar tujuan tidak ditemukan.';
                    ELSE
                        IF v_k_id_lama = v_k_id_baru THEN SET p_status_code = 0; SET p_status_message = 'Info: Penghuni sudah berada di kamar tujuan.';
                        ELSE
                            SELECT kapasitas INTO v_kap_k_baru FROM Kamar WHERE kamar_id_internal = v_k_id_baru;
                            SELECT COUNT(*) INTO v_jml_p_k_baru FROM Penghuni WHERE kamar_id_internal = v_k_id_baru;
                            IF v_jml_p_k_baru >= v_kap_k_baru THEN SET p_status_code = 3; SET p_status_message = 'Gagal: Kamar tujuan sudah penuh.';
                            ELSE UPDATE Penghuni SET kamar_id_internal = v_k_id_baru WHERE nim = p_nim; SET p_status_code = 0; SET p_status_message = 'Sukses: Penghuni berhasil dipindahkan.';
                            END IF;
                        END IF;
                    END IF;
                END IF;
            END IF;
        END""" # Tanpa SELECT OUT di sini
        
        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_TambahPenghuni")
        self._execute_single_ddl(sp_tambah_penghuni_ddl)
        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_PindahKamarPenghuni")
        self._execute_single_ddl(sp_pindah_kamar_ddl)
        print("Stored Procedures telah diperiksa/dibuat.")

        print("Inisialisasi skema database selesai.")

    def _populate_initial_master_data_if_empty(self):
        """Mengisi data master awal untuk Asrama dan Fakultas jika tabel kosong."""
        if not self.conn or not self.conn.is_connected(): return

        try:
            # Populate Asrama
            self.cursor.execute("SELECT COUNT(*) as count FROM Asrama")
            if (self.cursor.fetchone() or {}).get('count', 0) == 0:
                asramas_data = [
                    (1, "Aster"), (2, "Soka"), (3, "Tulip"), (4, "Edelweiss"),
                    (5, "Lily"), (6, "Dahlia"), (7, "Melati"), (8, "Anyelir")
                ]
                for asrama_id_val, nama in asramas_data:
                    self._execute_query("INSERT INTO Asrama (asrama_id, nama_asrama) VALUES (%s, %s)", (asrama_id_val, nama), is_ddl_or_commit_managed_elsewhere=True)
                self.conn.commit()
                print("Data awal Asrama dimasukkan.")

            # Populate Fakultas
            self.cursor.execute("SELECT COUNT(*) as count FROM Fakultas")
            if (self.cursor.fetchone() or {}).get('count', 0) == 0:
                fakultas_data = [
                    ('Teknik'), ('Ekonomi dan Bisnis'), ('Ilmu Sosial dan Ilmu Politik'),
                    ('Kedokteran'), ('Ilmu Budaya'), ('MIPA'), ('Ilmu Komputer'),
                    ('Ilmu Keolahragaan'), ('Vokasi'), ('Ilmu Pendidikan')
                ]
                for nama_fak in fakultas_data:
                    self._execute_query("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fak,), is_ddl_or_commit_managed_elsewhere=True)
                self.conn.commit()
                print("Data awal Fakultas dimasukkan.")
            
            # Populate Kamar (Contoh, bisa diperluas)
            self.cursor.execute("SELECT COUNT(*) as count FROM Kamar")
            if (self.cursor.fetchone() or {}).get('count', 0) == 0:
                # Kamar untuk Asrama Aster (asrama_id = 1)
                kamar_data_aster = [
                    (101, 1, 2), (102, 1, 2), (103, 1, 3), 
                    (201, 1, 2), (202, 1, 2), (203, 1, 2),
                    (301, 1, 2), (302, 1, 2), (303, 1, 2)
                ]
                for nk, aid, kap in kamar_data_aster:
                     self._execute_query("INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES (%s, %s, %s)", (nk, aid, kap), is_ddl_or_commit_managed_elsewhere=True)
                self.conn.commit()
                print("Data awal Kamar untuk Aster dimasukkan.")


        except mysql.connector.Error as e:
            print(f"Kesalahan saat mengisi data master awal: {e}")
            # self.conn.rollback() # Rollback jika ada error selama populasi

    # ... (sisa metode DatabaseService seperti add_penghuni, pindah_kamar_penghuni, dll. tetap sama) ...
    # Metode add_penghuni dan pindah_kamar_penghuni akan menggunakan
    # pendekatan modifikasi list argumen untuk OUT params.

    def add_penghuni(self, nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val):
        """Menambahkan penghuni baru menggunakan Stored Procedure sp_TambahPenghuni."""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return False
        try:
            proc_args_list = [nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val, 0, ""] 
            
            # Panggil SP. Konektor akan mencoba mengisi nilai OUT ke proc_args_list
            self.cursor.callproc('sp_TambahPenghuni', proc_args_list)
            
            # Ambil nilai OUT dari list yang sama
            status_code = proc_args_list[5] 
            status_message = proc_args_list[6]

            if status_code is not None: 
                if status_code == 0: 
                    messagebox.showinfo("Sukses", status_message)
                    self.conn.commit() 
                    return True
                else:
                    messagebox.showerror("Gagal Menambah Penghuni", status_message)
                    return False
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari Stored Procedure Tambah Penghuni (OUT params tidak terisi dengan benar).")
                return False
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_TambahPenghuni: {err}")
            try:
                if self.conn.in_transaction: self.conn.rollback()
            except: pass
            return False

    def pindah_kamar_penghuni(self, nim, nomor_kamar_baru, asrama_id_baru):
        """Memindahkan penghuni ke kamar lain menggunakan Stored Procedure sp_PindahKamarPenghuni."""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return False, "Tidak ada koneksi database."
        try:
            proc_args_list = [nim, nomor_kamar_baru, asrama_id_baru, 0, ""] 

            self.cursor.callproc('sp_PindahKamarPenghuni', proc_args_list)
            status_code = proc_args_list[3]
            status_message = proc_args_list[4]

            if status_code is not None: 
                if status_code == 0: 
                    if status_message and "Info:" in status_message: 
                        messagebox.showinfo("Info Pindah Kamar", status_message)
                    else:
                        messagebox.showinfo("Sukses Pindah Kamar", status_message if status_message else "Operasi berhasil.")
                    self.conn.commit()
                    return True, status_message
                else:
                    messagebox.showerror("Gagal Pindah Kamar", status_message)
                    return False, status_message
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari Stored Procedure Pindah Kamar (OUT params tidak terisi dengan benar).")
                return False, "Gagal mengambil status SP."
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_PindahKamarPenghuni: {err}")
            try:
                if self.conn.in_transaction: self.conn.rollback()
            except: pass
            return False, str(err)


    def update_penghuni(self, nim_original, nim_baru, nama_baru, nama_fakultas_baru):
        """Memperbarui data penghuni (Trigger akan mencatat log)."""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return "ERROR_CONNECTION" 

        check_exists_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
        self.cursor.execute(check_exists_query, (nim_original,))
        if not self.cursor.fetchone():
            messagebox.showwarning("Perhatian", f"Tidak ada data penghuni yang cocok dengan NIM original: {nim_original}.")
            return "ERROR_NIM_ORIGINAL_NOT_FOUND"

        updates = []
        params = []
        
        if nim_baru and nim_original != nim_baru:
            if not nim_baru.isdigit(): 
                messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.")
                return "ERROR_INVALID_NIM_FORMAT"
            check_nim_conflict_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
            self.cursor.execute(check_nim_conflict_query, (nim_baru,))
            if self.cursor.fetchone():
                messagebox.showerror("Kesalahan", f"NIM baru '{nim_baru}' sudah digunakan oleh penghuni lain.")
                return "ERROR_NIM_CONFLICT"
            updates.append("nim = %s")
            params.append(nim_baru)
        
        if nama_baru: 
            updates.append("nama_penghuni = %s")
            params.append(nama_baru)

        fakultas_id_to_update = None 
        if nama_fakultas_baru is not None: 
            if nama_fakultas_baru == "": 
                 fakultas_id_to_update = None 
                 updates.append("fakultas_id = %s") 
                 params.append(fakultas_id_to_update)
            else:
                fakultas_id_to_update = self.get_fakultas_id_by_name(nama_fakultas_baru)
                if fakultas_id_to_update is None: 
                    try: 
                        self.cursor.execute("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fakultas_baru,))
                        fakultas_id_to_update = self.cursor.lastrowid 
                        if fakultas_id_to_update: 
                            self.conn.commit() 
                            print(f"Fakultas baru '{nama_fakultas_baru}' ditambahkan dengan ID: {fakultas_id_to_update}")
                        else: 
                            messagebox.showerror("Kesalahan", f"Gagal menambahkan fakultas baru '{nama_fakultas_baru}'.")
                            return "ERROR_ADD_FAKULTAS"
                    except mysql.connector.Error as e_fak:
                        messagebox.showerror("Kesalahan Database", f"Gagal menambahkan fakultas baru: {e_fak}")
                        return "ERROR_ADD_FAKULTAS_DB"
                updates.append("fakultas_id = %s")
                params.append(fakultas_id_to_update)
        
        if not updates:
            messagebox.showinfo("Info", "Tidak ada data yang akan diubah (semua input kosong atau sama dengan data lama).")
            return "SUCCESS_NO_CHANGE" 

        params_for_update = list(params) 
        params_for_update.append(nim_original)
        query = f"UPDATE Penghuni SET {', '.join(updates)} WHERE nim = %s"

        success = self._execute_query(query, tuple(params_for_update), is_ddl_or_commit_managed_elsewhere=False)
        
        if success:
            if self.cursor.rowcount > 0:
                messagebox.showinfo("Sukses", "Data penghuni berhasil diubah.")
                return "SUCCESS_DATA_CHANGED" 
            else:
                messagebox.showwarning("Perhatian", "Tidak ada perubahan aktual pada data (data baru mungkin sama dengan data lama).")
                return "SUCCESS_NO_ACTUAL_CHANGE" 
        else:
            return "ERROR_UPDATE_FAILED"


    def delete_penghuni(self, nim):
        success = self._execute_query("DELETE FROM Penghuni WHERE nim = %s", (nim,), is_ddl_or_commit_managed_elsewhere=False)
        if success and self.cursor.rowcount > 0:
            messagebox.showinfo("Sukses", f"Data penghuni dengan NIM {nim} berhasil dihapus.")
            return True
        elif success and self.cursor.rowcount == 0:
            messagebox.showwarning("Gagal", f"Penghuni dengan NIM {nim} tidak ditemukan.")
            return False
        return False

    def get_audit_log_penghuni(self, limit=100): 
        query = """
            SELECT 
                log_id, DATE_FORMAT(waktu_aksi, '%Y-%m-%d %H:%i:%S') AS waktu_aksi_formatted, aksi, nim, 
                IFNULL(nama_penghuni_baru, nama_penghuni_lama) AS nama_terkait,
                IF(aksi = 'INSERT', 
                   CONCAT('Ke: ', IFNULL(nomor_kamar_baru, 'N/A'), ' (', IFNULL(nama_asrama_baru, 'N/A'), ') - Fak: ', IFNULL(fakultas_baru, 'N/A')),
                   IF(aksi = 'DELETE',
                      CONCAT('Dari: ', IFNULL(nomor_kamar_lama, 'N/A'), ' (', IFNULL(nama_asrama_lama, 'N/A'), ') - Fak: ', IFNULL(fakultas_lama, 'N/A')),
                      CONCAT('Dari: ', IFNULL(nomor_kamar_lama, 'N/A'), ' (', IFNULL(nama_asrama_lama, 'N/A'), ') Fak: ', IFNULL(fakultas_lama, 'N/A'),
                             ' Ke: ', IFNULL(nomor_kamar_baru, 'N/A'), ' (', IFNULL(nama_asrama_baru, 'N/A'), ') Fak: ', IFNULL(fakultas_baru, 'N/A'))
                   )
                ) AS detail_perubahan,
                keterangan_tambahan
            FROM AuditLogAktivitasPenghuni 
            ORDER BY waktu_aksi DESC 
            LIMIT %s
        """ 
        return self._execute_query(query, (limit,), fetch_all=True) or []

    def __del__(self):
        self._close()