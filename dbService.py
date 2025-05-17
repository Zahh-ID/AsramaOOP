import mysql.connector
from tkinter import messagebox
class DatabaseService:
    """
    Mengenkapsulasi semua interaksi dengan database MySQL.
    Menyediakan metode untuk operasi CRUD pada entitas Asrama, Kamar, dan Penghuni.
    Menggunakan View dan Stored Procedure.
    """
    def __init__(self, host, user, password, database_name):
        self.__host = host
        self.__user = user
        self.__password = password
        self.__database_name = database_name
        self.__conn = None
        self.__cursor = None
        self._connect()
        if self.conn:
            self._create_main_tables_if_not_exist() 
            self._ensure_log_table_exists() 

    def _connect(self):
        """Membuat koneksi ke database MySQL."""
        try:
            self.conn = mysql.connector.connect(
                host=self.__host,
                user=self.__user,
                password=self.__password,
                database=self.__database_name
            )
            self.cursor = self.conn.cursor(dictionary=True) 
            print("Berhasil terhubung ke database MySQL.")
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

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False, is_ddl_or_commit_managed_elsewhere=False):
        """Helper untuk eksekusi kueri dengan error handling."""
        if not self.conn or not self.conn.is_connected():
            print("Kesalahan Database: Tidak ada koneksi ke database MySQL.")
            return None if fetch_one or fetch_all else False
        try:
            self.cursor.execute(query, params)
            if not is_ddl_or_commit_managed_elsewhere and \
               query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self.conn.commit()
            if fetch_one:
                return self.cursor.fetchone()
            if fetch_all:
                return self.cursor.fetchall()
            return True
        except mysql.connector.Error as err:
            print(f"Kesalahan kueri MySQL: {err}\nKueri: {query}\nParams: {params}")
            messagebox.showerror("Kesalahan Kueri Database", f"Terjadi kesalahan saat menjalankan kueri: {err}")
            if not is_ddl_or_commit_managed_elsewhere: 
                 try:
                    if self.conn.in_transaction: 
                        self.conn.rollback()
                 except mysql.connector.Error as rb_err:
                    print(f"Kesalahan saat rollback: {rb_err}")
            return None if fetch_one or fetch_all else False

    def _create_main_tables_if_not_exist(self):
        """Membuat tabel utama jika belum ada. View, SP, Trigger harus dibuat di server."""
        if not self.conn or not self.conn.is_connected(): return
        tables_ddl = [
            """CREATE TABLE IF NOT EXISTS Asrama (
                asrama_id INTEGER PRIMARY KEY,
                nama_asrama VARCHAR(255) NOT NULL UNIQUE
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
                nim VARCHAR(50) PRIMARY KEY,
                nama_penghuni VARCHAR(255) NOT NULL,
                fakultas VARCHAR(255),
                kamar_id_internal INTEGER NOT NULL,
                FOREIGN KEY (kamar_id_internal) REFERENCES Kamar(kamar_id_internal) ON DELETE CASCADE
            ) ENGINE=InnoDB;"""
        ]
        try:
            for ddl in tables_ddl:
                self._execute_query(ddl, is_ddl_or_commit_managed_elsewhere=True)
            self.conn.commit() 
            print("Tabel utama Asrama, Kamar, Penghuni telah diperiksa/dibuat.")
        except mysql.connector.Error as e:
            print(f"Kesalahan pembuatan tabel utama MySQL: {e}")

    def _ensure_log_table_exists(self):
        """Memastikan tabel log aktivitas ada."""
        ddl_log_table = """
        CREATE TABLE IF NOT EXISTS AuditLogAktivitasPenghuni (
            log_id INT AUTO_INCREMENT PRIMARY KEY, nim VARCHAR(50),
            nama_penghuni_lama VARCHAR(255) DEFAULT NULL, nama_penghuni_baru VARCHAR(255) DEFAULT NULL,
            fakultas_lama VARCHAR(255) DEFAULT NULL, fakultas_baru VARCHAR(255) DEFAULT NULL,
            kamar_id_internal_lama INT DEFAULT NULL, kamar_id_internal_baru INT DEFAULT NULL,
            nomor_kamar_lama INT DEFAULT NULL, nama_asrama_lama VARCHAR(255) DEFAULT NULL,
            nomor_kamar_baru INT DEFAULT NULL, nama_asrama_baru VARCHAR(255) DEFAULT NULL,
            aksi VARCHAR(10) NOT NULL, waktu_aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            keterangan_tambahan TEXT DEFAULT NULL
        ) ENGINE=InnoDB;
        """
        if self._execute_query(ddl_log_table, is_ddl_or_commit_managed_elsewhere=True):
            self.conn.commit() 
            print("Tabel AuditLogAktivitasPenghuni telah diperiksa/dibuat.")


    # --- Metode CRUD untuk Asrama ---
    def get_all_asrama(self):
        """Mengambil semua data asrama."""
        return self._execute_query("SELECT asrama_id, nama_asrama FROM Asrama ORDER BY asrama_id", fetch_all=True) or []

    # --- Metode CRUD untuk Kamar ---
    def get_kamar_id_internal(self, nomor_kamar_val, asrama_id_val):
        """Mendapatkan ID internal kamar."""
        result = self._execute_query("SELECT kamar_id_internal FROM Kamar WHERE nomor_kamar = %s AND asrama_id = %s",
                                     (nomor_kamar_val, asrama_id_val), fetch_one=True)
        return result['kamar_id_internal'] if result else None

    def get_kapasitas_kamar(self, nomor_kamar_val, asrama_id_val):
        """Mengambil kapasitas kamar menggunakan View."""
        result = self._execute_query("SELECT kapasitas FROM vw_DetailKamarPenghuni WHERE nomor_kamar = %s AND asrama_id = %s",
                                     (nomor_kamar_val, asrama_id_val), fetch_one=True)
        return result['kapasitas'] if result else 0

    def get_jumlah_penghuni(self, nomor_kamar_val, asrama_id_val):
        """Mengambil jumlah penghuni dalam satu kamar menggunakan View."""
        result = self._execute_query("SELECT jumlah_penghuni_sekarang FROM vw_DetailKamarPenghuni WHERE nomor_kamar = %s AND asrama_id = %s",
                                     (nomor_kamar_val, asrama_id_val), fetch_one=True)
        return result['jumlah_penghuni_sekarang'] if result else 0
    
    def get_all_kamar_in_asrama(self, asrama_id_val):
        """Mengambil semua nomor kamar dalam satu asrama."""
        query = "SELECT nomor_kamar FROM Kamar WHERE asrama_id = %s ORDER BY nomor_kamar ASC"
        return self._execute_query(query, (asrama_id_val,), fetch_all=True) or []


    # --- Metode CRUD untuk Penghuni ---
    def get_penghuni_in_kamar(self, nomor_kamar_val, asrama_id_val):
        """Mengambil data penghuni dalam satu kamar menggunakan View."""
        kamar_internal_id = self.get_kamar_id_internal(nomor_kamar_val, asrama_id_val)
        if not kamar_internal_id:
            return ["Info: Kamar tidak ditemukan"], []

        query = """
            SELECT nim, nama_penghuni, fakultas, nomor_kamar, nama_asrama
            FROM vw_DaftarPenghuniLengkap
            WHERE kamar_id_internal = %s
            ORDER BY nama_penghuni ASC
        """
        data_lengkap_rows = self._execute_query(query, (kamar_internal_id,), fetch_all=True)

        if not data_lengkap_rows:
            return ["Info: Kamar ini kosong"], []

        opsi_display = [f"{row['nim']} - {row['nama_penghuni']}" for row in data_lengkap_rows]
        data_lengkap_list_of_dicts = [dict(row) for row in data_lengkap_rows]
        return opsi_display, data_lengkap_list_of_dicts

    def add_penghuni(self, nim, nama, fakultas, nomor_kamar_val, asrama_id_val):
        """Menambahkan penghuni baru menggunakan Stored Procedure sp_TambahPenghuni."""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return False
        try:
            # SP sp_TambahPenghuni expects 7 parameters: 5 IN, 2 OUT.
            # Pass a list/tuple of 7 elements to callproc.
            # The last 2 are placeholders for OUT params.
            args_for_callproc = [nim, nama, fakultas, nomor_kamar_val, asrama_id_val, None, None] 
            
            self.cursor.callproc('sp_TambahPenghuni', args_for_callproc) 
            
            out_params_dict = None
            # Mengambil hasil SELECT dari SP yang berisi parameter OUT
            for result in self.cursor.stored_results():
                out_params_dict = result.fetchone() 
                break 

            if out_params_dict:
                status_code = out_params_dict.get('p_status_code') 
                status_message = out_params_dict.get('p_status_message')

                if status_code == 0: 
                    messagebox.showinfo("Sukses", status_message)
                    self.conn.commit() 
                    return True
                else:
                    messagebox.showerror("Gagal Menambah Penghuni", status_message if status_message else "Status tidak diketahui dari SP.")
                    return False
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari Stored Procedure Tambah Penghuni (hasil SELECT tidak ditemukan).")
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
            # SP sp_PindahKamarPenghuni expects 5 parameters: 3 IN, 2 OUT.
            args_for_callproc = [nim, nomor_kamar_baru, asrama_id_baru, None, None]
            self.cursor.callproc('sp_PindahKamarPenghuni', args_for_callproc)

            out_params_dict = None
            for result in self.cursor.stored_results():
                out_params_dict = result.fetchone()
                break
            
            if out_params_dict:
                status_code = out_params_dict.get('p_status_code')
                status_message = out_params_dict.get('p_status_message')

                if status_code == 0: 
                    if status_message and "Info:" in status_message: 
                        messagebox.showinfo("Info Pindah Kamar", status_message)
                    else:
                        messagebox.showinfo("Sukses Pindah Kamar", status_message if status_message else "Operasi berhasil.")
                    self.conn.commit()
                    return True, status_message
                else:
                    messagebox.showerror("Gagal Pindah Kamar", status_message if status_message else "Status tidak diketahui dari SP.")
                    return False, status_message
            else:
                messagebox.showerror("Kesalahan SP", "Tidak dapat mengambil status dari Stored Procedure Pindah Kamar (hasil SELECT tidak ditemukan).")
                return False, "Gagal mengambil status SP."
        except mysql.connector.Error as err:
            messagebox.showerror("Kesalahan Database SP", f"Gagal memanggil sp_PindahKamarPenghuni: {err}")
            try:
                if self.conn.in_transaction: self.conn.rollback()
            except: pass
            return False, str(err)


    def update_penghuni(self, nim_original, nim_baru, nama_baru, fakultas_baru):
        """Memperbarui data penghuni (Trigger akan mencatat log)."""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return False

        updates = []
        params = []

        if nim_baru and nim_original != nim_baru:
            check_nim_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
            self.cursor.execute(check_nim_query, (nim_baru,))
            if self.cursor.fetchone():
                messagebox.showerror("Kesalahan", f"NIM baru '{nim_baru}' sudah digunakan oleh penghuni lain.")
                return False
            updates.append("nim = %s")
            params.append(nim_baru)
        if nama_baru:
            updates.append("nama_penghuni = %s")
            params.append(nama_baru)
        if fakultas_baru is not None:
            updates.append("fakultas = %s")
            params.append(fakultas_baru)

        if not updates:
            messagebox.showinfo("Info", "Tidak ada data yang diubah.")
            return True

        params.append(nim_original)
        query = f"UPDATE Penghuni SET {', '.join(updates)} WHERE nim = %s"

        success = self._execute_query(query, tuple(params), is_ddl_or_commit_managed_elsewhere=False)
        if success and self.cursor.rowcount > 0:
             messagebox.showinfo("Sukses", "Data penghuni berhasil diubah.")
             return True
        elif success and self.cursor.rowcount == 0:
             messagebox.showwarning("Perhatian", "Tidak ada data penghuni yang cocok dengan NIM original atau tidak ada perubahan aktual.")
             return False 
        return False


    def delete_penghuni(self, nim):
        """Menghapus data penghuni (Trigger akan mencatat log)."""
        success = self._execute_query("DELETE FROM Penghuni WHERE nim = %s", (nim,), is_ddl_or_commit_managed_elsewhere=False)
        if success and self.cursor.rowcount > 0:
            messagebox.showinfo("Sukses", f"Data penghuni dengan NIM {nim} berhasil dihapus.")
            return True
        elif success and self.cursor.rowcount == 0:
            messagebox.showwarning("Gagal", f"Penghuni dengan NIM {nim} tidak ditemukan.")
            return False
        return False

    def get_audit_log_penghuni(self, limit=100): 
        """Mengambil data log aktivitas penghuni dengan batasan jumlah."""
        query = """
            SELECT 
                log_id, 
                DATE_FORMAT(waktu_aksi, '%Y-%m-%d %H:%i:%S') AS waktu_aksi_formatted, 
                aksi, 
                nim, 
                IFNULL(nama_penghuni_baru, nama_penghuni_lama) AS nama_terkait,
                IF(aksi = 'INSERT', 
                   CONCAT('Ke: ', IFNULL(nomor_kamar_baru, 'N/A'), ' (', IFNULL(nama_asrama_baru, 'N/A'), ')'),
                   IF(aksi = 'DELETE',
                      CONCAT('Dari: ', IFNULL(nomor_kamar_lama, 'N/A'), ' (', IFNULL(nama_asrama_lama, 'N/A'), ')'),
                      CONCAT('Dari: ', IFNULL(nomor_kamar_lama, 'N/A'), ' (', IFNULL(nama_asrama_lama, 'N/A'), ') ke: ', IFNULL(nomor_kamar_baru, 'N/A'), ' (', IFNULL(nama_asrama_baru, 'N/A'), ')')
                   )
                ) AS detail_kamar,
                keterangan_tambahan
            FROM AuditLogAktivitasPenghuni 
            ORDER BY waktu_aksi DESC 
            LIMIT %s
        """
        return self._execute_query(query, (limit,), fetch_all=True) or []

    def __del__(self):
        self._close()