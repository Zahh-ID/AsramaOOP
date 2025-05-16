# Aplikasi Manajemen Sistem Asrama (Desktop OOP dengan MySQL)

## Deskripsi Singkat

Aplikasi ini adalah sistem manajemen asrama berbasis desktop yang dibangun menggunakan Python dengan library Tkinter untuk antarmuka pengguna (GUI). Aplikasi ini menerapkan prinsip-prinsip Object-Oriented Programming (OOP) dan terhubung ke database MySQL untuk menyimpan dan mengelola data. Fitur utama meliputi pengelolaan data asrama, kamar, penghuni, serta pencatatan riwayat aktivitas. Aplikasi ini juga memanfaatkan fitur database tingkat lanjut seperti View, Stored Procedure, dan Trigger.

## Fitur Utama

* **Manajemen Asrama**: Pengguna dapat melihat daftar asrama.
* **Manajemen Kamar**: Pengguna dapat melihat daftar kamar per asrama.
* **Manajemen Penghuni**:
    * Menambahkan data penghuni baru ke kamar tertentu.
    * Melihat daftar penghuni dalam sebuah kamar (beserta NIM, Nama, Fakultas).
    * Mengubah data penghuni yang sudah ada.
    * Menghapus data penghuni dari kamar.
    * Memindahkan penghuni dari satu kamar ke kamar lain (bisa berbeda asrama).
* **Riwayat Aktivitas**: Menampilkan log aktivitas terkait data penghuni (INSERT, UPDATE, DELETE) yang dicatat secara otomatis oleh trigger di database.
* **Antarmuka Pengguna Grafis (GUI)**: Dibangun menggunakan Tkinter dengan tombol kustom.
* **Integrasi Database MySQL**: Semua data disimpan dan dikelola dalam database MySQL.
* **Penerapan OOP**: Kode diorganisir ke dalam kelas-kelas dengan tanggung jawab yang jelas.
* **Pemanfaatan Fitur Database**:
    * **View**: Untuk menyederhanakan kueri kompleks dalam menampilkan data.
    * **Stored Procedure**: Untuk mengenkapsulasi logika bisnis di sisi database (misalnya, penambahan penghuni, pindah kamar).
    * **Trigger**: Untuk mencatat log aktivitas secara otomatis setiap kali ada perubahan pada data penghuni.

## Struktur Kode (Kelas Utama)

Aplikasi ini dibangun dengan beberapa kelas utama yang saling berinteraksi:
1.  **`DatabaseService`**:
    * Bertanggung jawab untuk semua interaksi dengan database MySQL.
    * Mengenkapsulasi kueri SQL, pemanggilan Stored Procedure, dan koneksi database.
    * Menggunakan View (`vw_DetailKamarPenghuni`, `vw_DaftarPenghuniLengkap`) untuk pengambilan data yang lebih efisien dan terstruktur.
    * Memanggil Stored Procedure (`sp_TambahPenghuni`, `sp_PindahKamarPenghuni`) untuk operasi data yang kompleks.

2.  **`BaseScreen`**:
    * Kelas dasar abstrak untuk semua layar (screen) dalam aplikasi.
    * Menyediakan fungsionalitas umum seperti pembersihan layar, akses ke `ScreenManager` dan `DatabaseService`.
    * Mendefinisikan metode `setup_ui()` yang harus diimplementasikan oleh setiap layar turunan (polimorfisme).

3.  **Kelas Layar Turunan dari `BaseScreen`**:
    * **`MainMenuScreen`**: Tampilan menu utama aplikasi.
    * **`AsramaSelectionScreen`**: Layar untuk memilih asrama.
    * **`KamarListScreen`**: Layar untuk menampilkan daftar kamar dalam satu asrama.
    * **`KamarDetailScreen`**: Layar untuk menampilkan detail kamar, termasuk daftar penghuni dalam bentuk tabel, dan tombol-tombol operasi.
    * **`InsertDataScreen`**: Form untuk menambahkan data penghuni baru.
    * **`UpdateDataScreen`**: Form untuk mengubah data penghuni yang sudah ada.
    * **`DeleteDataScreen`**: Form untuk menghapus data penghuni.
    * **`PindahKamarScreen`**: Form untuk memindahkan penghuni ke kamar lain.
    * **`RiwayatAktivitasScreen`**: Layar untuk menampilkan log aktivitas dari tabel `AuditLogAktivitasPenghuni` menggunakan `ttk.Treeview`.

