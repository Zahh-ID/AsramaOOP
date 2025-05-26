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
* **Memasukkan data awal asrama dan kamar**
    ```sql
    INSERT INTO Asrama (asrama_id, nama_asrama) VALUES
    (1, 'Aster'),
    (2, 'Soka'),
    (3, 'Tulip'),
    (4, 'Edelweiss'),
    (5, 'Lily'),
    (6, 'Dahlia'),
    (7, 'Melati'),
    (8, 'Anyelir');

    -- Kamar untuk Asrama Aster (asrama_id = 1)
    INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
    (101, 1, 2), (102, 1, 2), (103, 1, 3), 
    (201, 1, 2), (202, 1, 2), (203, 1, 2),
    (301, 1, 2), (302, 1, 2), (303, 1, 2);

    -- Kamar untuk Asrama Soka (asrama_id = 2)
    INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
    (101, 2, 2), (102, 2, 2), (103, 2, 2),
    (201, 2, 2), (202, 2, 2), (203, 2, 2),
    (301, 2, 2), (302, 2, 2), (303, 2, 2);

    -- Kamar untuk Asrama Tulip (asrama_id = 3)
    INSERT INTO Kamar (nomor_kamar, asrama_id) VALUES -- Menggunakan kapasitas default (2)
    (101, 3), (102, 3), (103, 3),
    (201, 3), (202, 3), (203, 3),
    (301, 3), (302, 3), (303, 3);

    -- Kamar untuk Asrama Edelweiss (asrama_id = 4)
    INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
    (101, 4, 2), (102, 4, 2), (103, 4, 2),
    (201, 4, 2), (202, 4, 2), (203, 4, 2),
    (301, 4, 2), (302, 4, 2), (303, 4, 2);

    -- Kamar untuk Asrama Lily (asrama_id = 5)
    INSERT INTO Kamar (nomor_kamar, asrama_id) VALUES 
    (101, 5), (102, 5), (103, 5),
    (201, 5), (202, 5), (203, 5),
    (301, 5), (302, 5), (303, 5);

    -- Kamar untuk Asrama Dahlia (asrama_id = 6)
    INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
    (101, 6, 2), (102, 6, 2), (103, 6, 2),
    (201, 6, 2), (202, 6, 2), (203, 6, 2),
    (301, 6, 2), (302, 6, 2), (303, 6, 2);

    -- Kamar untuk Asrama Melati (asrama_id = 7)
    INSERT INTO Kamar (nomor_kamar, asrama_id) VALUES 
    (101, 7), (102, 7), (103, 7),
    (201, 7), (202, 7), (203, 7),
    (301, 7), (302, 7), (303, 7);

    -- Kamar untuk Asrama Anyelir (asrama_id = 8)
    INSERT INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
    (101, 8, 2), (102, 8, 2), (103, 8, 2),
    (201, 8, 2), (202, 8, 2), (203, 8, 2),
    (301, 8, 2), (302, 8, 2), (303, 8, 2);


    ```
## Implementasi Rinci Fitur Database Lanjutan

Aplikasi manajemen sistem asrama ini secara ekstensif memanfaatkan fitur-fitur database MySQL seperti View, Stored Procedure, dan Trigger untuk meningkatkan fungsionalitas, integritas data, efisiensi, dan kemudahan pengelolaan. Berikut adalah penjelasan rinci mengenai implementasi masing-masing fitur:

### 1. View (Tampilan)

**Konsep Dasar:**
View adalah objek database yang merupakan tabel virtual. Isinya tidak disimpan secara fisik melainkan didefinisikan oleh sebuah kueri SQL yang dieksekusi setiap kali view tersebut diakses. View berfungsi sebagai lapisan abstraksi, menyederhanakan kueri yang kompleks, dan dapat digunakan untuk tujuan keamanan dengan membatasi akses ke data tertentu.

**Implementasi dalam Aplikasi:**

