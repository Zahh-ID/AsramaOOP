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
        self._host = host  # Diubah menjadi private
        self._user = user  # Diubah menjadi private
        self._password = password # Diubah menjadi private
        self._database_name = database_name # Diubah menjadi private
        self._conn = None # Diubah menjadi private
        self._cursor = None # Diubah menjadi private
        self._connect()
        if self._conn: # Menggunakan atribut private
            self._create_main_tables_if_not_exist() 
            self._ensure_log_table_exists() 

    def _connect(self):
        """Membuat koneksi ke database MySQL."""
        try:
            self._conn = mysql.connector.connect(
                host=self._host, # Menggunakan atribut private
                user=self._user, # Menggunakan atribut private
                password=self._password # Menggunakan atribut private
                # Database akan dipilih setelah dibuat jika belum ada
            )
            self._cursor = self._conn.cursor(dictionary=True) # Menggunakan atribut private
            self._cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self._database_name}") # Menggunakan atribut private
            self._cursor.execute(f"USE {self._database_name}") # Menggunakan atribut private
            print(f"Berhasil terhubung ke database MySQL dan menggunakan database '{self._database_name}'.")
        except mysql.connector.Error as err:
            print(f"Kesalahan koneksi database MySQL: {err}")
            messagebox.showerror("Kesalahan Database", f"Tidak dapat terhubung ke MySQL: {err}\n\nPastikan server MySQL berjalan dan detail koneksi benar.")
            self._conn = None
            self._cursor = None

    def _close(self):
        """Menutup koneksi database."""
        if self._cursor: # Menggunakan atribut private
            self._cursor.close()
        if self._conn and self._conn.is_connected(): # Menggunakan atribut private
            self._conn.close()
            print("Koneksi MySQL ditutup.")

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False, is_ddl_or_commit_managed_elsewhere=False): 
        """Helper untuk eksekusi kueri dengan error handling."""
        if not self._conn or not self._conn.is_connected(): # Menggunakan atribut private
            print("Kesalahan Database: Tidak ada koneksi ke database MySQL.")
            return None if fetch_one or fetch_all else False
        try:
            self._cursor.execute(query, params) # Menggunakan atribut private
            if not is_ddl_or_commit_managed_elsewhere and \
               query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                self._conn.commit() # Menggunakan atribut private
            if fetch_one:
                return self._cursor.fetchone() # Menggunakan atribut private
            if fetch_all:
                return self._cursor.fetchall() # Menggunakan atribut private
            return True
        except mysql.connector.Error as err:
            print(f"Kesalahan kueri MySQL: {err}\nKueri: {query}\nParams: {params}")
            messagebox.showerror("Kesalahan Kueri Database", f"Terjadi kesalahan saat menjalankan kueri: {err}")
            if not is_ddl_or_commit_managed_elsewhere: 
                 try:
                    if self._conn.in_transaction:  # Menggunakan atribut private
                        self._conn.rollback() # Menggunakan atribut private
                 except mysql.connector.Error as rb_err:
                    print(f"Kesalahan saat rollback: {rb_err}")
            return None if fetch_one or fetch_all else False

    def _create_main_tables_if_not_exist(self):
        """Membuat tabel utama jika belum ada. View, SP, Trigger harus dibuat di server."""
        if not self._conn or not self._conn.is_connected(): return # Menggunakan atribut private
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
            ) ENGINE=InnoDB;"""
        ]
        try:
            for ddl in tables_ddl:
                self._execute_query(ddl, is_ddl_or_commit_managed_elsewhere=True) 
            self._conn.commit()  # Menggunakan atribut private
            print("Tabel utama Asrama, Fakultas, Kamar, Penghuni telah diperiksa/dibuat.")
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
            self._conn.commit()  # Menggunakan atribut private
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

    # --- Metode untuk Fakultas ---
    def get_all_fakultas(self):
        """Mengambil semua data fakultas untuk dropdown."""
        query = "SELECT fakultas_id, nama_fakultas FROM Fakultas ORDER BY nama_fakultas ASC"
        return self._execute_query(query, fetch_all=True) or [] 

    def get_fakultas_id_by_name(self, nama_fakultas):
        """Mendapatkan fakultas_id berdasarkan nama_fakultas."""
        if not nama_fakultas: return None
        query = "SELECT fakultas_id FROM Fakultas WHERE nama_fakultas = %s"
        result = self._execute_query(query, (nama_fakultas,), fetch_one=True) 
        return result['fakultas_id'] if result else None

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

    def add_penghuni(self, nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val):
        """Menambahkan penghuni baru menggunakan Stored Procedure sp_TambahPenghuni."""
        if not self._conn or not self._conn.is_connected(): # Menggunakan atribut private
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return False
        try:
            proc_args_list = [nim, nama, nama_fakultas, nomor_kamar_val, asrama_id_val, 0, ""] 
            
            self._cursor.callproc('sp_TambahPenghuni', proc_args_list) # Menggunakan atribut private
            
            status_code = proc_args_list[5] 
            status_message = proc_args_list[6]

            if status_code is not None: 
                if status_code == 0: 
                    messagebox.showinfo("Sukses", status_message)
                    self._conn.commit()  # Menggunakan atribut private
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
                if self._conn.in_transaction: self._conn.rollback() # Menggunakan atribut private
            except: pass
            return False

    def pindah_kamar_penghuni(self, nim, nomor_kamar_baru, asrama_id_baru):
        """Memindahkan penghuni ke kamar lain menggunakan Stored Procedure sp_PindahKamarPenghuni."""
        if not self._conn or not self._conn.is_connected(): # Menggunakan atribut private
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return False, "Tidak ada koneksi database."
        try:
            proc_args_list = [nim, nomor_kamar_baru, asrama_id_baru, 0, ""] 

            self._cursor.callproc('sp_PindahKamarPenghuni', proc_args_list) # Menggunakan atribut private
            status_code = proc_args_list[3]
            status_message = proc_args_list[4]

            if status_code is not None: 
                if status_code == 0: 
                    if status_message and "Info:" in status_message: 
                        messagebox.showinfo("Info Pindah Kamar", status_message)
                    else:
                        messagebox.showinfo("Sukses Pindah Kamar", status_message if status_message else "Operasi berhasil.")
                    self._conn.commit() # Menggunakan atribut private
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
                if self._conn.in_transaction: self._conn.rollback() # Menggunakan atribut private
            except: pass
            return False, str(err)


    def update_penghuni(self, nim_original, nim_baru, nama_baru, nama_fakultas_baru):
        """Memperbarui data penghuni (Trigger akan mencatat log)."""
        if not self._conn or not self._conn.is_connected(): # Menggunakan atribut private
            messagebox.showerror("Kesalahan Database", "Tidak ada koneksi ke database MySQL.")
            return "ERROR_CONNECTION" 

        check_exists_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
        self._cursor.execute(check_exists_query, (nim_original,)) # Menggunakan atribut private
        if not self._cursor.fetchone(): # Menggunakan atribut private
            messagebox.showwarning("Perhatian", f"Tidak ada data penghuni yang cocok dengan NIM original: {nim_original}.")
            return "ERROR_NIM_ORIGINAL_NOT_FOUND"

        updates = []
        params = []
        
        if nim_baru and nim_original != nim_baru:
            if not nim_baru.isdigit(): 
                messagebox.showerror("Kesalahan Input", "NIM baru harus berupa angka.")
                return "ERROR_INVALID_NIM_FORMAT"
            check_nim_conflict_query = "SELECT 1 FROM Penghuni WHERE nim = %s"
            self._cursor.execute(check_nim_conflict_query, (nim_baru,)) # Menggunakan atribut private
            if self._cursor.fetchone(): # Menggunakan atribut private
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
                        self._cursor.execute("INSERT INTO Fakultas (nama_fakultas) VALUES (%s)", (nama_fakultas_baru,)) # Menggunakan atribut private
                        fakultas_id_to_update = self._cursor.lastrowid  # Menggunakan atribut private
                        if fakultas_id_to_update: 
                            self._conn.commit()  # Menggunakan atribut private
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
            if self._cursor.rowcount > 0: # Menggunakan atribut private
                messagebox.showinfo("Sukses", "Data penghuni berhasil diubah.")
                return "SUCCESS_DATA_CHANGED" 
            else:
                messagebox.showwarning("Perhatian", "Tidak ada perubahan aktual pada data (data baru mungkin sama dengan data lama).")
                return "SUCCESS_NO_ACTUAL_CHANGE" 
        else:
            return "ERROR_UPDATE_FAILED"


    def delete_penghuni(self, nim):
        success = self._execute_query("DELETE FROM Penghuni WHERE nim = %s", (nim,), is_ddl_or_commit_managed_elsewhere=False) 
        if success and self._cursor.rowcount > 0: # Menggunakan atribut private
            messagebox.showinfo("Sukses", f"Data penghuni dengan NIM {nim} berhasil dihapus.")
            return True
        elif success and self._cursor.rowcount == 0: # Menggunakan atribut private
            messagebox.showwarning("Gagal", f"Penghuni dengan NIM {nim} tidak ditemukan.")
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