4.  **`ScreenManager`**:
    * Mengelola transisi dan tampilan antar berbagai layar aplikasi.
    * Menyimpan konteks navigasi (seperti asrama yang sedang aktif).

5.  **`App`**:
    * Kelas utama aplikasi yang menginisialisasi window Tkinter, canvas utama, `DatabaseService`, dan `ScreenManager`.
    * Bertanggung jawab untuk memuat aset (gambar) dan memulai loop utama Tkinter.

## Detail Penerapan Konsep OOP

Konsep-konsep Object-Oriented Programming (OOP) yang diterapkan dalam aplikasi ini meliputi:

### 1. Enkapsulasi (Encapsulation)
Enkapsulasi adalah mekanisme membungkus data (atribut) dan metode (fungsi yang beroperasi pada data tersebut) menjadi satu unit tunggal yang disebut objek (atau kelas sebagai cetak birunya). Ini juga sering melibatkan penyembunyian detail implementasi internal dari dunia luar, hanya mengekspos antarmuka (metode publik) yang diperlukan.

* **`DatabaseService`**:
    * **Data yang dibungkus**: Detail koneksi MySQL (`host`, `user`, `password`, `database_name`), objek koneksi (`self.conn`), dan objek cursor (`self.cursor`).
    * **Metode yang dibungkus**: Semua logika untuk berinteraksi dengan database (`_connect`, `get_all_asrama`, `add_penghuni`, dll.).
    * **Penyembunyian Detail**: Kelas lain tidak perlu tahu bagaimana kueri SQL ditulis atau bagaimana transaksi dikelola. Mereka hanya memanggil metode publik seperti `db_service.add_penghuni(...)`.

* **`App`**:
    * **Data yang dibungkus**: Window Tkinter (`self.window`), canvas (`self.canvas`), instance `DatabaseService` dan `ScreenManager`.
    * **Metode yang dibungkus**: Logika inisialisasi aplikasi, pemuatan aset, penggambaran background, dan penutupan aplikasi.

* **`ScreenManager`**:
    * **Data yang dibungkus**: Referensi ke `App`, `DatabaseService`, layar aktif saat ini (`self.current_screen_instance`), dan konteks navigasi.
    * **Metode yang dibungkus**: Logika untuk menampilkan dan mengganti layar. Kelas layar hanya memanggil metode navigasi di `ScreenManager`.

* **Kelas Layar (turunan `BaseScreen`)**:
    * Setiap layar (misalnya, `InsertDataScreen`) mengenkapsulasi elemen UI (widget Tkinter) dan logika spesifiknya (misalnya, `_save_data` untuk menyimpan data dari form).

### 2. Pewarisan (Inheritance)
Pewarisan memungkinkan sebuah kelas (kelas anak) untuk mewarisi atribut dan metode dari kelas lain (kelas induk). Ini mempromosikan penggunaan kembali kode.

* **`BaseScreen` dan Kelas Layar Spesifik**:
    * `BaseScreen` adalah kelas induk yang mendefinisikan fungsionalitas umum untuk semua layar (misalnya, `clear_screen_elements()`, akses ke `db_service` dan `screen_manager`).
    * Kelas seperti `MainMenuScreen`, `InsertDataScreen`, dll., adalah kelas anak yang mewarisi dari `BaseScreen`. Mereka mendapatkan fungsionalitas dasar dan hanya perlu mengimplementasikan UI dan logika unik mereka di metode `setup_ui()`.

