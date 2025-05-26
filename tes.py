import tkinter as tk
from tkinter import ttk, Canvas, NW, PhotoImage, StringVar, Entry
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk, ImageFilter
import mysql.connector # Import MySQL connector
import os 
import re # Untuk validasi regex NIM

# Diasumsikan file tombol.py ada di direktori yang sama
from tombol import tbl

# --- Kelas Utama 1: DatabaseService (Enkapsulasi Logika Database dengan MySQL) ---
class DatabaseService:
    """
    Mengenkapsulasi semua interaksi dengan database MySQL.
    Menyediakan metode untuk operasi CRUD pada entitas Asrama, Kamar, dan Penghuni.
    Menggunakan View dan Stored Procedure.
    Otomatis mencoba membuat skema database jika belum ada.
    """
    def __init__(self, host, user, password, database_name):
        self._host = host
        self._user = user
        self._password = password
        self._database_name = database_name
        self._conn = None 
        self._cursor = None 
        self._connect()
        if self._conn: 
            self._initialize_database_schema() # Membuat semua objek DB
            self._populate_initial_master_data_if_empty() 

    def _connect(self):
        """Membuat koneksi ke database MySQL."""
        try:
            # Koneksi awal tanpa menentukan database, untuk bisa CREATE DATABASE IF NOT EXISTS
            self._conn = mysql.connector.connect(
                host=self._host, 
                user=self._user, 
                password=self._password 
            )
            self._cursor = self._conn.cursor(dictionary=True) 
            self._cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self._database_name}") 
            self._cursor.execute(f"USE {self._database_name}") 
            # Re-assign koneksi untuk memastikan database yang benar digunakan untuk operasi selanjutnya
            self._conn.database = self._database_name
            print(f"Berhasil terhubung ke database MySQL dan menggunakan database '{self._database_name}'.")
        except mysql.connector.Error as err:
            print(f"Kesalahan koneksi database MySQL: {err}")
            messagebox.showerror("Kesalahan Database", f"Tidak dapat terhubung ke MySQL: {err}\n\nPastikan server MySQL berjalan dan detail koneksi benar.")
            self._conn = None
            self._cursor = None

    def _close(self):
        """Menutup koneksi database."""
        if self._cursor: 
            self._cursor.close()
        if self._conn and self._conn.is_connected(): 
            self._conn.close()
            print("Koneksi MySQL ditutup.")

    def _execute_single_ddl(self, ddl_statement):
        """Mengeksekusi satu pernyataan DDL dan melakukan commit."""
        if not self._conn or not self._conn.is_connected():
            print(f"Eksekusi DDL dibatalkan, tidak ada koneksi: {ddl_statement[:50]}...")
            return False
        try:
            # Untuk trigger dan procedure yang mungkin mengandung banyak statement,
            # kita eksekusi sebagai satu blok.
            # MySQL connector menangani DELIMITER secara berbeda dari klien CLI.
            # Kita kirim seluruh blok CREATE PROCEDURE/TRIGGER sebagai satu string.
            if ddl_statement.strip().upper().startswith(("CREATE TRIGGER", "CREATE PROCEDURE")):
                # Pisahkan DROP IF EXISTS jika ada
                if ddl_statement.strip().upper().startswith("DROP"):
                    parts = ddl_statement.split("$$") # Asumsi $$ digunakan sebagai delimiter di string DDL
                    if len(parts) > 1: # Ada DROP dan CREATE
                        self._cursor.execute(parts[0].strip()) # Eksekusi DROP
                        self._cursor.execute(parts[1].strip()) # Eksekusi CREATE
                    else: # Hanya DROP atau hanya CREATE
                         self._cursor.execute(ddl_statement)
                else: # Hanya CREATE
                    self._cursor.execute(ddl_statement)
            else: # Untuk CREATE TABLE, CREATE VIEW
                self._cursor.execute(ddl_statement)
            
            self._conn.commit()
            # print(f"DDL berhasil dijalankan: {ddl_statement[:60]}...")
            return True
        except mysql.connector.Error as err:
            print(f"Peringatan/Error saat menjalankan DDL: {err}\nDDL: {ddl_statement[:200]}...")
            try:
                if self._conn.in_transaction: self._conn.rollback()
            except: pass
            return False

    def _initialize_database_schema(self):
        """Membuat semua tabel, view, trigger, dan stored procedure jika belum ada."""
        if not self._conn or not self._conn.is_connected():
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
        # Penting: Eksekusi DROP dan CREATE secara terpisah untuk trigger dan procedure
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogInsertPenghuni")
        trigger_insert_ddl = """
        CREATE TRIGGER trg_LogInsertPenghuni
        AFTER INSERT ON Penghuni
        FOR EACH ROW
        BEGIN
            DECLARE v_nomor_kamar INT; DECLARE v_nama_asrama VARCHAR(255); DECLARE v_nama_fakultas VARCHAR(255) DEFAULT NULL;
            SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar, v_nama_asrama FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = NEW.kamar_id_internal;
            IF NEW.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nama_fakultas FROM Fakultas WHERE fakultas_id = NEW.fakultas_id; END IF;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_baru, fakultas_baru, kamar_id_internal_baru, nomor_kamar_baru, nama_asrama_baru, aksi, keterangan_tambahan)
            VALUES (NEW.nim, NEW.nama_penghuni, v_nama_fakultas, NEW.kamar_id_internal, v_nomor_kamar, v_nama_asrama, 'INSERT', CONCAT('Penghuni baru ditambahkan ke kamar ', v_nomor_kamar, ' Asrama ', v_nama_asrama));
        END"""
        self._execute_single_ddl(trigger_insert_ddl)
        
        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogUpdatePenghuni")
        trigger_update_ddl = """
        CREATE TRIGGER trg_LogUpdatePenghuni
        AFTER UPDATE ON Penghuni
        FOR EACH ROW
        BEGIN
            DECLARE v_nmr_kmr_lama INT DEFAULT NULL; DECLARE v_nm_asr_lama VARCHAR(255) DEFAULT NULL; DECLARE v_nm_fak_lama VARCHAR(255) DEFAULT NULL;
            DECLARE v_nmr_kmr_baru INT DEFAULT NULL; DECLARE v_nm_asr_baru VARCHAR(255) DEFAULT NULL; DECLARE v_nm_fak_baru VARCHAR(255) DEFAULT NULL;
            DECLARE v_ket TEXT DEFAULT 'Data penghuni diubah.';
            IF OLD.kamar_id_internal IS NOT NULL THEN SELECT K.nomor_kamar, A.nama_asrama INTO v_nmr_kmr_lama, v_nm_asr_lama FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = OLD.kamar_id_internal; END IF;
            IF OLD.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nm_fak_lama FROM Fakultas WHERE fakultas_id = OLD.fakultas_id; END IF;
            IF NEW.kamar_id_internal IS NOT NULL THEN SELECT K.nomor_kamar, A.nama_asrama INTO v_nmr_kmr_baru, v_nm_asr_baru FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = NEW.kamar_id_internal; END IF;
            IF NEW.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nm_fak_baru FROM Fakultas WHERE fakultas_id = NEW.fakultas_id; END IF;
            IF OLD.kamar_id_internal != NEW.kamar_id_internal THEN SET v_ket = CONCAT('Penghuni pindah dari kamar ', IFNULL(v_nmr_kmr_lama, 'N/A'), ' Asrama ', IFNULL(v_nm_asr_lama, 'N/A'), ' ke kamar ', IFNULL(v_nmr_kmr_baru, 'N/A'), ' Asrama ', IFNULL(v_nm_asr_baru, 'N/A'), '.');
            ELSEIF OLD.fakultas_id != NEW.fakultas_id OR (OLD.fakultas_id IS NULL AND NEW.fakultas_id IS NOT NULL) OR (OLD.fakultas_id IS NOT NULL AND NEW.fakultas_id IS NULL) THEN SET v_ket = CONCAT('Fakultas diubah dari ', IFNULL(v_nm_fak_lama, 'N/A'), ' menjadi ', IFNULL(v_nm_fak_baru, 'N/A'), '.');
            ELSEIF OLD.nama_penghuni != NEW.nama_penghuni THEN SET v_ket = CONCAT('Nama diubah dari ', OLD.nama_penghuni, ' menjadi ', NEW.nama_penghuni, '.'); END IF;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_lama, nama_penghuni_baru, fakultas_lama, fakultas_baru, kamar_id_internal_lama, kamar_id_internal_baru, nomor_kamar_lama, nama_asrama_lama, nomor_kamar_baru, nama_asrama_baru, aksi, keterangan_tambahan)
            VALUES (OLD.nim, OLD.nama_penghuni, NEW.nama_penghuni, v_nm_fak_lama, v_nm_fak_baru, OLD.kamar_id_internal, NEW.kamar_id_internal, v_nmr_kmr_lama, v_nm_asr_lama, v_nmr_kmr_baru, v_nm_asr_baru, 'UPDATE', v_ket);
        END"""
        self._execute_single_ddl(trigger_update_ddl)

        self._execute_single_ddl("DROP TRIGGER IF EXISTS trg_LogDeletePenghuni")
        trigger_delete_ddl = """
        CREATE TRIGGER trg_LogDeletePenghuni
        AFTER DELETE ON Penghuni
        FOR EACH ROW
        BEGIN
            DECLARE v_nmr_kmr INT DEFAULT NULL; DECLARE v_nm_asr VARCHAR(255) DEFAULT NULL; DECLARE v_nm_fak VARCHAR(255) DEFAULT NULL;
            IF OLD.kamar_id_internal IS NOT NULL THEN SELECT K.nomor_kamar, A.nama_asrama INTO v_nmr_kmr, v_nm_asr FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id WHERE K.kamar_id_internal = OLD.kamar_id_internal; END IF;
            IF OLD.fakultas_id IS NOT NULL THEN SELECT nama_fakultas INTO v_nm_fak FROM Fakultas WHERE fakultas_id = OLD.fakultas_id; END IF;
            INSERT INTO AuditLogAktivitasPenghuni (nim, nama_penghuni_lama, fakultas_lama, kamar_id_internal_lama, nomor_kamar_lama, nama_asrama_lama, aksi, keterangan_tambahan)
            VALUES (OLD.nim, OLD.nama_penghuni, v_nm_fak, OLD.kamar_id_internal, v_nmr_kmr, v_nm_asr, 'DELETE', CONCAT('Penghuni dihapus dari kamar ', IFNULL(v_nmr_kmr, 'N/A'), ' Asrama ', IFNULL(v_nm_asr, 'N/A')));
        END"""
        self._execute_single_ddl(trigger_delete_ddl)
        print("Trigger telah diperiksa/dibuat.")

        # 4. Buat Stored Procedures
        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_TambahPenghuni")
        sp_tambah_penghuni_ddl = """
        CREATE PROCEDURE sp_TambahPenghuni (
            IN p_nim VARCHAR(50), IN p_nama_penghuni VARCHAR(255), IN p_nama_fakultas_input VARCHAR(255), 
            IN p_nomor_kamar INT, IN p_asrama_id INT, OUT p_status_code INT, OUT p_status_message VARCHAR(255)
        )
        BEGIN
            DECLARE v_k_id_int INT; DECLARE v_kap_kmr INT; DECLARE v_jml_p_skr INT; DECLARE v_fak_id INT DEFAULT NULL;
            SET p_status_code = 4; SET p_status_message = 'Terjadi kesalahan tidak diketahui.';
            IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN SET p_status_code = 5; SET p_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
            ELSE
                IF p_nama_fakultas_input IS NOT NULL AND p_nama_fakultas_input != '' THEN
                    SELECT fakultas_id INTO v_fak_id FROM Fakultas WHERE nama_fakultas = p_nama_fakultas_input;
                    IF v_fak_id IS NULL THEN INSERT INTO Fakultas (nama_fakultas) VALUES (p_nama_fakultas_input); SET v_fak_id = LAST_INSERT_ID(); END IF;
                END IF;
                SELECT kamar_id_internal INTO v_k_id_int FROM Kamar WHERE nomor_kamar = p_nomor_kamar AND asrama_id = p_asrama_id;
                IF v_k_id_int IS NULL THEN SET p_status_code = 1; SET p_status_message = 'Gagal: Kamar tidak ditemukan.';
                ELSE
                    SELECT kapasitas INTO v_kap_kmr FROM Kamar WHERE kamar_id_internal = v_k_id_int;
                    SELECT COUNT(*) INTO v_jml_p_skr FROM Penghuni WHERE kamar_id_internal = v_k_id_int;
                    IF v_jml_p_skr >= v_kap_kmr THEN SET p_status_code = 2; SET p_status_message = 'Gagal: Kamar sudah penuh.';
                    ELSE
                        IF EXISTS (SELECT 1 FROM Penghuni WHERE nim = p_nim) THEN SET p_status_code = 3; SET p_status_message = CONCAT('Gagal: NIM ', p_nim, ' sudah terdaftar.');
                        ELSE INSERT INTO Penghuni (nim, nama_penghuni, fakultas_id, kamar_id_internal) VALUES (p_nim, p_nama_penghuni, v_fak_id, v_k_id_int); SET p_status_code = 0; SET p_status_message = 'Sukses: Penghuni berhasil ditambahkan.';
                        END IF;
                    END IF;
                END IF;
            END IF;
        END""" # Dihapus SELECT OUT params
        self._execute_single_ddl(sp_tambah_penghuni_ddl)

        self._execute_single_ddl("DROP PROCEDURE IF EXISTS sp_PindahKamarPenghuni")
        sp_pindah_kamar_ddl = """
        CREATE PROCEDURE sp_PindahKamarPenghuni (
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
        END""" # Dihapus SELECT OUT params
        self._execute_single_ddl(sp_pindah_kamar_ddl)
        print("Stored Procedures telah diperiksa/dibuat.")

        print("Inisialisasi skema database selesai.")

    def _populate_initial_master_data_if_empty(self):
        """Mengisi data master awal untuk Asrama dan Fakultas jika tabel kosong."""
        if not self._conn or not self._conn.is_connected(): return

        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM Asrama")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                asramas_data = [
                    (1, "Aster"), (2, "Soka"), (3, "Tulip"), (4, "Edelweiss"),
                    (5, "Lily"), (6, "Dahlia"), (7, "Melati"), (8, "Anyelir")
                ]
                for asrama_id_val, nama in asramas_data:
                    self._execute_query("INSERT INTO Asrama (asrama_id, nama_asrama) VALUES (%s, %s)", (asrama_id_val, nama), is_ddl_or_commit_managed_elsewhere=True)
                self._conn.commit()
                print("Data awal Asrama dimasukkan.")

            self.cursor.execute("SELECT COUNT(*) as count FROM Fakultas")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                fakultas_data = [
                    ('Teknik'), ('Ekonomi dan Bisnis'), ('Ilmu Sosial dan Ilmu Politik'),
                    ('Kedokteran'), ('Ilmu Budaya'), ('MIPA'), ('Ilmu Komputer'),
                    ('Ilmu Keolahragaan'), ('Vokasi'), ('Ilmu Pendidikan')
                ]
                for nama_fak in fakultas_data:
                    self._execute_query("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fak,), is_ddl_or_commit_managed_elsewhere=True)
                self._conn.commit()
                print("Data awal Fakultas dimasukkan.")
            
            self.cursor.execute("SELECT COUNT(*) as count FROM Kamar")
            if (self._cursor.fetchone() or {}).get('count', 0) == 0:
                kamar_data_aster = [
                    (101, 1, 2), (102, 1, 2), (103, 1, 3), 
                    (201, 1, 2), (202, 1, 2), (203, 1, 2),
                    (301, 1, 2), (302, 1, 2), (303, 1, 2)
                ]
                for nk, aid, kap in kamar_data_aster:
                     self._execute_query("INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES (%s, %s, %s)", (nk, aid, kap), is_ddl_or_commit_managed_elsewhere=True)
                self._conn.commit()
                print("Data awal Kamar untuk Aster dimasukkan.")
        except mysql.connector.Error as e:
            print(f"Kesalahan saat mengisi data master awal: {e}")


    # ... (sisa metode DatabaseService seperti add_penghuni, pindah_kamar_penghuni, dll. tetap sama) ...
    # Metode add_penghuni dan pindah_kamar_penghuni akan menggunakan
    # pendekatan modifikasi list argumen untuk OUT params.

    def add_penghuni(self, nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val):
        """Menambahkan penghuni baru menggunakan Stored Procedure sp_TambahPenghuni."""
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return False
        try:
            # SP sp_TambahPenghuni expects 7 parameters: 5 IN, 2 OUT.
            # Pass a list of 7 elements to callproc.
            # The last 2 are placeholders for OUT params.
            proc_args_list = [nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val, 0, ""] # Inisialisasi OUT params
            
            # Panggil SP. Konektor akan mencoba mengisi nilai OUT ke proc_args_list
            self._cursor.callproc('sp_TambahPenghuni', proc_args_list) 
            
            # Ambil nilai OUT dari list yang sama
            status_code = proc_args_list[5] 
            status_message = proc_args_list[6]

            if status_code is not None: 
                if status_code == 0: 
                    messagebox.showinfo("Sukses", status_message, parent=self._parent_window)
                    self._conn.commit()  
                    return True
                else:
                    messagebox.showerror("Gagal Menambah Penghuni", status_message, parent=self._parent_window)
                    return False
            else:
                # Fallback jika list tidak dimodifikasi (jarang terjadi jika SP benar)
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari Stored Procedure Tambah Penghuni (OUT params tidak terisi dengan benar).", parent=self._parent_window)
                return False
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_TambahPenghuni: {err}", parent=self._parent_window)
            try:
                if self._conn.in_transaction: self._conn.rollback() 
            except: pass
            return False

    def pindah_kamar_penghuni(self, nim, nomor_kamar_baru, asrama_id_baru):
        """Memindahkan penghuni ke kamar lain menggunakan Stored Procedure sp_PindahKamarPenghuni."""
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return False, "Tidak ada koneksi database."
        try:
            # SP sp_PindahKamarPenghuni expects 5 parameters: 3 IN, 2 OUT.
            proc_args_list = [nim, nomor_kamar_baru, asrama_id_baru, 0, ""] # Inisialisasi OUT params

            self._cursor.callproc('sp_PindahKamarPenghuni', proc_args_list) 
            # Ambil nilai OUT dari list yang sama
            status_code = proc_args_list[3]
            status_message = proc_args_list[4]

            if status_code is not None: 
                if status_code == 0: 
                    if status_message and "Info:" in status_message: 
                        messagebox.showinfo("Info Pindah Kamar", status_message, parent=self._parent_window)
                    else:
                        messagebox.showinfo("Sukses Pindah Kamar", status_message if status_message else "Operasi berhasil.", parent=self._parent_window)
                    self._conn.commit() 
                    return True, status_message
                else:
                    messagebox.showerror("Gagal Pindah Kamar", status_message, parent=self._parent_window)
                    return False, status_message
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari Stored Procedure Pindah Kamar (OUT params tidak terisi dengan benar).", parent=self._parent_window)
                return False, "Gagal mengambil status SP."
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_PindahKamarPenghuni: {err}", parent=self._parent_window)
            try:
                if self._conn.in_transaction: self._conn.rollback() 
            except: pass
            return False, str(err)


    def update_penghuni(self, nim_original, nim_baru, nama_baru, nama_fakultas_baru):
        """Memperbarui data penghuni (Trigger akan mencatat log)."""
        if not self._conn or not self._conn.is_connected(): 
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.", parent=self._parent_window)
            return "ERROR_CONNECTION" 

        check_exists_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
        self._cursor.execute(check_exists_query, (nim_original,)) 
        if not self._cursor.fetchone(): 
            messagebox.showwarning("Perhatian", f"Tidak ada data penghuni yang cocok dengan NIM original: {nim_original}.", parent=self._parent_window)
            return "ERROR_NIM_ORIGINAL_NOT_FOUND"

        updates = []
        params = []
        
        if nim_baru and nim_original != nim_baru:
            if not nim_baru.isdigit(): 
                messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.", parent=self._parent_window)
                return "ERROR_INVALID_NIM_FORMAT"
            check_nim_conflict_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
            self._cursor.execute(check_nim_conflict_query, (nim_baru,)) 
            if self._cursor.fetchone(): 
                messagebox.showerror("Kesalahan", f"NIM baru '{nim_baru}' sudah digunakan oleh penghuni lain.", parent=self._parent_window)
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
                        self._cursor.execute("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fakultas_baru,)) 
                        fakultas_id_to_update = self._cursor.lastrowid  
                        if fakultas_id_to_update: 
                            self._conn.commit()  
                            print(f"Fakultas baru '{nama_fakultas_baru}' ditambahkan dengan ID: {fakultas_id_to_update}")
                        else: 
                            messagebox.showerror("Kesalahan", f"Gagal menambahkan fakultas baru '{nama_fakultas_baru}'.", parent=self._parent_window)
                            return "ERROR_ADD_FAKULTAS"
                    except mysql.connector.Error as e_fak:
                        messagebox.showerror("Kesalahan Database", f"Gagal menambahkan fakultas baru: {e_fak}", parent=self._parent_window)
                        return "ERROR_ADD_FAKULTAS_DB"
                updates.append("fakultas_id = %s")
                params.append(fakultas_id_to_update)
        
        if not updates:
            messagebox.showinfo("Info", "Tidak ada data yang akan diubah (semua input kosong atau sama dengan data lama).", parent=self._parent_window)
            return "SUCCESS_NO_CHANGE" 

        params_for_update = list(params) 
        params_for_update.append(nim_original)
        query = f"UPDATE Penghuni SET {', '.join(updates)} WHERE nim = %s"

        success = self._execute_query(query, tuple(params_for_update), is_ddl_or_commit_managed_elsewhere=False) 
        
        if success:
            if self._cursor.rowcount > 0: 
                messagebox.showinfo("Sukses", "Data penghuni berhasil diubah.", parent=self._parent_window)
                return "SUCCESS_DATA_CHANGED" 
            else:
                messagebox.showwarning("Perhatian", "Tidak ada perubahan aktual pada data (data baru mungkin sama dengan data lama).", parent=self._parent_window)
                return "SUCCESS_NO_ACTUAL_CHANGE" 
        else:
            return "ERROR_UPDATE_FAILED"


    def delete_penghuni(self, nim):
        success = self._execute_query("DELETE FROM Penghuni WHERE nim = %s", (nim,), is_ddl_or_commit_managed_elsewhere=False) 
        if success and self._cursor.rowcount > 0: 
            messagebox.showinfo("Sukses", f"Data penghuni dengan NIM {nim} berhasil dihapus.", parent=self._parent_window)
            return True
        elif success and self._cursor.rowcount == 0: 
            messagebox.showwarning("Gagal", f"Penghuni dengan NIM {nim} tidak ditemukan.", parent=self._parent_window)
            return False
        return False

    def get_audit_log_penghuni(self, limit=100): 
        """Mengambil data log aktivitas penghuni dengan batasan jumlah."""
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

# --- Kelas Dasar untuk Semua Layar ---
class BaseScreen:
    def __init__(self, screen_manager, db_service):
        self.screen_manager = screen_manager
        self.db_service = db_service
        self.app_instance = screen_manager.app
        self.canvas = self.app_instance.canvas
        self.widgets_on_screen = []
        self.canvas_items_on_screen = []
    def clear_screen_elements(self):
        for widget in self.widgets_on_screen: widget.destroy()
        self.widgets_on_screen = []
        for item in self.canvas_items_on_screen: self.canvas.delete(item)
        self.canvas_items_on_screen = []
    def add_widget(self, widget):
        self.widgets_on_screen.append(widget)
        return widget
    def create_canvas_text(self, *args, **kwargs):
        item = self.canvas.create_text(*args, **kwargs)
        self.canvas_items_on_screen.append(item)
        return item
    def create_canvas_image(self, *args, **kwargs):
        item = self.canvas.create_image(*args, **kwargs)
        self.canvas_items_on_screen.append(item)
        return item
    def setup_ui(self): raise NotImplementedError("Subclass harus mengimplementasikan metode setup_ui")

# --- Kelas Layar-Layar Aplikasi ---
class MainMenuScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(270, 300, text="MANAJEMEN\nSISTEM\nASRAMA", fill="#F47B07", font=("Cooper Black", 50, "bold"), anchor="w")
        tbl(self.canvas, 700, 180, 300, 100, 20, 20, 90, 180, 270, 360, "#F47B07", "Masuk", self.screen_manager.show_asrama_selection)
        tbl(self.canvas, 700, 300, 300, 100, 20, 20, 90, 180, 270, 360, "#4682B4", "Riwayat Aktivitas", self.screen_manager.show_riwayat_aktivitas)
        tbl(self.canvas, 700, 420, 300, 100, 20, 20, 90, 180, 270, 360, "red", "Keluar", self.app_instance.quit)

class AsramaSelectionScreen(BaseScreen):
    def setup_ui(self):
        self.create_canvas_text(540, 50, text="PILIH ASRAMA", fill="#F4FEFF", font=("Cooper Black", 30, "bold"))
        asramas_data = self.db_service.get_all_asrama()
        positions = [(50, 100), (420, 100), (780, 100), (50, 290), (420, 290), (780, 290), (50, 500), (420, 500)]
        if not asramas_data: self.create_canvas_text(540, 250, text="Tidak ada data asrama.", fill="red", font=("Arial", 16))
        for i, asrama_row in enumerate(asramas_data):
            if i < len(positions):
                x_pos, y_pos = positions[i]
                tbl(self.canvas, x_pos, y_pos, 250, 120, 20, 20, 90, 180, 270, 360, "#F47B07",
                    asrama_row['nama_asrama'], lambda aid=asrama_row['asrama_id'], aname=asrama_row['nama_asrama']: self.screen_manager.show_kamar_list(aid, aname))
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_main_menu)

class KamarListScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, asrama_id, asrama_nama):
        super().__init__(screen_manager, db_service)
        self.asrama_id = asrama_id; self.asrama_nama = asrama_nama
    def setup_ui(self):
        self.create_canvas_text(540, 50, text=f"Asrama {self.asrama_nama}", fill="#F4FEFF", font=("Cooper Black", 24, "bold"))
        tbl(self.canvas, 50, 15, 150, 50, 10, 10, 90, 180, 270, 360, "red", "Kembali", self.screen_manager.show_asrama_selection)
        kamars_layout = [("Kamar 101", 101, 50,100),("Kamar 102",102, 420,100),("Kamar 103",103, 780,100),
                         ("Kamar 201", 201, 50,300),("Kamar 202",202, 420,300),("Kamar 203",203, 780,300),
                         ("Kamar 301", 301, 50,500),("Kamar 302",302, 420,500),("Kamar 303",303, 780,500)]
        for nama, id_k, x, y in kamars_layout:
            tbl(self.canvas, x, y, 250, 120, 20, 20, 90, 180, 270, 360, "#F47B07", nama, lambda kid=id_k: self.screen_manager.show_kamar_detail(kid))

class KamarDetailScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context
        self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.kamar_id=kamar_id
        self.penghuni_treeview=None; self.treeview_scrollbar=None
    def setup_ui(self):
        style=ttk.Style(); style.configure("Custom.Treeview", background="#E1E1E1", fieldbackground="#FFFFFF", foreground="black")
        style.configure("Custom.Treeview.Heading", background="yellow", foreground="black", font=('Arial',10,'bold'), relief="flat")
        style.map("Custom.Treeview.Heading", background=[('active','#FFD700')])
        self.create_canvas_text(self.app_instance.appwidth/2, 80, text=f"Asrama {self.asrama_nama} - Kamar {self.kamar_id}", fill="#000000", font=("Cooper Black",22,"bold"))
        info_text_x=self.app_instance.appwidth/2; info_text_y=120
        jml_penghuni=self.db_service.get_jumlah_penghuni(self.kamar_id,self.asrama_id)
        kapasitas=self.db_service.get_kapasitas_kamar(self.kamar_id,self.asrama_id)
        self.create_canvas_text(info_text_x,info_text_y, text=f"Data Penghuni ({jml_penghuni}/{kapasitas})", fill="#000000", font=("Cooper Black",18,"bold"))
        table_x=50; table_y=info_text_y+20+20; table_container_width=self.app_instance.appwidth-(2*50)
        scrollbar_width=20; treeview_actual_width=table_container_width-scrollbar_width
        treeview_display_height=self.app_instance.appheight-table_y-70-120
        columns=("no","nim","nama","fakultas"); self.penghuni_treeview=ttk.Treeview(self.canvas,columns=columns,show='headings',style="Custom.Treeview")
        for col,txt,w,anc in [("no","No.",0.05,tk.CENTER),("nim","NIM",0.25,tk.W),("nama","Nama Mahasiswa",0.40,tk.W),("fakultas","Fakultas",0.30,tk.W)]:
            self.penghuni_treeview.heading(col,text=txt); self.penghuni_treeview.column(col,width=int(treeview_actual_width*w),anchor=anc,stretch=tk.YES if col!="no" else tk.NO)
        self.treeview_scrollbar=ttk.Scrollbar(self.canvas,orient="vertical",command=self.penghuni_treeview.yview)
        self.penghuni_treeview.configure(yscrollcommand=self.treeview_scrollbar.set)
        _,daftar_penghuni=self.db_service.get_penghuni_in_kamar(self.kamar_id,self.asrama_id)
        for i in self.penghuni_treeview.get_children(): self.penghuni_treeview.delete(i)
        if daftar_penghuni and not (isinstance(daftar_penghuni[0],str) and daftar_penghuni[0].startswith("Info:")):
            for i,p in enumerate(daftar_penghuni): self.penghuni_treeview.insert("","end",values=(i+1,p['nim'],p['nama_penghuni'],p.get('fakultas') or "N/A")) 
        else:
            if not self.penghuni_treeview.get_children(): self.penghuni_treeview.insert("","end",values=("","Belum ada penghuni.","",""))
        self.add_widget(self.penghuni_treeview); self.add_widget(self.treeview_scrollbar)
        self.canvas.create_window(table_x,table_y,anchor=tk.NW,window=self.penghuni_treeview,width=treeview_actual_width,height=treeview_display_height)
        self.canvas.create_window(table_x+treeview_actual_width,table_y,anchor=tk.NW,window=self.treeview_scrollbar,height=treeview_display_height)
        y_buttons=15; btn_width=150; btn_spacing=160; current_x=50
        actions=[("Kembali","red",lambda:self.screen_manager.show_kamar_list(self.asrama_id,self.asrama_nama)),
                 ("Tambah Data","#F47B07",lambda:self.screen_manager.show_insert_data_form(self.kamar_id)),
                 ("Ubah Data","#F47B07",lambda:self.screen_manager.show_update_data_form(self.kamar_id)),
                 ("Hapus Data","#F47B07",lambda:self.screen_manager.show_delete_data_form(self.kamar_id))]
        for i, (text,color,cmd) in enumerate(actions):
            tbl(self.canvas,current_x + (i*btn_spacing),y_buttons,btn_width,50,10,10,90,180,270,360,color,text,cmd)
        y_pindah=table_y+treeview_display_height+25; lebar_pindah=200; x_pindah=(self.app_instance.appwidth/2)-(lebar_pindah/2)
        tbl(self.canvas,x_pindah,y_pindah,lebar_pindah,50,10,10,90,180,270,360,"blue","Pindah Kamar",lambda:self.screen_manager.show_pindah_kamar_form(self.kamar_id))

    def clear_screen_elements(self): super().clear_screen_elements(); self.penghuni_treeview=None; self.treeview_scrollbar=None

class InsertDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context; self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.kamar_id=kamar_id; self.nim_entry=None; self.nama_entry=None; self.fakultas_pilihan=StringVar()
        self.fakultas_map={}
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Insert Data Kamar {self.kamar_id} Asrama {self.asrama_nama}",fill="#F4F0FF",font=("Cooper Black",24,"bold"))
        self.create_canvas_text(365,188,text="NIM",fill="#F4FEFF",font=("Arial",12,"bold"))
        self.nim_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF")); self.nim_entry.place(x=350,y=200)
        self.create_canvas_text(374,270,text="Nama",fill="#F4FEFF",font=("Arial",12,"bold"))
        self.nama_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF")); self.nama_entry.place(x=350,y=280)
        self.create_canvas_text(385,340,text="Fakultas",fill="#F4FEFF",font=("Arial",12,"bold"))
        fakultas_db=self.db_service.get_all_fakultas(); fakultas_display_list=[""]
        if fakultas_db:
            for fak in fakultas_db: self.fakultas_map[fak['nama_fakultas']]=fak['fakultas_id']; fakultas_display_list.append(fak['nama_fakultas'])
        self.fakultas_pilihan.set(fakultas_display_list[0])
        dropdown=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.fakultas_pilihan,values=fakultas_display_list,width=29,font=("Arial",18),state="readonly"))
        dropdown.place(x=350,y=360)
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"#F47B07","Simpan",self._save_data)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.kamar_id))
    def _save_data(self):
        nim=self.nim_entry.get(); nama=self.nama_entry.get(); nama_fakultas_terpilih=self.fakultas_pilihan.get()
        if not nim or not nama: messagebox.showwarning("Input Tidak Lengkap","NIM dan Nama tidak boleh kosong."); return
        if nim and not nim.isdigit(): 
            messagebox.showerror("Kesalahan Input", "NIM harus berupa angka.")
            return
        if self.db_service.add_penghuni(nim,nama,nama_fakultas_terpilih if nama_fakultas_terpilih else None,self.kamar_id,self.asrama_id):
            self.screen_manager.show_kamar_detail(self.kamar_id)

class UpdateDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context; self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.kamar_id=kamar_id; self.selected_mahasiswa_nim_original=None; self.nim_baru_entry=None; self.nama_baru_entry=None
        self.fakultas_baru_pilihan=StringVar(); self.plh_mahasiswa_var=StringVar(); self.data_lengkap_mahasiswa_cache=[]; self.fakultas_map={}
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Ubah Data Kamar {self.kamar_id} Asrama {self.asrama_nama}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        opsi_display_db,self.data_lengkap_mahasiswa_cache=self.db_service.get_penghuni_in_kamar(self.kamar_id,self.asrama_id)
        self.create_canvas_text(413,100,text="Pilih Mahasiswa (NIM - Nama)",fill="#F4FEFF",font=("Arial",12,"bold"))
        m_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.plh_mahasiswa_var,font=("Arial",15),state="readonly",values=opsi_display_db,width=34))
        m_dd.place(x=350,y=120);m_dd.bind("<<ComboboxSelected>>",self._on_mahasiswa_selected)
        self.create_canvas_text(386,178,text="NIM Baru (Kosongkan jika tidak diubah)",fill="#F4FEFF",font=("Arial",10,"bold"))
        self.nim_baru_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF"));self.nim_baru_entry.place(x=350,y=190)
        self.create_canvas_text(391,258,text="Nama Baru (Kosongkan jika tidak diubah)",fill="#F4FEFF",font=("Arial",10,"bold"))
        self.nama_baru_entry=self.add_widget(Entry(self.canvas,width=30,font=("Arial",18),bg="#F4FEFF"));self.nama_baru_entry.place(x=350,y=270)
        self.create_canvas_text(405,328,text="Fakultas Baru",fill="#F4FEFF",font=("Arial",12,"bold"))
        fakultas_db=self.db_service.get_all_fakultas();fakultas_display_list=[""]
        if fakultas_db:
            for fak in fakultas_db:self.fakultas_map[fak['nama_fakultas']]=fak['fakultas_id'];fakultas_display_list.append(fak['nama_fakultas'])
        f_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.fakultas_baru_pilihan,values=fakultas_display_list,width=29,font=("Arial",18),state="readonly"))
        f_dd.place(x=350,y=350)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:")and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0]);self._on_mahasiswa_selected()
        elif opsi_display_db and(opsi_display_db[0].startswith("Info:")or opsi_display_db[0].startswith("Kesalahan:")):self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:
            self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
            if self.nim_baru_entry:self.nim_baru_entry.delete(0,tk.END)
            if self.nama_baru_entry:self.nama_baru_entry.delete(0,tk.END)
            self.fakultas_baru_pilihan.set("")
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"#F47B07","Ubah",self._update_data_action)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.kamar_id))
    def _get_nim_from_selection(self,s):return s.split(" - ")[0]if" - "in s else None
    def _on_mahasiswa_selected(self,e=None):
        if not all([self.nim_baru_entry,self.nama_baru_entry,hasattr(self.fakultas_baru_pilihan,'set')]):return
        s_disp_s=self.plh_mahasiswa_var.get();nim_orig=self._get_nim_from_selection(s_disp_s)
        self.selected_mahasiswa_nim_original=nim_orig
        self.nim_baru_entry.delete(0,tk.END);self.nama_baru_entry.delete(0,tk.END);self.fakultas_baru_pilihan.set("")
        if nim_orig and self.data_lengkap_mahasiswa_cache:
            for d_mhs in self.data_lengkap_mahasiswa_cache:
                if str(d_mhs['nim'])==str(nim_orig):
                    self.nama_baru_entry.insert(0,str(d_mhs['nama_penghuni']))
                    self.fakultas_baru_pilihan.set(str(d_mhs.get('fakultas'))if d_mhs.get('fakultas')else"")
                    break
    def _update_data_action(self):
        if not self.selected_mahasiswa_nim_original:messagebox.showwarning("Peringatan","Pilih mahasiswa.");return
        nim_n=self.nim_baru_entry.get().strip();nama_n=self.nama_baru_entry.get().strip();fak_n=self.fakultas_baru_pilihan.get()
        
        if nim_n and not nim_n.isdigit():
            messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.")
            return
        
        current_nama_e_v=self.nama_baru_entry.get()
        if not nama_n and current_nama_e_v.strip() != "": 
             messagebox.showwarning("Input Tidak Valid","Nama baru tidak boleh dikosongkan jika field diisi.")
             return
        
        update_status = self.db_service.update_penghuni(self.selected_mahasiswa_nim_original,nim_n,nama_n,fak_n if fak_n else None)
        
        if update_status == "SUCCESS_DATA_CHANGED":
            self.screen_manager.show_kamar_detail(self.kamar_id)
        # Jika "SUCCESS_NO_CHANGE", "SUCCESS_NO_ACTUAL_CHANGE", atau error lainnya, tetap di layar ini.
        # Pesan error/info sudah ditangani oleh DatabaseService.

class DeleteDataScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id):
        super().__init__(screen_manager, db_service)
        self.asrama_id=self.screen_manager.current_asrama_id_context; self.asrama_nama=self.screen_manager.current_asrama_nama_context
        self.kamar_id=kamar_id; self.plh_mahasiswa_var=StringVar(); self.selected_mahasiswa_nim_to_delete=None
    def setup_ui(self):
        self.create_canvas_text(560,50,text=f"Hapus Data Kamar {self.kamar_id} Asrama {self.asrama_nama}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        opsi_display_db,_=self.db_service.get_penghuni_in_kamar(self.kamar_id,self.asrama_id)
        self.create_canvas_text(413,290,text="Pilih Mahasiswa (NIM - Nama) untuk Dihapus",fill="#F4FEFF",font=("Arial",12,"bold"))
        m_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.plh_mahasiswa_var,font=("Arial",15),state="readonly",values=opsi_display_db,width=34))
        m_dd.place(x=350,y=310);m_dd.bind("<<ComboboxSelected>>",self._on_mahasiswa_selected)
        if opsi_display_db and not opsi_display_db[0].startswith("Info:")and not opsi_display_db[0].startswith("Kesalahan:"):
            self.plh_mahasiswa_var.set(opsi_display_db[0]);self._on_mahasiswa_selected()
        elif opsi_display_db and(opsi_display_db[0].startswith("Info:")or opsi_display_db[0].startswith("Kesalahan:")):self.plh_mahasiswa_var.set(opsi_display_db[0])
        else:self.plh_mahasiswa_var.set("Tidak ada data penghuni.")
        tbl(self.canvas,300,430,200,70,20,20,90,180,270,360,"red","Hapus",self._delete_data_action)
        tbl(self.canvas,600,430,200,70,20,20,90,180,270,360,"#F47B07","Batal",lambda:self.screen_manager.show_kamar_detail(self.kamar_id))
    def _get_nim_from_selection(self,s):return s.split(" - ")[0]if" - "in s else None
    def _on_mahasiswa_selected(self,e=None):self.selected_mahasiswa_nim_to_delete=self._get_nim_from_selection(self.plh_mahasiswa_var.get())
    def _delete_data_action(self):
        if not self.selected_mahasiswa_nim_to_delete:messagebox.showwarning("Peringatan","Pilih mahasiswa.");return
        if messagebox.askyesno("Konfirmasi Hapus",f"Yakin hapus NIM {self.selected_mahasiswa_nim_to_delete}?"):
            if self.db_service.delete_penghuni(self.selected_mahasiswa_nim_to_delete):self.screen_manager.show_kamar_detail(self.kamar_id)