* **`vw_DetailKamarPenghuni`**
    * **Tujuan**: Menyediakan ringkasan informasi yang sering dibutuhkan untuk setiap kamar, yaitu nomor kamar, nama asrama terkait, ID asrama, kapasitas total kamar, dan jumlah penghuni yang saat ini menempati kamar tersebut, beserta ID internal kamar. Ini menghilangkan kebutuhan untuk menulis ulang kueri join dan subquery `COUNT(*)` setiap kali informasi ini diperlukan di aplikasi.
    * **Definisi SQL**:
        ```sql
        CREATE OR REPLACE VIEW vw_DetailKamarPenghuni AS
        SELECT
            K.nomor_kamar,
            A.nama_asrama,
            K.asrama_id,
            K.kapasitas,
            (SELECT COUNT(*) FROM Penghuni P WHERE P.kamar_id_internal = K.kamar_id_internal) AS jumlah_penghuni_sekarang,
            K.kamar_id_internal
        FROM Kamar K
        JOIN Asrama A ON K.asrama_id = A.asrama_id;
        ```
    * **Penggunaan di Python (`DatabaseService`)**:
        * Metode `get_kapasitas_kamar(nomor_kamar_val, asrama_id_val)`: Mengambil kolom `kapasitas` dari view ini berdasarkan `nomor_kamar` dan `asrama_id`.
        * Metode `get_jumlah_penghuni(nomor_kamar_val, asrama_id_val)`: Mengambil kolom `jumlah_penghuni_sekarang` dari view ini.
        * **Manfaat Langsung**: Kode Python menjadi lebih bersih karena tidak perlu lagi melakukan perhitungan `COUNT(*)` secara manual atau join yang kompleks di sisi aplikasi. Cukup `SELECT` dari view.

* **`vw_DaftarPenghuniLengkap`**
    * **Tujuan**: Menyajikan daftar penghuni yang komprehensif dengan menggabungkan informasi dari tabel `Penghuni`, `Kamar` (untuk nomor kamar), `Asrama` (untuk nama asrama), dan `Fakultas` (untuk nama fakultas). View ini sangat penting untuk menampilkan daftar penghuni di `KamarDetailScreen` dan untuk mengisi dropdown pilihan mahasiswa di layar ubah, hapus, atau pindah kamar.
    * **Definisi SQL**:
        ```sql
        CREATE OR REPLACE VIEW vw_DaftarPenghuniLengkap AS
        SELECT
            P.nim,
            P.nama_penghuni,
            F.nama_fakultas AS fakultas, 
            K.nomor_kamar,
            A.nama_asrama,
            K.asrama_id AS id_asrama_penghuni,
            A.asrama_id AS id_asrama_kamar,   
            K.kamar_id_internal,
            P.fakultas_id 
        FROM Penghuni P
        JOIN Kamar K ON P.kamar_id_internal = K.kamar_id_internal
        JOIN Asrama A ON K.asrama_id = A.asrama_id
        LEFT JOIN Fakultas F ON P.fakultas_id = F.fakultas_id;
        ```
        Penggunaan `LEFT JOIN Fakultas` memastikan bahwa penghuni yang mungkin belum memiliki data fakultas (jika `fakultas_id` adalah `NULL`) tetap akan ditampilkan dalam daftar, dengan kolom fakultasnya bernilai `NULL`.
    * **Penggunaan di Python (`DatabaseService`)**:
        * Metode `get_penghuni_in_kamar(nomor_kamar_val, asrama_id_val)`: Menggunakan view ini untuk mengambil semua informasi yang diperlukan tentang penghuni di kamar tertentu, termasuk nama fakultas mereka, dengan kueri yang jauh lebih sederhana daripada melakukan semua join secara manual di Python.

### 2. Stored Procedure (Prosedur Tersimpan)

**Konsep Dasar:**
Stored Procedure adalah sekumpulan satu atau lebih pernyataan SQL yang telah di-compile dan disimpan di server database. Mereka dapat dipanggil berdasarkan nama dan dapat menerima parameter input (IN) serta mengembalikan parameter output (OUT) atau result set.

**Implementasi dalam Aplikasi:**