### 3. Polimorfisme (Polymorphism)
Polimorfisme ("banyak bentuk") adalah kemampuan objek dari kelas yang berbeda untuk merespons panggilan metode yang sama dengan cara yang spesifik untuk kelas mereka.

* **Metode `setup_ui()` pada Kelas Layar**:
    * `BaseScreen` mendefinisikan `setup_ui()` sebagai metode yang harus diimplementasikan oleh kelas anak (`raise NotImplementedError`).
    * Setiap kelas layar turunan (misalnya, `MainMenuScreen`, `KamarDetailScreen`) menyediakan implementasi `setup_ui()` yang berbeda untuk membangun antarmuka pengguna spesifiknya.
    * Ketika `ScreenManager` memanggil `self.current_screen_instance.setup_ui()`, versi `setup_ui()` yang sesuai dengan tipe objek layar saat itu akan dieksekusi. `ScreenManager` tidak perlu tahu tipe spesifik layar tersebut untuk memanggil metode ini.

## Detail Penerapan Fitur Database

Aplikasi ini memanfaatkan beberapa fitur database MySQL untuk meningkatkan fungsionalitas dan integritas data:

### 1. View
View adalah tabel virtual yang isinya didefinisikan oleh sebuah kueri SQL.
* **`vw_DetailKamarPenghuni`**:
    * **Definisi SQL**: Menggabungkan informasi dari tabel `Kamar` dan `Asrama`, serta menghitung jumlah penghuni saat ini per kamar menggunakan subquery.
        ```sql
        CREATE OR REPLACE VIEW vw_DetailKamarPenghuni AS
        SELECT
            K.nomor_kamar, A.nama_asrama, K.asrama_id, K.kapasitas,
            (SELECT COUNT(*) FROM Penghuni P WHERE P.kamar_id_internal = K.kamar_id_internal) AS jumlah_penghuni_sekarang,
            K.kamar_id_internal
        FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id;
        ```
    * **Penggunaan di Python (`DatabaseService`)**: Metode `get_kapasitas_kamar` dan `get_jumlah_penghuni` menggunakan view ini untuk menyederhanakan pengambilan data ringkasan kamar.

* **`vw_DaftarPenghuniLengkap`**:
    * **Definisi SQL**: Menggabungkan data dari tabel `Penghuni`, `Kamar`, dan `Asrama` untuk menampilkan detail lengkap setiap penghuni termasuk nama kamar dan asramanya.
        ```sql
        CREATE OR REPLACE VIEW vw_DaftarPenghuniLengkap AS
        SELECT
            P.nim, P.nama_penghuni, P.fakultas, K.nomor_kamar, A.nama_asrama,
            K.asrama_id AS id_asrama_penghuni, A.asrama_id AS id_asrama_kamar, K.kamar_id_internal
        FROM Penghuni P
        JOIN Kamar K ON P.kamar_id_internal = K.kamar_id_internal
        JOIN Asrama A ON K.asrama_id = A.asrama_id;
        ```
    * **Penggunaan di Python (`DatabaseService`)**: Metode `get_penghuni_in_kamar` menggunakan view ini untuk mengisi tabel daftar penghuni di `KamarDetailScreen` dan dropdown di layar lain.

