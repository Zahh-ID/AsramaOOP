# AsramaOOP
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

5.  **`AppGui`**:
    * Kelas utama aplikasi yang menginisialisasi window Tkinter, canvas utama, `DatabaseService`, dan `ScreenManager`.
    * Bertanggung jawab untuk memuat aset (gambar) dan memulai loop utama Tkinter.

## Fitur Database yang Diterapkan

* **View**:
    * `vw_DetailKamarPenghuni`: Menyediakan ringkasan per kamar (nomor kamar, nama asrama, kapasitas, jumlah penghuni saat ini). Digunakan untuk menampilkan informasi kapasitas dan jumlah penghuni di `KamarDetailScreen`.
    * `vw_DaftarPenghuniLengkap`: Menggabungkan data dari tabel `Penghuni`, `Kamar`, dan `Asrama` untuk tampilan data penghuni yang komprehensif. Digunakan untuk mengisi tabel penghuni di `KamarDetailScreen` dan dropdown di layar ubah/hapus/pindah.
* **Stored Procedure**:
    * `sp_TambahPenghuni`: Menangani logika penambahan penghuni baru, termasuk validasi (kamar ditemukan, kapasitas kamar, NIM duplikat). Mengembalikan status operasi melalui parameter `OUT`.
    * `sp_PindahKamarPenghuni`: Menangani logika pemindahan penghuni ke kamar lain, termasuk validasi. Mengembalikan status operasi.
* **Trigger**:
    * `trg_LogInsertPenghuni`: Mencatat aktivitas ke tabel `AuditLogAktivitasPenghuni` setiap kali ada data baru dimasukkan ke tabel `Penghuni`.
    * `trg_LogUpdatePenghuni`: Mencatat aktivitas (termasuk perubahan data dan perpindahan kamar) ke tabel `AuditLogAktivitasPenghuni` setiap kali data di tabel `Penghuni` diubah.
    * `trg_LogDeletePenghuni`: Mencatat aktivitas ke tabel `AuditLogAktivitasPenghuni` setiap kali data penghuni dihapus.

## Cara Menjalankan Aplikasi

1.  **Dependensi**:
    Pastikan Anda telah menginstal library Python yang dibutuhkan:
    ```bash
    pip install Pillow mysql-connector-python
    ```

2.  **Konfigurasi Database MySQL**:
    * Pastikan server MySQL Anda berjalan.
    * Buat sebuah database baru di MySQL, misalnya dengan nama `asrama_db_mysql`.
    * Sesuaikan detail koneksi database (host, user, password, nama database) di dalam kelas `AppGui` pada file Python utama jika berbeda dari default:
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
    Pastikan semua file Python (`.py`) dan direktori `assets` (berisi `um.png`) berada dalam satu direktori utama proyek. Jika Anda memisahkan file per kelas, pastikan struktur direktori dan impor antar modul sudah benar.

5.  **Menjalankan Skrip Python**:
    Jalankan file Python utama (misalnya, `main.py` jika Anda memisahkannya, atau file tunggal yang berisi semua kode) melalui terminal:
    ```bash
    python nama_file_utama.py
    ```

## File `tombol.py`

File ini diasumsikan berisi fungsi `tbl(...)` yang bertanggung jawab untuk menggambar tombol kustom pada canvas Tkinter. Fungsi ini menerima parameter seperti posisi, ukuran, radius sudut, warna, teks, dan perintah (fungsi callback) yang akan dijalankan saat tombol diklik. Versi yang digunakan dalam aplikasi ini menggambar tombol dengan empat sudut membulat.

## Aset

* Aplikasi ini menggunakan gambar latar belakang yang diharapkan berada di direktori `./assets/um.png` relatif terhadap lokasi skrip utama dijalankan.

## Potensi Pengembangan Lebih Lanjut

* Implementasi fungsionalitas login pengguna dan pencatatan `user_aksi` di tabel log.
* Validasi input yang lebih detail dan feedback error yang lebih baik di UI.
* Fitur pencarian dan filter data penghuni.
* Manajemen data kamar dan asrama (tambah/ubah/hapus) melalui UI.
* Penggunaan tema Tkinter yang lebih modern atau kustomisasi style yang lebih mendalam.
* Pemisahan konfigurasi ke file eksternal (misalnya, `.env` atau `.ini`).
* Unit testing untuk logika bisnis dan interaksi database.