class PindahKamarScreen(BaseScreen):
    def __init__(self, screen_manager, db_service, kamar_id_asal):
        super().__init__(screen_manager, db_service)
        self.kamar_id_asal=kamar_id_asal; self.asrama_id_asal=screen_manager.current_asrama_id_context
        self.asrama_nama_asal=screen_manager.current_asrama_nama_context
        self.selected_nim_var=StringVar(); self.selected_asrama_tujuan_var=StringVar(); self.selected_kamar_tujuan_var=StringVar()
        self.penghuni_asal_options=[]; self.asrama_tujuan_options_map={}; self.kamar_tujuan_options=[]
    def setup_ui(self):
        self.create_canvas_text(self.app_instance.appwidth/2,50,text=f"Pindah Kamar dari {self.asrama_nama_asal} - Kamar {self.kamar_id_asal}",fill="#F4FEFF",font=("Cooper Black",20,"bold"))
        y_curr=110;lbl_w=150;dd_w_char=30;est_dd_px_w=dd_w_char*7;form_w=lbl_w+10+est_dd_px_w
        x_lbl=(self.app_instance.appwidth-form_w)/2;x_dd=x_lbl+lbl_w+10
        self.create_canvas_text(x_lbl,y_curr+10,text="Pilih Penghuni:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        opsi_p,_=self.db_service.get_penghuni_in_kamar(self.kamar_id_asal,self.asrama_id_asal)
        self.penghuni_asal_options=opsi_p if not(opsi_p and opsi_p[0].startswith("Info:"))else["Tidak ada penghuni"]
        p_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_nim_var,values=self.penghuni_asal_options,width=dd_w_char,state="readonly",font=("Arial",14)))
        p_dd.place(x=x_dd,y=y_curr);y_curr+=50
        if self.penghuni_asal_options and self.penghuni_asal_options[0]!="Tidak ada penghuni":self.selected_nim_var.set(self.penghuni_asal_options[0])
        self.create_canvas_text(x_lbl,y_curr+10,text="Asrama Tujuan:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        all_a=self.db_service.get_all_asrama();self.asrama_tujuan_options_map={a['nama_asrama']:a['asrama_id']for a in all_a}
        a_disp_opts=list(self.asrama_tujuan_options_map.keys())
        a_t_dd=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_asrama_tujuan_var,values=a_disp_opts,width=dd_w_char,state="readonly",font=("Arial",14)))
        a_t_dd.place(x=x_dd,y=y_curr);a_t_dd.bind("<<ComboboxSelected>>",self._on_asrama_tujuan_selected);y_curr+=50
        self.create_canvas_text(x_lbl,y_curr+10,text="Kamar Tujuan:",fill="#F4FEFF",font=("Arial",12,"bold"),anchor="w")
        self.kamar_tujuan_dropdown=self.add_widget(ttk.Combobox(self.canvas,textvariable=self.selected_kamar_tujuan_var,values=[],width=dd_w_char,state="disabled",font=("Arial",14)))
        self.kamar_tujuan_dropdown.place(x=x_dd,y=y_curr);y_curr+=70
        btn_w=200;x_btn_p=self.app_instance.appwidth/2-btn_w-10;x_btn_b=self.app_instance.appwidth/2+10
        tbl(self.canvas,x_btn_p,y_curr,btn_w,50,10,10,90,180,270,360,"blue","Pindahkan",self._proses_pindah_kamar)
        tbl(self.canvas,x_btn_b,y_curr,btn_w,50,10,10,90,180,270,360,"red","Batal",lambda:self.screen_manager.show_kamar_detail(self.kamar_id_asal))
    def _on_asrama_tujuan_selected(self,e=None):
        nama_a=self.selected_asrama_tujuan_var.get();id_a_t=self.asrama_tujuan_options_map.get(nama_a)
        if id_a_t:
            kamars=self.db_service.get_all_kamar_in_asrama(id_a_t);self.kamar_tujuan_options=[k['nomor_kamar']for k in kamars]
            self.kamar_tujuan_dropdown['values']=self.kamar_tujuan_options
            if self.kamar_tujuan_options:self.selected_kamar_tujuan_var.set(self.kamar_tujuan_options[0]);self.kamar_tujuan_dropdown['state']="readonly"
            else:self.selected_kamar_tujuan_var.set("Tidak ada kamar");self.kamar_tujuan_dropdown['state']="disabled"
        else:self.kamar_tujuan_options=[];self.kamar_tujuan_dropdown['values']=[];self.selected_kamar_tujuan_var.set("");self.kamar_tujuan_dropdown['state']="disabled"
    def _proses_pindah_kamar(self):
        nim_s=self.selected_nim_var.get()
        if not nim_s or nim_s=="Tidak ada penghuni":messagebox.showwarning("Peringatan","Pilih penghuni.");return
        nim_m=nim_s.split(" - ")[0]
        nama_a_t=self.selected_asrama_tujuan_var.get();id_a_t=self.asrama_tujuan_options_map.get(nama_a_t)
        no_k_t_s=self.selected_kamar_tujuan_var.get()
        if not id_a_t or not no_k_t_s or no_k_t_s=="Tidak ada kamar":messagebox.showwarning("Peringatan","Pilih asrama & kamar tujuan.");return
        try:no_k_t=int(no_k_t_s)
        except ValueError:messagebox.showerror("Kesalahan","Nomor kamar tujuan tidak valid.");return
        succ,msg=self.db_service.pindah_kamar_penghuni(nim_m,no_k_t,id_a_t)
        if succ:self.screen_manager.show_kamar_detail(self.kamar_id_asal)