### 2. Stored Procedure
Stored Procedure adalah sekumpulan pernyataan SQL yang disimpan di server database dan dapat dipanggil berdasarkan namanya.
* **`sp_TambahPenghuni`**:
    * **Definisi SQL**: Menerima parameter IN (nim, nama, fakultas, nomor kamar, id asrama) dan parameter OUT (status_code, status_message). Melakukan validasi (kamar ditemukan, kapasitas tidak penuh, NIM tidak duplikat) sebelum melakukan `INSERT` ke tabel `Penghuni`. Mengembalikan status operasi melalui parameter `OUT`. Diakhiri dengan `SELECT p_status_code, p_status_message;` untuk memudahkan pengambilan nilai `OUT` di Python.
    ```sql
    DELIMITER $$
    $$
    CREATE PROCEDURE sp_TambahPenghuni (
        IN p_nim VARCHAR(50),
        IN p_nama_penghuni VARCHAR(255),
        IN p_fakultas VARCHAR(255),
        IN p_nomor_kamar INT,
        IN p_asrama_id INT,
        OUT p_status_code INT, 
        OUT p_status_message VARCHAR(255)
    )
    BEGIN
        DECLARE v_kamar_id_internal INT;
        DECLARE v_kapasitas_kamar INT;
        DECLARE v_jumlah_penghuni_saat_ini INT;

        SET p_status_code = 4; -- Default error
        SET p_status_message = 'Terjadi kesalahan tidak diketahui.';

        SELECT kamar_id_internal INTO v_kamar_id_internal
        FROM Kamar
        WHERE nomor_kamar = p_nomor_kamar AND asrama_id = p_asrama_id;

        IF v_kamar_id_internal IS NULL THEN
            SET p_status_code = 1;
            SET p_status_message = 'Gagal: Kamar tidak ditemukan.';
        ELSE
            SELECT kapasitas INTO v_kapasitas_kamar FROM Kamar WHERE kamar_id_internal = v_kamar_id_internal;
            SELECT COUNT(*) INTO v_jumlah_penghuni_saat_ini FROM Penghuni WHERE kamar_id_internal = v_kamar_id_internal;

            IF v_jumlah_penghuni_saat_ini >= v_kapasitas_kamar THEN
                SET p_status_code = 2;
                SET p_status_message = 'Gagal: Kamar sudah penuh.';
            ELSE
                IF EXISTS (SELECT 1 FROM Penghuni WHERE nim = p_nim) THEN
                    SET p_status_code = 3;
                    SET p_status_message = CONCAT('Gagal: NIM ', p_nim, ' sudah terdaftar.');
                ELSE
                    INSERT INTO Penghuni (nim, nama_penghuni, fakultas, kamar_id_internal)
                    VALUES (p_nim, p_nama_penghuni, p_fakultas, v_kamar_id_internal);
                    SET p_status_code = 0;
                    SET p_status_message = 'Sukses: Penghuni berhasil ditambahkan.';
                    -- Trigger trg_LogInsertPenghuni akan otomatis berjalan
                END IF;
            END IF;
        END IF;
        
        -- Pilih parameter OUT sebagai hasil akhir
        SELECT p_status_code, p_status_message;
    END$$

    $$
    CREATE PROCEDURE sp_PindahKamarPenghuni (
        IN p_nim VARCHAR(50),
        IN p_nomor_kamar_baru INT,
        IN p_asrama_id_baru INT,
        OUT p_status_code INT, 
        OUT p_status_message VARCHAR(255)
    )
    BEGIN
        DECLARE v_kamar_id_internal_lama INT;
        DECLARE v_kamar_id_internal_baru INT;
        DECLARE v_kapasitas_kamar_baru INT;
        DECLARE v_jumlah_penghuni_kamar_baru INT;
        DECLARE v_penghuni_exists INT DEFAULT 0;

        SET p_status_code = 4;
        SET p_status_message = 'Terjadi kesalahan tidak diketahui.';

        SELECT COUNT(*), kamar_id_internal INTO v_penghuni_exists, v_kamar_id_internal_lama FROM Penghuni WHERE nim = p_nim;
        
        IF v_penghuni_exists = 0 THEN
            SET p_status_code = 1;
            SET p_status_message = 'Gagal: Penghuni dengan NIM tersebut tidak ditemukan.';
        ELSE
            SELECT kamar_id_internal INTO v_kamar_id_internal_baru
            FROM Kamar
            WHERE nomor_kamar = p_nomor_kamar_baru AND asrama_id = p_asrama_id_baru;

            IF v_kamar_id_internal_baru IS NULL THEN
                SET p_status_code = 2;
                SET p_status_message = 'Gagal: Kamar tujuan tidak ditemukan.';
            ELSE
                IF v_kamar_id_internal_lama = v_kamar_id_internal_baru THEN
                    SET p_status_code = 0; 
                    SET p_status_message = 'Info: Penghuni sudah berada di kamar tujuan.';
                ELSE
                    SELECT kapasitas INTO v_kapasitas_kamar_baru FROM Kamar WHERE kamar_id_internal = v_kamar_id_internal_baru;
                    SELECT COUNT(*) INTO v_jumlah_penghuni_kamar_baru FROM Penghuni WHERE kamar_id_internal = v_kamar_id_internal_baru;

                    IF v_jumlah_penghuni_kamar_baru >= v_kapasitas_kamar_baru THEN
                        SET p_status_code = 3;
                        SET p_status_message = 'Gagal: Kamar tujuan sudah penuh.';
                    ELSE
                        UPDATE Penghuni SET kamar_id_internal = v_kamar_id_internal_baru WHERE nim = p_nim;
                        SET p_status_code = 0;
                        SET p_status_message = 'Sukses: Penghuni berhasil dipindahkan.';
                        -- Trigger trg_LogUpdatePenghuni akan otomatis berjalan
                    END IF;
                END IF;
            END IF;
        END IF;

        -- Pilih parameter OUT sebagai hasil akhir
        SELECT p_status_code, p_status_message;
    END$$

    DELIMITER ;
    ```
    * **Penggunaan di Python (`DatabaseService.add_penghuni`)**: Memanggil prosedur ini menggunakan `self.cursor.callproc()`. Hasil parameter `OUT` diambil dari `self.cursor.stored_results()` dan digunakan untuk memberikan feedback ke pengguna.

