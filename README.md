# Deteksi Tanda Tangan pada Gambar Ijazah

Program Python ini mendeteksi kemungkinan adanya tanda tangan pada area tertentu di gambar ijazah. Program memproses hingga 9 gambar dan membandingkan hasil dua metode thresholding: **Global Threshold** dan **Otsu**.

Deteksi dilakukan dengan teknik pengolahan citra dan aturan berdasarkan bentuk serta kepadatan tinta. Program ini tidak menggunakan model machine learning yang dilatih.

## Kebutuhan

- Python 3
- OpenCV (`opencv-python`)
- NumPy

Pasang pustaka yang diperlukan dengan perintah:

```bash
pip install opencv-python numpy
```

## Struktur folder

Secara default, program membaca gambar dari folder `contoh_ijazah` dan menyimpan hasil ke folder `hasil_ttd`.

```text
proyek/
├── deteksi_ttd.py
├── README.md
└── contoh_ijazah/
    ├── ijazah1.jpg
    ├── ijazah2.jpg
    └── ... (minimal 9 gambar)
```

Format gambar yang didukung adalah JPG, JPEG, dan PNG. Program memilih 9 gambar pertama setelah nama file diurutkan.

## Cara menjalankan

Jalankan dari terminal pada folder proyek:

```bash
python deteksi_ttd.py
```

Untuk menentukan folder gambar sendiri:

```bash
python deteksi_ttd.py nama_folder
```

Untuk menyimpan citra perantara thresholding dan morfologi:

```bash
python deteksi_ttd.py --debug
```

Untuk mengubah area yang diperiksa (ROI), berikan koordinat relatif `X0 Y0 X1 Y1` dengan nilai antara 0 dan 1:

```bash
python deteksi_ttd.py --roi 0.60 0.65 0.90 0.85
```

ROI harus memenuhi `0 <= X0 < X1 <= 1` dan `0 <= Y0 < Y1 <= 1`. Nilai bawaan program adalah `[0.60, 0.65, 0.90, 0.85]`, yaitu area sekitar kanan bawah gambar.

## Alur kerja program

1. Membaca gambar JPG, JPEG, atau PNG dari folder masukan. Program berhenti jika gambar kurang dari 9 atau folder tidak ditemukan.
2. Memutar gambar portrait 90° searah jarum jam agar menjadi landscape.
3. Memotong **Region of Interest (ROI)** berdasarkan koordinat relatif yang ditentukan.
4. Mengubah ROI dari format warna BGR menjadi grayscale.
5. Membuat citra biner dengan dua cara:
   - **Global Threshold** menggunakan nilai ambang tetap 127.
   - **Otsu** menentukan nilai ambang secara otomatis dari distribusi intensitas piksel.
6. Menggunakan operasi morfologi untuk membantu menghilangkan garis horizontal dan vertikal, lalu menyambungkan bagian tinta yang terputus kecil.
7. Menghitung piksel foreground dan kepadatan tinta, menemukan komponen-komponen yang terhubung, serta menyaring komponen yang terlalu kecil sebagai noise.
8. Mengukur ciri komponen terbesar seperti luas, lebar, tinggi, rasio lebar terhadap tinggi, dan *extent*.
9. Menerapkan aturan untuk menentukan apakah area kemungkinan berisi tanda tangan. Hasil Global dan Otsu ditampilkan untuk dibandingkan.
10. Menyimpan potongan ROI dan gambar anotasi ke folder `hasil_ttd`. Dengan opsi `--debug`, citra biner dan hasil morfologi kedua metode juga disimpan.

## Konsep yang digunakan

- **Grayscale**: citra abu-abu dengan nilai intensitas umumnya dari 0 (hitam) sampai 255 (putih). Bentuk ini memudahkan pemisahan tinta dari kertas.
- **Thresholding**: mengelompokkan piksel menjadi foreground dan background berdasarkan nilai ambang. Program membalik hasil biner agar tinta gelap menjadi foreground (putih).
- **Global Threshold**: memakai satu nilai ambang tetap untuk seluruh ROI. Metode ini sederhana, tetapi dapat terpengaruh pencahayaan.
- **Otsu Thresholding**: memilih ambang otomatis berdasarkan histogram intensitas citra.
- **Morfologi citra**: operasi pada citra biner. *Opening* dengan kernel panjang membantu mengenali garis, sedangkan *closing* dengan kernel elips membantu menyambungkan tinta yang terputus.
- **Connected components**: mengelompokkan piksel foreground yang saling terhubung sebagai objek terpisah. Konektivitas 8 berarti piksel yang bersentuhan secara diagonal juga dianggap terhubung.
- **Rule-based classification**: klasifikasi dengan aturan yang ditentukan langsung, bukan dengan model yang belajar dari data.