class RiwayatAktivitasScreen(BaseScreen):
    def __init__(self, screen_manager, db_service):
        super().__init__(screen_manager, db_service)
        self.log_treeview=None; self.log_scrollbar=None
    def setup_ui(self):
        style=ttk.Style(); style.configure("Riwayat.Treeview",background="#F0F0F0",fieldbackground="#FFFFFF",foreground="black",rowheight=25)
        style.configure("Riwayat.Treeview.Heading",background="#BFBFBF",foreground="black",font=('Arial',10,'bold'),relief="flat")
        style.map("Riwayat.Treeview.Heading",background=[('active','#A0A0A0')])
        self.create_canvas_text(self.app_instance.appwidth/2,50,text="Riwayat Aktivitas Penghuni",fill="#000000",font=("Cooper Black",24,"bold"))
        tbl_pad_h=30;tbl_pad_top=90;tbl_pad_bot=70;tbl_x=tbl_pad_h;tbl_y=tbl_pad_top
        tbl_cont_w=self.app_instance.appwidth-(2*tbl_pad_h);scr_w=20;tree_w=tbl_cont_w-scr_w
        tree_h=self.app_instance.appheight-tbl_y-tbl_pad_bot-20
        cols=("log_id","waktu","aksi","nim","nama","detail_kamar","keterangan")
        self.log_treeview=ttk.Treeview(self.canvas,columns=cols,show='headings',style="Riwayat.Treeview")
        hdrs={"log_id":"ID","waktu":"Waktu","aksi":"Aksi","nim":"NIM","nama":"Nama Terkait","detail_kamar":"Detail Perubahan","keterangan":"Keterangan"}
        cols_cfg={"log_id":{"w":0.04,"anc":tk.CENTER,"st":tk.NO},"waktu":{"w":0.15,"anc":tk.W,"st":tk.YES},"aksi":{"w":0.07,"anc":tk.W,"st":tk.YES},
                  "nim":{"w":0.12,"anc":tk.W,"st":tk.YES},"nama":{"w":0.18,"anc":tk.W,"st":tk.YES},
                  "detail_kamar":{"w":0.22,"anc":tk.W,"st":tk.YES},"keterangan":{"w":0.22,"anc":tk.W,"st":tk.YES}}
        for c,t in hdrs.items(): self.log_treeview.heading(c,text=t); self.log_treeview.column(c,width=int(tree_w*cols_cfg[c]["w"]),anchor=cols_cfg[c]["anc"],stretch=cols_cfg[c]["st"])
        self.log_scrollbar=ttk.Scrollbar(self.canvas,orient="vertical",command=self.log_treeview.yview); self.log_treeview.configure(yscrollcommand=self.log_scrollbar.set)
        logs=self.db_service.get_audit_log_penghuni(limit=200)
        for i in self.log_treeview.get_children(): self.log_treeview.delete(i)
        if logs:
            for log in logs: self.log_treeview.insert("","end",values=(log['log_id'],log['waktu_aksi_formatted'],log['aksi'],log['nim'],log['nama_terkait'],log['detail_perubahan'],log['keterangan_tambahan']))
        else: self.log_treeview.insert("","end",values=("","Belum ada riwayat.","","","","",""))
        self.add_widget(self.log_treeview); self.add_widget(self.log_scrollbar)
        self.canvas.create_window(tbl_x,tbl_y,anchor=tk.NW,window=self.log_treeview,width=tree_w,height=tree_h)
        self.canvas.create_window(tbl_x+tree_w,tbl_y,anchor=tk.NW,window=self.log_scrollbar,height=tree_h)
        y_btn_b=self.app_instance.appheight-50;w_btn_b=150;x_btn_b=(self.app_instance.appwidth-w_btn_b)/2
        tbl(self.canvas,x_btn_b,y_btn_b,w_btn_b,40,10,10,90,180,270,360,"gray","Kembali",self.screen_manager.show_main_menu)
    def clear_screen_elements(self): super().clear_screen_elements(); self.log_treeview=None; self.log_scrollbar=None