* **`sp_PindahKamarPenghuni`**:
    * **Definisi SQL**: Menerima parameter IN (nim, nomor kamar baru, id asrama baru) dan parameter OUT (status_code, status_message). Melakukan validasi (penghuni ada, kamar tujuan ada, kapasitas kamar tujuan) sebelum melakukan `UPDATE` pada `kamar_id_internal` di tabel `Penghuni`. Diakhiri dengan `SELECT p_status_code, p_status_message;`.
    * **Penggunaan di Python (`DatabaseService.pindah_kamar_penghuni`)**: Mirip dengan `add_penghuni`, memanggil prosedur dan mengambil status operasinya.

### 3. Trigger
Trigger adalah blok kode SQL yang secara otomatis dieksekusi sebagai respons terhadap event tertentu (INSERT, UPDATE, DELETE) pada tabel.
* **Tabel `AuditLogAktivitasPenghuni`**: Dibuat untuk menyimpan log semua perubahan data penghuni.
* **`trg_LogInsertPenghuni`**:
    * **Event**: `AFTER INSERT ON Penghuni`
    * **Aksi**: Mencatat data penghuni yang baru ditambahkan (NIM, nama, fakultas, detail kamar baru) ke dalam tabel `AuditLogAktivitasPenghuni` dengan aksi 'INSERT'.
* **`trg_LogUpdatePenghuni`**:
    * **Event**: `AFTER UPDATE ON Penghuni`
    * **Aksi**: Mencatat nilai lama dan baru untuk nama, fakultas, dan detail kamar penghuni yang diubah ke dalam `AuditLogAktivitasPenghuni` dengan aksi 'UPDATE'. Juga memberikan keterangan jika terjadi perpindahan kamar.
* **`trg_LogDeletePenghuni`**:
    * **Event**: `AFTER DELETE ON Penghuni`
    * **Aksi**: Mencatat data penghuni yang dihapus (NIM, nama lama, fakultas lama, detail kamar lama) ke dalam `AuditLogAktivitasPenghuni` dengan aksi 'DELETE'.