## Aturan deteksi

Untuk setiap metode thresholding, program mengevaluasi lima ciri:

| Ciri | Aturan yang digunakan |
| --- | --- |
| Kepadatan tinta | Di antara 0,4% dan 25% dari luas ROI |
| Tinggi relatif | Tinggi komponen terbesar minimal 1,8 kali median tinggi komponen yang lolos penyaringan |
| Luas objek | Minimal 0,6% dari luas ROI |
| Bentuk goresan | *Extent* maksimal 0,45; *extent* adalah luas objek dibagi luas kotak pembatasnya |
| Lebar relatif | Lebar objek minimal 12% dari lebar ROI |

Hasil dinyatakan `SIGNATURE PRESENT` jika kepadatan tinta, tinggi relatif, dan bentuk goresan memenuhi aturan, serta setidaknya salah satu dari aturan luas objek atau lebar relatif terpenuhi. Skor adalah proporsi dari lima ciri yang terpenuhi, dalam rentang 0 sampai 1. Skor bukan probabilitas.

## Hasil keluaran

Untuk setiap gambar, folder `hasil_ttd` dapat berisi:

- `*_ttd_roi.png`: potongan area ROI yang dianalisis.
- `*_ttd_anotasi.png`: gambar asli dengan kotak ROI dan kotak komponen terbesar. Kotak komponen berwarna hijau jika terdeteksi dan merah jika tidak.
- Dengan `--debug`: `*_global_biner.png`, `*_global_morfologi.png`, `*_otsu_biner.png`, dan `*_otsu_morfologi.png`.

## Uji sistem dan analisis thresholding

Program sebaiknya diuji dengan dua kelompok citra: citra yang memiliki tanda tangan pada ROI dan citra yang tidak memiliki tanda tangan pada ROI. Untuk kelompok tanpa tanda tangan, gunakan gambar ijazah atau area dokumen yang sama jenisnya, tetapi pastikan area ROI memang kosong. Jalankan kedua kelompok dengan perintah yang sama, lalu cocokkan hasil program dengan kondisi sebenarnya.

### Hasil pada citra yang tersedia

Keluaran contoh yang dilampirkan berisi 9 citra dengan variasi kualitas, seperti kontras rendah, blur, noise, resolusi rendah, dan kompresi JPEG. Hasilnya:

| Citra | Global Threshold | Otsu |
| --- | --- | --- |
| `01_HighQuality_Enhanced.jpg` | PRESENT (1.00) | PRESENT (1.00) |
| `02_LowContrast.jpg` | ABSENT (0.40) | PRESENT (1.00) |
| `03_Blurred.jpg` | PRESENT (0.80) | PRESENT (1.00) |
| `04_HighNoise.jpg` | PRESENT (1.00) | PRESENT (1.00) |
| `05_LowResolution_Upsampled.jpg` | PRESENT (1.00) | PRESENT (1.00) |
| `06_Faded_Underexposed.jpg` | PRESENT (1.00) | PRESENT (1.00) |
| `07_ColorShift_WarmTint.jpg` | PRESENT (1.00) | PRESENT (1.00) |
| `08_JPEGCompression_Artifacts.jpg` | PRESENT (1.00) | PRESENT (1.00) |
| `09_CombinedDegradation.jpg` | PRESENT (1.00) | PRESENT (1.00) |

Pada sampel yang tersedia, Otsu menyatakan tanda tangan hadir di semua 9 citra. Global menyatakan hadir pada 8 citra dan tidak hadir pada `02_LowContrast.jpg`. Sampel keluaran ini tidak memuat citra tanpa tanda tangan, jadi hasil untuk kelas tanpa tanda tangan belum dapat dilaporkan sebagai hasil pengujian aktual. Untuk melengkapi pengujian dua kelas, tambahkan beberapa citra tanpa tanda tangan ke folder masukan dan bandingkan keputusan program dengan label sebenarnya. Karena program memproses 9 gambar pertama yang diurutkan berdasarkan nama file, pastikan kumpulan uji yang dijalankan berisi citra yang ingin diuji.