* **`sp_TambahPenghuni`**
    * **Tujuan**: Mengenkapsulasi seluruh logika bisnis dan validasi yang diperlukan saat menambahkan penghuni baru. Ini memastikan bahwa semua aturan diterapkan secara konsisten, terlepas dari bagaimana prosedur ini dipanggil.
    * **Parameter**:
        * `IN p_nim VARCHAR(50)`
        * `IN p_nama_penghuni VARCHAR(255)`
        * `IN p_nama_fakultas_input VARCHAR(255)` (Nama fakultas, bukan ID)
        * `IN p_nomor_kamar INT`
        * `IN p_asrama_id INT`
        * `OUT p_status_code INT` (Kode status: 0 untuk sukses, >0 untuk berbagai jenis error)
        * `OUT p_status_message VARCHAR(255)` (Pesan deskriptif mengenai hasil operasi)
    * **Logika Internal Prosedur**:
        1.  Validasi `p_nim`: Memastikan NIM tidak kosong dan hanya berisi angka menggunakan `REGEXP '^[0-9]+$'`. Jika tidak valid, set `p_status_code = 5`.
        2.  Penanganan Fakultas: Jika `p_nama_fakultas_input` diberikan, prosedur mencari `fakultas_id` di tabel `Fakultas`. Jika nama fakultas belum ada, fakultas baru akan otomatis ditambahkan ke tabel `Fakultas`, dan `fakultas_id` yang baru dibuat akan digunakan.
        3.  Pencarian Kamar: Mencari `kamar_id_internal` berdasarkan `p_nomor_kamar` dan `p_asrama_id`. Jika tidak ditemukan, set `p_status_code = 1`.
        4.  Validasi Kapasitas: Jika kamar ditemukan, periksa kapasitasnya dibandingkan dengan jumlah penghuni saat ini. Jika penuh, set `p_status_code = 2`.
        5.  Validasi Duplikasi NIM: Periksa apakah NIM yang akan ditambahkan sudah terdaftar. Jika ya, set `p_status_code = 3`.
        6.  Operasi `INSERT`: Jika semua validasi lolos, lakukan `INSERT` data penghuni baru ke tabel `Penghuni` dengan `fakultas_id` yang sesuai. Set `p_status_code = 0` dan pesan sukses.
    * **Penggunaan di Python (`DatabaseService.add_penghuni`)**:
        * Kode Python memanggil prosedur ini menggunakan `self.cursor.callproc('sp_TambahPenghuni', proc_args_list)`.
        * `proc_args_list` adalah list Python yang berisi parameter IN dan placeholder (misalnya, `0` dan `""`) untuk parameter OUT.
        * Setelah `callproc`, nilai parameter `OUT` (`status_code` dan `status_message`) dibaca langsung dari `proc_args_list` yang telah dimodifikasi oleh konektor.
        * Aplikasi menampilkan pesan berdasarkan `status_message` dan melakukan `self.conn.commit()` jika `status_code` adalah 0.

* **`sp_PindahKamarPenghuni`**
    * **Tujuan**: Mengenkapsulasi logika untuk memindahkan penghuni ke kamar lain, termasuk semua validasi yang diperlukan.
    * **Parameter**:
        * `IN p_nim VARCHAR(50)`
        * `IN p_nomor_kamar_baru INT`
        * `IN p_asrama_id_baru INT`
        * `OUT p_status_code INT`
        * `OUT p_status_message VARCHAR(255)`
    * **Logika Internal Prosedur**:
        1.  Validasi `p_nim`: Memastikan NIM tidak kosong dan hanya berisi angka. Jika tidak valid, set `p_status_code = 5`.
        2.  Pengecekan Penghuni: Verifikasi apakah penghuni dengan `p_nim` ada. Jika tidak, set `p_status_code = 1`.
        3.  Pengecekan Kamar Tujuan: Verifikasi apakah kamar tujuan (`p_nomor_kamar_baru` di `p_asrama_id_baru`) ada. Jika tidak, set `p_status_code = 2`.
        4.  Pengecekan Pindah ke Kamar Sendiri: Jika kamar tujuan sama dengan kamar saat ini, operasi dianggap info (sukses tanpa perubahan), set `p_status_code = 0`.
        5.  Validasi Kapasitas Kamar Tujuan: Jika kamar tujuan berbeda, periksa kapasitasnya. Jika penuh, set `p_status_code = 3`.
        6.  Operasi `UPDATE`: Jika semua validasi lolos, lakukan `UPDATE` pada kolom `kamar_id_internal` di tabel `Penghuni`. Set `p_status_code = 0` dan pesan sukses.
    * **Penggunaan di Python (`DatabaseService.pindah_kamar_penghuni`)**:
        * Mirip dengan `add_penghuni`, memanggil prosedur menggunakan `callproc` dan mengambil parameter `OUT` dari list argumen yang dimodifikasi. Melakukan `commit` jika berhasil.

**Manfaat Penggunaan Stored Procedure:**
* **Enkapsulasi Logika Bisnis**: Semua aturan validasi dan urutan operasi data yang kompleks terkait penambahan atau pemindahan penghuni kini terpusat di database. Ini mengurangi risiko inkonsistensi jika ada beberapa cara untuk memodifikasi data.
* **Kinerja**: Stored Procedure di-compile sekali oleh server database dan dapat dieksekusi lebih cepat daripada mengirim banyak pernyataan SQL individual dari aplikasi.
* **Keamanan**: Dengan memberikan izin `EXECUTE` pada prosedur ini kepada pengguna database aplikasi, Anda dapat mencabut izin `INSERT` atau `UPDATE` langsung ke tabel `Penghuni` atau `Fakultas`, sehingga semua modifikasi harus melalui logika yang terkontrol di dalam prosedur.
* **Mengurangi Lalu Lintas Jaringan**: Aplikasi hanya mengirim nama prosedur dan parameter input, bukan blok kode SQL yang panjang.