* **Penggunaan di Python**: Trigger bekerja secara otomatis di sisi database. Kode Python hanya perlu melakukan operasi DML (INSERT, UPDATE, DELETE) pada tabel `Penghuni` (baik secara langsung maupun melalui Stored Procedure), dan trigger akan terpanggil untuk mencatat log. Layar `RiwayatAktivitasScreen` kemudian menampilkan data dari tabel `AuditLogAktivitasPenghuni`.

## Cara Menjalankan Aplikasi

1.  **Dependensi**:
    Pastikan Anda telah menginstal library Python yang dibutuhkan:
    ```bash
    pip install Pillow mysql-connector-python
    ```

2.  **Konfigurasi Database MySQL**:
    * Pastikan server MySQL Anda berjalan.
    * Buat sebuah database baru di MySQL, misalnya dengan nama `asrama_db_mysql`.
    * Sesuaikan detail koneksi database (host, user, password, nama database) di dalam kelas `App` pada file Python utama jika berbeda dari default:
        ```python
        MYSQL_HOST = "localhost"
        MYSQL_USER = "root"
        MYSQL_PASSWORD = ""  # Ganti dengan password Anda jika ada
        MYSQL_DB_NAME = "asrama_db_mysql" 
        ```

3.  **Jalankan Skrip DDL SQL**:
    * Sebelum menjalankan aplikasi Python untuk pertama kali, jalankan skrip DDL SQL yang berisi perintah `CREATE TABLE` (untuk `Asrama`, `Kamar`, `Penghuni`, `AuditLogAktivitasPenghuni`), `CREATE VIEW` (untuk `vw_DetailKamarPenghuni`, `vw_DaftarPenghuniLengkap`), `CREATE TRIGGER` (untuk `trg_LogInsertPenghuni`, `trg_LogUpdatePenghuni`, `trg_LogDeletePenghuni`), dan `CREATE PROCEDURE` (untuk `sp_TambahPenghuni`, `sp_PindahKamarPenghuni`) pada server MySQL Anda. Anda bisa menggunakan tools seperti phpMyAdmin, MySQL Workbench, atau command line client MySQL.
    * (Opsional) Anda juga bisa menambahkan data awal untuk tabel `Asrama` dan `Kamar` melalui skrip SQL.

4.  **Struktur File Proyek**:
    Jika Anda memisahkan file per kelas, pastikan struktur direktori dan impor antar modul sudah benar (seperti yang didiskusikan sebelumnya, dengan `main.py` sebagai titik masuk utama). Jika menggunakan satu file, pastikan semua kelas dan fungsi ada di file tersebut.

5.  **Menjalankan Skrip Python**:
    Jalankan file Python utama (misalnya, `main.py` jika dipisah, atau file tunggal) melalui terminal:
    ```bash
    python nama_file_utama.py
    ```

## File `tombol.py`

File ini diasumsikan berisi fungsi `tbl(...)` yang bertanggung jawab untuk menggambar tombol kustom pada canvas Tkinter. Fungsi ini menerima parameter seperti posisi, ukuran, radius sudut, warna, teks, dan perintah (fungsi callback) yang akan dijalankan saat tombol diklik. Versi yang digunakan dalam aplikasi ini menggambar tombol dengan empat sudut membulat.

## Aset

* Aplikasi ini menggunakan gambar latar belakang yang diharapkan berada di direktori `./assets/um.png` relatif terhadap lokasi skrip utama dijalankan.

## Potensi Pengembangan Lebih Lanjut

* Implementasi fungsionalitas login pengguna.
* Validasi input yang lebih detail dan feedback error yang lebih baik di UI.
* Fitur pencarian dan filter data penghuni yang lebih canggih.
* Manajemen data kamar dan asrama (tambah/ubah/hapus) melalui UI.
* Penggunaan tema Tkinter yang lebih modern atau kustomisasi style yang lebih mendalam.
* Pemisahan konfigurasi ke file eksternal (misalnya, `.env` atau `.ini`).
* Unit testing untuk logika bisnis dan interaksi database.