### Mengapa thresholding diperlukan?

ROI masih berupa citra berwarna atau grayscale yang memiliki banyak nilai intensitas. Thresholding mengubahnya menjadi citra biner: piksel yang dianggap tinta menjadi foreground, sedangkan latar kertas menjadi background. Pemisahan ini membuat program lebih mudah menghitung kepadatan tinta, mencari komponen yang terhubung, mengukur bentuk objek, dan menerapkan aturan deteksi tanda tangan.

Program menggunakan threshold inverse (`THRESH_BINARY_INV`): piksel dengan intensitas di bawah ambang menjadi putih/foreground. Global memakai ambang tetap 127, sedangkan Otsu memilih ambang dari histogram ROI. Contoh citra `02_LowContrast.jpg` memperlihatkan dampak pilihan ini: Global menghasilkan 7.283 piksel foreground, skor 0.40, dan `SIGNATURE ABSENT`; Otsu dengan ambang 198 menghasilkan 38.172 piksel foreground, skor 1.00, dan `SIGNATURE PRESENT`.

### Dampak ambang terlalu rendah atau terlalu tinggi

- **Ambang terlalu rendah:** hanya bagian yang sangat gelap yang menjadi foreground. Goresan tanda tangan yang tipis atau pudar dapat hilang atau terputus, sehingga jumlah tinta dan ukuran komponen mengecil. Akibatnya tanda tangan bisa salah dinyatakan tidak ada (*false negative*).
- **Ambang terlalu tinggi:** lebih banyak piksel abu-abu, termasuk tekstur kertas, bayangan, atau noise, ikut menjadi foreground. Objek bisa membesar atau menyatu; kepadatan tinta dapat melewati batas maksimum 25% atau bentuk komponen berubah. Hal ini bisa menyebabkan deteksi keliru (*false positive*) atau justru membuat aturan bentuk gagal.

Nilai ambang yang paling sesuai bergantung pada kontras dan pencahayaan. Otsu dapat menyesuaikan nilai ambang otomatis, tetapi hasilnya tetap perlu diperiksa, terutama pada citra dengan latar tidak rata atau noise tinggi.

## Batasan

Hasil bergantung pada posisi ROI, kualitas gambar, pencahayaan, dan nilai ambang aturan. Tanda tangan yang berada di luar ROI atau terlalu tipis dapat terlewat. Tulisan, noda, atau objek lain yang memiliki ciri serupa dapat dianggap sebagai tanda tangan. Gunakan hasil sebagai penyaringan awal dan periksa gambar anotasi secara visual.

### Hasil Keluaran lengkap terminal

Perintah yang dijalankan:

```bash
python deteksi_ttd.py "contoh_ijazah" --roi 0.60 0.65 0.90 0.85 --debug
```

Keluaran lengkap:

```text
============================================================
              DETEKSI TANDA TANGAN - 9 GAMBAR               
============================================================
Folder input : contoh_ijazah
Jumlah gambar: 9
Folder hasil : hasil_ttd

[1/9] Memproses: 01_HighQuality_Enhanced.jpg

============================================================
          GAMBAR 1/9 : 01_HighQuality_Enhanced.jpg          
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 158

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 35806 piksel
Background       : 485986 piksel
Foreground (%)   : 6.862%
Kepadatan tinta  : 6.862%
Jumlah komponen  : 21
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 38474 piksel
Background       : 483318 piksel
Foreground (%)   : 7.373%
Kepadatan tinta  : 7.373%
Jumlah komponen  : 20
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 12.53
Luas objek       : 25307 piksel
Luas / ROI       : 4.850%
Lebar objek      : 774 piksel
Tinggi objek     : 357 piksel
Aspect ratio     : 2.17
Extent           : 0.092
Lebar relatif    : 0.736

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=35806 | komponen=21 | score=1.00 | PRESENT
Otsu   : foreground=38474 | komponen=20 | score=1.00 | PRESENT

[2/9] Memproses: 02_LowContrast.jpg

============================================================
              GAMBAR 2/9 : 02_LowContrast.jpg               
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 198

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 7283 piksel
Background       : 514509 piksel
Foreground (%)   : 1.396%
Kepadatan tinta  : 1.396%
Jumlah komponen  : 7
Opening          : dilakukan
Closing          : dilakukan
Skor             : 0.40
Hasil            : SIGNATURE ABSENT

METODE OTSU
------------------------------------------------------------
Foreground       : 38172 piksel
Background       : 483620 piksel
Foreground (%)   : 7.316%
Kepadatan tinta  : 7.316%
Jumlah komponen  : 20
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 12.53
Luas objek       : 25378 piksel
Luas / ROI       : 4.864%
Lebar objek      : 774 piksel
Tinggi objek     : 357 piksel
Aspect ratio     : 2.17
Extent           : 0.092
Lebar relatif    : 0.736

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=7283 | komponen=7 | score=0.40 | ABSENT
Otsu   : foreground=38172 | komponen=20 | score=1.00 | PRESENT

[3/9] Memproses: 03_Blurred.jpg

============================================================
                GAMBAR 3/9 : 03_Blurred.jpg                 
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 200

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 11418 piksel
Background       : 510374 piksel
Foreground (%)   : 2.188%
Kepadatan tinta  : 2.188%
Jumlah komponen  : 10
Opening          : dilakukan
Closing          : dilakukan
Skor             : 0.80
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 43422 piksel
Background       : 478370 piksel
Foreground (%)   : 8.322%
Kepadatan tinta  : 8.322%
Jumlah komponen  : 34
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 8.06
Luas objek       : 9215 piksel
Luas / ROI       : 1.766%
Lebar objek      : 285 piksel
Tinggi objek     : 262 piksel
Aspect ratio     : 1.09
Extent           : 0.123
Lebar relatif    : 0.271

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=11418 | komponen=10 | score=0.80 | PRESENT
Otsu   : foreground=43422 | komponen=34 | score=1.00 | PRESENT

[4/9] Memproses: 04_HighNoise.jpg

============================================================
               GAMBAR 4/9 : 04_HighNoise.jpg                
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 165

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 33932 piksel
Background       : 487860 piksel
Foreground (%)   : 6.503%
Kepadatan tinta  : 6.503%
Jumlah komponen  : 22
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 38580 piksel
Background       : 483212 piksel
Foreground (%)   : 7.394%
Kepadatan tinta  : 7.394%
Jumlah komponen  : 21
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 12.31
Luas objek       : 25028 piksel
Luas / ROI       : 4.797%
Lebar objek      : 774 piksel
Tinggi objek     : 357 piksel
Aspect ratio     : 2.17
Extent           : 0.091
Lebar relatif    : 0.736

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=33932 | komponen=22 | score=1.00 | PRESENT
Otsu   : foreground=38580 | komponen=21 | score=1.00 | PRESENT

[5/9] Memproses: 05_LowResolution_Upsampled.jpg

============================================================
        GAMBAR 5/9 : 05_LowResolution_Upsampled.jpg         
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 182

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 23791 piksel
Background       : 498001 piksel
Foreground (%)   : 4.559%
Kepadatan tinta  : 4.559%
Jumlah komponen  : 6
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 37785 piksel
Background       : 484007 piksel
Foreground (%)   : 7.241%
Kepadatan tinta  : 7.241%
Jumlah komponen  : 29
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 10.72
Luas objek       : 10172 piksel
Luas / ROI       : 1.949%
Lebar objek      : 337 piksel
Tinggi objek     : 268 piksel
Aspect ratio     : 1.26
Extent           : 0.113
Lebar relatif    : 0.320

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=23791 | komponen=6 | score=1.00 | PRESENT
Otsu   : foreground=37785 | komponen=29 | score=1.00 | PRESENT

[6/9] Memproses: 06_Faded_Underexposed.jpg

============================================================
           GAMBAR 6/9 : 06_Faded_Underexposed.jpg           
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 123

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 38992 piksel
Background       : 482800 piksel
Foreground (%)   : 7.473%
Kepadatan tinta  : 7.473%
Jumlah komponen  : 20
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 38106 piksel
Background       : 483686 piksel
Foreground (%)   : 7.303%
Kepadatan tinta  : 7.303%
Jumlah komponen  : 19
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 12.75
Luas objek       : 25263 piksel
Luas / ROI       : 4.842%
Lebar objek      : 774 piksel
Tinggi objek     : 357 piksel
Aspect ratio     : 2.17
Extent           : 0.091
Lebar relatif    : 0.736

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=38992 | komponen=20 | score=1.00 | PRESENT
Otsu   : foreground=38106 | komponen=19 | score=1.00 | PRESENT

[7/9] Memproses: 07_ColorShift_WarmTint.jpg

============================================================
          GAMBAR 7/9 : 07_ColorShift_WarmTint.jpg           
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 165

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 33737 piksel
Background       : 488055 piksel
Foreground (%)   : 6.466%
Kepadatan tinta  : 6.466%
Jumlah komponen  : 19
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 38485 piksel
Background       : 483307 piksel
Foreground (%)   : 7.376%
Kepadatan tinta  : 7.376%
Jumlah komponen  : 20
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 12.53
Luas objek       : 25407 piksel
Luas / ROI       : 4.869%
Lebar objek      : 774 piksel
Tinggi objek     : 357 piksel
Aspect ratio     : 2.17
Extent           : 0.092
Lebar relatif    : 0.736

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=33737 | komponen=19 | score=1.00 | PRESENT
Otsu   : foreground=38485 | komponen=20 | score=1.00 | PRESENT

[8/9] Memproses: 08_JPEGCompression_Artifacts.jpg

============================================================
       GAMBAR 8/9 : 08_JPEGCompression_Artifacts.jpg        
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 172

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 31482 piksel
Background       : 490310 piksel
Foreground (%)   : 6.033%
Kepadatan tinta  : 6.033%
Jumlah komponen  : 22
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 37139 piksel
Background       : 484653 piksel
Foreground (%)   : 7.118%
Kepadatan tinta  : 7.118%
Jumlah komponen  : 20
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 11.60
Luas objek       : 17767 piksel
Luas / ROI       : 3.405%
Lebar objek      : 601 piksel
Tinggi objek     : 348 piksel
Aspect ratio     : 1.73
Extent           : 0.085
Lebar relatif    : 0.571

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=31482 | komponen=22 | score=1.00 | PRESENT
Otsu   : foreground=37139 | komponen=20 | score=1.00 | PRESENT

[9/9] Memproses: 09_CombinedDegradation.jpg

============================================================
          GAMBAR 9/9 : 09_CombinedDegradation.jpg           
============================================================

METODE THRESHOLDING
------------------------------------------------------------
Global : 127
Otsu   : 144

METODE GLOBAL THRESHOLD
------------------------------------------------------------
Foreground       : 32344 piksel
Background       : 489448 piksel
Foreground (%)   : 6.199%
Kepadatan tinta  : 6.199%
Jumlah komponen  : 23
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

METODE OTSU
------------------------------------------------------------
Foreground       : 37178 piksel
Background       : 484614 piksel
Foreground (%)   : 7.125%
Kepadatan tinta  : 7.125%
Jumlah komponen  : 22
Opening          : dilakukan
Closing          : dilakukan
Skor             : 1.00
Hasil            : SIGNATURE PRESENT

FITUR RULE-BASED
------------------------------------------------------------
Tinggi vs teks   : 13.92
Luas objek       : 18356 piksel
Luas / ROI       : 3.518%
Lebar objek      : 600 piksel
Tinggi objek     : 348 piksel
Aspect ratio     : 1.72
Extent           : 0.088
Lebar relatif    : 0.570

ATURAN
------------------------------------------------------------
  Ink       : True
  Tinggi    : True
  Luas      : True
  Stroke    : True
  Lebar     : True

PERBANDINGAN GLOBAL VS OTSU
------------------------------------------------------------
Global : foreground=32344 | komponen=23 | score=1.00 | PRESENT
Otsu   : foreground=37178 | komponen=22 | score=1.00 | PRESENT

============================================================
                     RINGKASAN 9 GAMBAR                     
============================================================
01. 01_HighQuality_Enhanced.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)
02. 02_LowContrast.jpg
    Global : SIGNATURE ABSENT (score=0.40)
    Otsu   : SIGNATURE PRESENT (score=1.00)
03. 03_Blurred.jpg
    Global : SIGNATURE PRESENT (score=0.80)
    Otsu   : SIGNATURE PRESENT (score=1.00)
04. 04_HighNoise.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)
05. 05_LowResolution_Upsampled.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)
06. 06_Faded_Underexposed.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)
07. 07_ColorShift_WarmTint.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)
08. 08_JPEGCompression_Artifacts.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)
09. 09_CombinedDegradation.jpg
    Global : SIGNATURE PRESENT (score=1.00)
    Otsu   : SIGNATURE PRESENT (score=1.00)

============================================================
[OK] Semua 9 gambar selesai diproses.
[OK] Hasil disimpan di: hasil_ttd
============================================================
```