### 3. Trigger (Pemicu)

**Konsep Dasar:**
Trigger adalah blok kode SQL yang secara otomatis dieksekusi oleh server database sebagai respons terhadap event DML (Data Manipulation Language) tertentu (`INSERT`, `UPDATE`, `DELETE`) yang terjadi pada tabel tertentu.

**Implementasi dalam Aplikasi:**

* **Tabel `AuditLogAktivitasPenghuni`**:
    * Sebuah tabel khusus (`AuditLogAktivitasPenghuni`) dibuat untuk menyimpan catatan (log) dari semua aktivitas penting yang terjadi pada data penghuni. Kolom-kolomnya mencakup NIM, nilai lama dan baru dari data yang diubah (nama, fakultas, kamar), jenis aksi (`INSERT`, `UPDATE`, `DELETE`), waktu aksi, dan keterangan tambahan.

* **`trg_LogInsertPenghuni`**:
    * **Event**: `AFTER INSERT ON Penghuni` (berjalan setelah baris baru berhasil dimasukkan ke tabel `Penghuni`).
    * **Aksi**: Secara otomatis mengambil data penghuni yang baru dimasukkan (`NEW.nim`, `NEW.nama_penghuni`), mencari nama fakultas berdasarkan `NEW.fakultas_id`, serta detail kamar baru. Informasi ini kemudian disisipkan sebagai entri baru ke dalam tabel `AuditLogAktivitasPenghuni` dengan `aksi = 'INSERT'` dan keterangan yang relevan.

* **`trg_LogUpdatePenghuni`**:
    * **Event**: `AFTER UPDATE ON Penghuni` (berjalan setelah data pada baris yang ada di tabel `Penghuni` berhasil diubah).
    * **Aksi**: Mencatat nilai lama (`OLD.*`) dan nilai baru (`NEW.*`) untuk kolom-kolom seperti nama penghuni, nama fakultas (diambil melalui join), dan detail kamar (lama dan baru jika ada perpindahan). Informasi ini dicatat ke `AuditLogAktivitasPenghuni` dengan `aksi = 'UPDATE'`. Trigger ini juga memberikan keterangan yang lebih spesifik jika terjadi perpindahan kamar atau hanya perubahan data lainnya.

* **`trg_LogDeletePenghuni`**:
    * **Event**: `AFTER DELETE ON Penghuni` (berjalan setelah baris berhasil dihapus dari tabel `Penghuni`).
    * **Aksi**: Mencatat informasi penghuni yang dihapus (NIM, nama lama, nama fakultas lama, detail kamar lama) ke dalam `AuditLogAktivitasPenghuni` dengan `aksi = 'DELETE'`.

**Manfaat Penggunaan Trigger:**
* **Auditing Otomatis dan Komprehensif**: Setiap perubahan data penting pada tabel `Penghuni` (baik melalui Stored Procedure maupun operasi DML langsung jika diizinkan) akan secara otomatis dicatat. Ini memastikan bahwa semua modifikasi data terlacak tanpa memerlukan kode logging tambahan di sisi aplikasi Python.
* **Integritas dan Transparansi**: Menyediakan jejak audit yang jelas yang dapat digunakan untuk analisis, pelacakan masalah, atau kebutuhan kepatuhan di kemudian hari.
* **Pemisahan Tanggung Jawab**: Logika auditing sepenuhnya ditangani oleh database, memisahkan kekhawatiran ini dari logika aplikasi utama.
* **Konsistensi Log**: Karena logging dilakukan di level database, format dan kelengkapan log akan selalu konsisten.

**Interaksi Keseluruhan:**
Kode Python di `DatabaseService` berinteraksi dengan View untuk menyederhanakan pengambilan data. Untuk operasi modifikasi data yang krusial seperti menambah atau memindahkan penghuni, `DatabaseService` memanggil Stored Procedure yang sesuai. Stored Procedure ini kemudian melakukan validasi dan operasi DML. Setiap operasi DML (`INSERT`, `UPDATE`, `DELETE`) pada tabel `Penghuni` secara otomatis memicu Trigger yang relevan, yang kemudian mencatat aktivitas tersebut ke tabel `AuditLogAktivitasPenghuni`. Akhirnya, layar `RiwayatAktivitasScreen` di aplikasi Python membaca data dari tabel log ini untuk menampilkannya kepada pengguna.

Kombinasi dari struktur OOP yang baik di Python dengan pemanfaatan fitur database tingkat lanjut ini menghasilkan sebuah aplikasi yang tidak hanya fungsional tetapi juga lebih kuat, aman, dan mudah dipelihara.


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