# ==============================================================================
# == KELAS ScreenManager ==
# ==============================================================================
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

# ==============================================================================
# == KELAS AppGui (Aplikasi Utama) ==
# ==============================================================================
class AppGui: 
    def __init__(self, root_window):
        self.window = root_window
        self.window.title("Manajemen Asrama OOP - MySQL")
        self.appwidth = 1080
        self.appheight = 700
        self._setup_window_geometry()
        self.canvas = Canvas(self.window, width=self.appwidth, height=self.appheight)
        self.canvas.place(x=0, y=0)
        self.bg_image_tk = None
        self.asset_path = "./assets/um.png" 
        self._load_assets()
        
        MYSQL_HOST = os.getenv("DB_HOST", "localhost")
        MYSQL_USER = os.getenv("DB_USER", "root")
        MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "") 
        MYSQL_DB_NAME = os.getenv("DB_NAME", "asrama_db_mysql") 
        
        self.db_service = DatabaseService(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database_name=MYSQL_DB_NAME, parent_window=self.window) 
        self.screen_manager = ScreenManager(self, self.db_service)
        
        if self.db_service._conn and self.db_service._conn.is_connected(): 
            self._draw_background()
            self.screen_manager.show_main_menu()
        else:
            self.canvas.create_text(self.appwidth / 2, self.appheight / 2, text="Koneksi ke Database Gagal.\nPeriksa konfigurasi dan server MySQL Anda.\nAplikasi tidak dapat dimulai.", font=("Arial", 16, "bold"), fill="red", justify=tk.CENTER)

    def _setup_window_geometry(self):
        screen_width = self.window.winfo_screenwidth()
        x_pos = (screen_width / 2) - (self.appwidth / 2)
        y_pos = 0
        self.window.geometry(f"{self.appwidth}x{self.appheight}+{int(x_pos)}+{int(y_pos)}")
        self.window.resizable(False, False)

    def _load_assets(self):
        try:
            current_script_dir = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
            assets_dir = os.path.join(current_script_dir, "assets")
            
            if not os.path.isdir(assets_dir): 
                try:
                    os.makedirs(assets_dir)
                    print(f"Direktori '{assets_dir}' dibuat. Harap letakkan 'um.png' di dalamnya.")
                except OSError as e:
                    print(f"Gagal membuat direktori '{assets_dir}': {e}")
            
            image_path = os.path.join(assets_dir, "um.png")

            if not os.path.exists(image_path):
                 messagebox.showwarning("Aset Tidak Ditemukan", f"File gambar '{image_path}' tidak ditemukan. Background akan default.", parent=self.window if self.window.winfo_exists() else None)
                 self.bg_image_tk = None
                 return

            bg_img_pil = Image.open(image_path).resize((self.appwidth, self.appheight))
            self.bg_image_tk = ImageTk.PhotoImage(bg_img_pil)
        except FileNotFoundError: 
            messagebox.showwarning("Aset Tidak Ditemukan", f"Pastikan file '{self.asset_path}' ada di direktori 'assets'.", parent=self.window if self.window.winfo_exists() else None)
            self.bg_image_tk = None 
        except Exception as e: 
            messagebox.showerror("Kesalahan Aset", f"Gagal memuat gambar: {e}", parent=self.window if self.window.winfo_exists() else None)
            self.bg_image_tk = None 

    def _draw_background(self):
        if self.bg_image_tk: 
            self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor=NW, tags="app_background")
        else: 
            self.canvas.create_rectangle(0,0, self.appwidth, self.appheight, fill="#CCCCCC", tags="app_background")

    def _clear_canvas_for_new_screen(self):
        all_items = self.canvas.find_all()
        for item in all_items:
            if "app_background" not in self.canvas.gettags(item): 
                self.canvas.delete(item)

    def quit(self):
        if messagebox.askokcancel("Keluar", "Anda yakin ingin keluar dari aplikasi?", parent=self.window):
            if self.db_service: 
                self.db_service._close()
            self.window.quit()
            self.window.destroy()

# ==============================================================================
# == TITIK MASUK APLIKASI ==
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    main_app = AppGui(root) 
    root.mainloop()
