-- ==========================================================================================
-- == PEMBUATAN TABEL UTAMA ==
-- ==========================================================================================

CREATE TABLE IF NOT EXISTS Asrama (
    asrama_id INTEGER PRIMARY KEY,
    nama_asrama VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Fakultas (
    fakultas_id INT AUTO_INCREMENT PRIMARY KEY,
    nama_fakultas VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Kamar (
    kamar_id_internal INTEGER PRIMARY KEY AUTO_INCREMENT,
    nomor_kamar INTEGER NOT NULL,
    asrama_id INTEGER NOT NULL,
    kapasitas INTEGER NOT NULL DEFAULT 2,
    FOREIGN KEY (asrama_id) REFERENCES Asrama(asrama_id) ON DELETE CASCADE,
    UNIQUE (nomor_kamar, asrama_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS Penghuni (
    nim VARCHAR(50) PRIMARY KEY,
    nama_penghuni VARCHAR(255) NOT NULL,
    fakultas_id INT NULL DEFAULT NULL, -- Menggunakan ID dari tabel Fakultas
    kamar_id_internal INTEGER NOT NULL,
    FOREIGN KEY (kamar_id_internal) REFERENCES Kamar(kamar_id_internal) ON DELETE CASCADE,
    FOREIGN KEY (fakultas_id) REFERENCES Fakultas(fakultas_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ==========================================================================================
-- == PEMBUATAN TABEL LOG AKTIVITAS ==
-- ==========================================================================================

CREATE TABLE IF NOT EXISTS AuditLogAktivitasPenghuni (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    nim VARCHAR(50),
    nama_penghuni_lama VARCHAR(255) DEFAULT NULL,
    nama_penghuni_baru VARCHAR(255) DEFAULT NULL,
    fakultas_lama VARCHAR(255) DEFAULT NULL, -- Akan menyimpan nama fakultas
    fakultas_baru VARCHAR(255) DEFAULT NULL, -- Akan menyimpan nama fakultas
    kamar_id_internal_lama INT DEFAULT NULL,
    kamar_id_internal_baru INT DEFAULT NULL,
    nomor_kamar_lama INT DEFAULT NULL,
    nama_asrama_lama VARCHAR(255) DEFAULT NULL,
    nomor_kamar_baru INT DEFAULT NULL,
    nama_asrama_baru VARCHAR(255) DEFAULT NULL,
    aksi VARCHAR(10) NOT NULL COMMENT 'INSERT, UPDATE, DELETE',
    waktu_aksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    keterangan_tambahan TEXT DEFAULT NULL
) ENGINE=InnoDB;

-- ==========================================================================================
-- == PEMBUATAN VIEWS ==
-- ==========================================================================================

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

    CREATE OR REPLACE VIEW vw_DaftarPenghuniLengkap AS
    SELECT
        P.nim,
        P.nama_penghuni,
        F.nama_fakultas AS fakultas, -- Mengambil nama fakultas dari tabel Fakultas
        K.nomor_kamar,
        A.nama_asrama,
        K.asrama_id AS id_asrama_penghuni,
        A.asrama_id AS id_asrama_kamar,
        K.kamar_id_internal,
        P.fakultas_id
    FROM Penghuni P
    JOIN Kamar K ON P.kamar_id_internal = K.kamar_id_internal
    JOIN Asrama A ON K.asrama_id = A.asrama_id
    LEFT JOIN Fakultas F ON P.fakultas_id = F.fakultas_id; -- LEFT JOIN agar penghuni tanpa fakultas tetap tampil

-- ==========================================================================================
-- == PEMBUATAN TRIGGERS UNTUK LOG AKTIVITAS PENGHUNI ==
-- ==========================================================================================

DELIMITER $$

DROP TRIGGER IF EXISTS trg_LogInsertPenghuni;
$$
CREATE TRIGGER trg_LogInsertPenghuni
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
END$$

DROP TRIGGER IF EXISTS trg_LogUpdatePenghuni;
$$
CREATE TRIGGER trg_LogUpdatePenghuni
AFTER UPDATE ON Penghuni
FOR EACH ROW
BEGIN
    DECLARE v_nomor_kamar_lama INT DEFAULT NULL;
    DECLARE v_nama_asrama_lama VARCHAR(255) DEFAULT NULL;
    DECLARE v_nama_fakultas_lama VARCHAR(255) DEFAULT NULL;
    DECLARE v_nomor_kamar_baru INT DEFAULT NULL;
    DECLARE v_nama_asrama_baru VARCHAR(255) DEFAULT NULL;
    DECLARE v_nama_fakultas_baru VARCHAR(255) DEFAULT NULL;
    DECLARE v_keterangan TEXT DEFAULT 'Data penghuni diubah.';

    IF OLD.kamar_id_internal IS NOT NULL THEN
        SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar_lama, v_nama_asrama_lama
        FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id
        WHERE K.kamar_id_internal = OLD.kamar_id_internal;
    END IF;
    IF OLD.fakultas_id IS NOT NULL THEN
        SELECT nama_fakultas INTO v_nama_fakultas_lama FROM Fakultas WHERE fakultas_id = OLD.fakultas_id;
    END IF;

    IF NEW.kamar_id_internal IS NOT NULL THEN
        SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar_baru, v_nama_asrama_baru
        FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id
        WHERE K.kamar_id_internal = NEW.kamar_id_internal;
    END IF;
    IF NEW.fakultas_id IS NOT NULL THEN
        SELECT nama_fakultas INTO v_nama_fakultas_baru FROM Fakultas WHERE fakultas_id = NEW.fakultas_id;
    END IF;

    IF OLD.kamar_id_internal != NEW.kamar_id_internal THEN
        SET v_keterangan = CONCAT('Penghuni pindah dari kamar ', IFNULL(v_nomor_kamar_lama, 'N/A'), ' Asrama ', IFNULL(v_nama_asrama_lama, 'N/A'), 
                                ' ke kamar ', IFNULL(v_nomor_kamar_baru, 'N/A'), ' Asrama ', IFNULL(v_nama_asrama_baru, 'N/A'), '.');
    ELSEIF OLD.fakultas_id != NEW.fakultas_id OR (OLD.fakultas_id IS NULL AND NEW.fakultas_id IS NOT NULL) OR (OLD.fakultas_id IS NOT NULL AND NEW.fakultas_id IS NULL) THEN
        SET v_keterangan = CONCAT('Fakultas diubah dari ', IFNULL(v_nama_fakultas_lama, 'N/A'), ' menjadi ', IFNULL(v_nama_fakultas_baru, 'N/A'), '.');
    ELSEIF OLD.nama_penghuni != NEW.nama_penghuni THEN
        SET v_keterangan = CONCAT('Nama diubah dari ', OLD.nama_penghuni, ' menjadi ', NEW.nama_penghuni, '.');
    END IF;


    INSERT INTO AuditLogAktivitasPenghuni (
        nim,
        nama_penghuni_lama, nama_penghuni_baru,
        fakultas_lama, fakultas_baru,
        kamar_id_internal_lama, kamar_id_internal_baru,
        nomor_kamar_lama, nama_asrama_lama,
        nomor_kamar_baru, nama_asrama_baru,
        aksi, keterangan_tambahan
    )
    VALUES (
        OLD.nim, 
        OLD.nama_penghuni, NEW.nama_penghuni,
        v_nama_fakultas_lama, v_nama_fakultas_baru,
        OLD.kamar_id_internal, NEW.kamar_id_internal,
        v_nomor_kamar_lama, v_nama_asrama_lama,
        v_nomor_kamar_baru, v_nama_asrama_baru,
        'UPDATE', v_keterangan
    );
END$$

DROP TRIGGER IF EXISTS trg_LogDeletePenghuni;
$$
CREATE TRIGGER trg_LogDeletePenghuni
AFTER DELETE ON Penghuni
FOR EACH ROW
BEGIN
    DECLARE v_nomor_kamar INT DEFAULT NULL;
    DECLARE v_nama_asrama VARCHAR(255) DEFAULT NULL;
    DECLARE v_nama_fakultas VARCHAR(255) DEFAULT NULL;

    IF OLD.kamar_id_internal IS NOT NULL THEN
        SELECT K.nomor_kamar, A.nama_asrama INTO v_nomor_kamar, v_nama_asrama
        FROM Kamar K JOIN Asrama A ON K.asrama_id = A.asrama_id
        WHERE K.kamar_id_internal = OLD.kamar_id_internal;
    END IF;
    IF OLD.fakultas_id IS NOT NULL THEN
        SELECT nama_fakultas INTO v_nama_fakultas FROM Fakultas WHERE fakultas_id = OLD.fakultas_id;
    END IF;

    INSERT INTO AuditLogAktivitasPenghuni (
        nim, nama_penghuni_lama, fakultas_lama,
        kamar_id_internal_lama, nomor_kamar_lama, nama_asrama_lama,
        aksi, keterangan_tambahan
    )
    VALUES (
        OLD.nim, OLD.nama_penghuni, v_nama_fakultas,
        OLD.kamar_id_internal, v_nomor_kamar, v_nama_asrama,
        'DELETE', CONCAT('Penghuni dihapus dari kamar ', IFNULL(v_nomor_kamar, 'N/A'), ' Asrama ', IFNULL(v_nama_asrama, 'N/A'))
    );
END$$

DELIMITER ;

-- ==========================================================================================
-- == PEMBUATAN STORED PROCEDURES ==
-- ==========================================================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS sp_TambahPenghuni;
$$
CREATE PROCEDURE sp_TambahPenghuni (
    IN p_nim VARCHAR(50),
    IN p_nama_penghuni VARCHAR(255),
    IN p_nama_fakultas_input VARCHAR(255), 
    IN p_nomor_kamar INT,
    IN p_asrama_id INT,
    OUT p_status_code INT, 
    OUT p_status_message VARCHAR(255)
)
BEGIN
    DECLARE v_kamar_id_internal INT;
    DECLARE v_kapasitas_kamar INT;
    DECLARE v_jumlah_penghuni_saat_ini INT;
    DECLARE v_fakultas_id INT DEFAULT NULL;

    SET p_status_code = 4; 
    SET p_status_message = 'Terjadi kesalahan tidak diketahui.';

    IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN
        SET p_status_code = 5; 
        SET p_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
    ELSE
        IF p_nama_fakultas_input IS NOT NULL AND p_nama_fakultas_input != '' THEN
            SELECT fakultas_id INTO v_fakultas_id FROM Fakultas WHERE nama_fakultas = p_nama_fakultas_input;
            IF v_fakultas_id IS NULL THEN
                INSERT INTO Fakultas (nama_fakultas) VALUES (p_nama_fakultas_input);
                SET v_fakultas_id = LAST_INSERT_ID();
            END IF;
        END IF;

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
                    INSERT INTO Penghuni (nim, nama_penghuni, fakultas_id, kamar_id_internal)
                    VALUES (p_nim, p_nama_penghuni, v_fakultas_id, v_kamar_id_internal);
                    SET p_status_code = 0;
                    SET p_status_message = 'Sukses: Penghuni berhasil ditambahkan.';
                END IF;
            END IF;
        END IF;
    END IF;
    
    SELECT p_status_code, p_status_message; -- BARIS INI DIKEMBALIKAN
END$$

DROP PROCEDURE IF EXISTS sp_PindahKamarPenghuni;
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

    IF p_nim IS NULL OR p_nim = '' OR NOT (p_nim REGEXP '^[0-9]+$') THEN
        SET p_status_code = 5; 
        SET p_status_message = 'Gagal: NIM tidak valid (harus berupa angka dan tidak boleh kosong).';
    ELSE
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
                    END IF;
                END IF;
            END IF;
        END IF;
    END IF;

    SELECT p_status_code, p_status_message; -- BARIS INI DIKEMBALIKAN
END$$

DELIMITER ;

-- ==========================================================================================
-- == CONTOH INSERT DATA AWAL (JALANKAN SETELAH TABEL DIBUAT) ==
-- ==========================================================================================

INSERT IGNORE INTO Asrama (asrama_id, nama_asrama) VALUES
(1, 'Aster'), (2, 'Soka'), (3, 'Tulip'), (4, 'Edelweiss'),
(5, 'Lily'), (6, 'Dahlia'), (7, 'Melati'), (8, 'Anyelir');

INSERT IGNORE INTO Fakultas (nama_fakultas) VALUES
('Teknik'), ('Ekonomi dan Bisnis'), ('Ilmu Sosial dan Ilmu Politik'),
('Kedokteran'), ('Ilmu Budaya'), ('MIPA'), ('Ilmu Komputer'),
('Ilmu Keolahragaan'), ('Vokasi'), ('Ilmu Pendidikan');

INSERT IGNORE INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
(101, 1, 2), (102, 1, 2), (103, 1, 3), 
(201, 1, 2), (202, 1, 2), (203, 1, 2),
(301, 1, 2), (302, 1, 2), (303, 1, 2);

INSERT IGNORE INTO Kamar (nomor_kamar, asrama_id, kapasitas) VALUES
(101, 2, 2), (102, 2, 2), (103, 2, 2),
(201, 2, 2), (202, 2, 2), (203, 2, 2),
(301, 2, 2), (302, 2, 2), (303, 2, 2);

-- ... (Tambahkan data kamar untuk asrama lain jika diperlukan) ...

