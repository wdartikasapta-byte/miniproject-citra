import os
import cv2
import numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Sesuaikan path Tesseract sesuai instalasi Anda

#------------------------------KONFIGURASI DAN PARAMETER GLOBAL-------------------------------------------------

# Folder yang berisi file citra/gambar ijazah masukan
FOLDER_CITRA = "contoh_ijazah"

# Teks acuan (ground truth) nomor ijazah untuk evaluasi akurasi OCR
GROUND_TRUTH = "571012022000056"

# Folder tujuan untuk menyimpan gambar hasil cropping dan filtering
OUTPUT_FOLDER = "hasil_integrasi_proyek_mini"

# Kamus koordinat relatif (ymin, ymax, xmin, xmax) untuk cropping ROI
IJAZAH_ROIS = {
    "nomor": (0.887, 0.988, 0.157, 0.314),  # Area nomor ijazah (kiri bawah)
    "ttd": (0.600, 0.850, 0.650, 0.900),    # Area tanda tangan (kanan bawah)
}

# Membuat folder output secara otomatis jika belum ada
os.makedirs(OUTPUT_FOLDER, exist_ok=True)



# -----------------------FUNGSI EVALUASI METRIK AKURASI OCR -----------------------------

def calculate_cer(reference, hypothesis):
    """
    Menghitung Character Error Rate (CER) berbasis Levenshtein Distance (Dynamic Programming).
    """
    ref, hyp = list(reference), list(hypothesis)
    dp = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=int)

    # Inisialisasi baris dan kolom pertama matriks DP
    for i in range(len(ref) + 1):
        dp[i][0] = i
    for j in range(len(hyp) + 1):
        dp[0][j] = j

    # Pengisian matriks jarak Levenshtein
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    # Menghitung rasio kesalahan karakter terhadap panjang string referensi
    return dp[len(ref)][len(hyp)] / float(len(ref)) if len(ref) > 0 else 0.0


#------------------------FUNGSI CROPPING DAN PREPROCESSING CITRA------------------------------
def crop_ijazah(img, section):
    """
    Memotong area citra berdasarkan rasio koordinat relatif dari IJAZAH_ROIS.
    """
    h, w = img.shape[:2]
    y1_rel, y2_rel, x1_rel, x2_rel = IJAZAH_ROIS[section]
    
    # Konversi koordinat relatif ke piksel absolut
    y1, y2 = int(y1_rel * h), int(y2_rel * h)
    x1, x2 = int(x1_rel * w), int(x2_rel * w)
    
    return img[y1:y2, x1:x2].copy()


def load_and_enhance_ijazah(img_path):
    """
    Membaca citra, konversi ke grayscale, perbaikan kontras dengan CLAHE, 
    dan pemotongan area ROI (nomor & ttd).
    """
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Gambar pada path '{img_path}' tidak ditemukan!")

    # Konversi ke keabu-abuan (grayscale)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Meningkatkan kontras lokal dengan CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Pemotongan ROI nomor dan tanda tangan
    crop_nomor = crop_ijazah(enhanced, "nomor")
    crop_ttd = crop_ijazah(enhanced, "ttd")

    return enhanced, crop_nomor, crop_ttd


def apply_filters(crop_nomor):
    """
    Menerapkan 4 jenis filter spasial pada potongan gambar nomor ijazah.
    """
    return {
        "Mean": cv2.blur(crop_nomor, (3, 3)), #Mean Filter untuk mengurangi noise dengan rata-rata piksel tetangga
        "Median": cv2.medianBlur(crop_nomor, 3), #Median Filter untuk mengurangi noise dengan nilai median tetangga
        "Gaussian": cv2.GaussianBlur(crop_nomor, (3, 3), 0), #Gaussian Filter untuk mengurangi noise dengan distribusi Gaussian
        "Sharpen": cv2.filter2D(
            crop_nomor,
            -1,
            np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]),
        ),
    }

# -----------------------FUNGSI PROSES CABANG (OCR, TTD & VERIFIKASI)-----------------------
def process_ocr(crop_nomor_filtered):
    """
    Cabang Nomor: Ekstraksi teks menggunakan Tesseract OCR.
    """
    custom_config = (
        r"--psm 7 -c tessedit_char_whitelist=0123456789/ABCDEFGHIJKLMNOPQRSTUVWXYZ.-"
    )
    return pytesseract.image_to_string(
        crop_nomor_filtered, config=custom_config
    ).strip()


def process_signature(crop_ttd):
    """
    Cabang TTD: Thresholding Otsu -> Operasi Morfologi -> Penghitungan Piksel.
    """
    # Thresholding Otsu Biner Inversi
    _, thresh_ttd = cv2.threshold(
        crop_ttd, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    
    kernel = np.ones((3, 3), np.uint8)
    # Operasi Morfologi Opening dan Closing
    opening_ttd = cv2.morphologyEx(thresh_ttd, cv2.MORPH_OPEN, kernel)
    morph_ttd = cv2.morphologyEx(opening_ttd, cv2.MORPH_CLOSE, kernel)

    # Menghitung piksel putih hasil morfologi
    pixel_count = cv2.countNonZero(morph_ttd)
    status_ttd = "PRESENT" if pixel_count > 500 else "ABSENT"
    
    return status_ttd, morph_ttd


def verify_ijazah(nomor_text, status_ttd, ground_truth=GROUND_TRUTH):
    """
    Penggabungan keputusan hasil verifikasi nomor dan tanda tangan.
    """
    is_nomor_valid = nomor_text == ground_truth # Memeriksa apakah teks OCR sesuai dengan ground truth
    is_ttd_valid = status_ttd == "PRESENT" # Memeriksa apakah tanda tangan terdeteksi
    # Menentukan status verifikasi akhir berdasarkan hasil pemeriksaan
    if is_nomor_valid and is_ttd_valid:
        status_verifikasi = "TERVERIFIKASI (VALID)" # Jika nomor valid dan tanda tangan terdeteksi
    elif not is_nomor_valid and not is_ttd_valid:
        status_verifikasi = "GAGAL (Nomor Salah & TTD Absen)" # Jika nomor tidak valid dan tanda tangan tidak terdeteksi
    elif not is_nomor_valid:
        status_verifikasi = "GAGAL (Nomor Tidak Sesuai)" # Jika nomor tidak valid
    else:
        status_verifikasi = "GAGAL (TTD Tidak Ditemukan)" # Jika tanda tangan tidak terdeteksi

    return status_verifikasi


# -----------------------MAIN EXECUTION-----------------------

def main():
    if not os.path.exists(FOLDER_CITRA):
        print(f"Folder '{FOLDER_CITRA}' tidak ditemukan!")
        return

    # Mengambil semua file gambar di dalam folder input
    files = [
        f
        for f in os.listdir(FOLDER_CITRA)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    # Format output tabel di terminal
    HEADER_FMT = "{:<32} | {:<8} | {:<18} | {:<6} | {:<10} | {}"
    ROW_FMT = "{:<32} | {:<8} | {:<18} | {:<6.4f} | {:<10} | {}"
    LINE_LEN = 108

    print("=" * LINE_LEN)
    print(
        HEADER_FMT.format(
            "Nama File",
            "Filter",
            "Hasil OCR",
            "CER",
            "Status TTD",
            "Hasil Verifikasi",
        )
    )
    print("=" * LINE_LEN)

    # Memproses setiap gambar ijazah
    for filename in files:
        img_path = os.path.join(FOLDER_CITRA, filename)
        base_name = os.path.splitext(filename)[0]

        # 1. Load dan Crop Citra
        _, crop_nomor, crop_ttd = load_and_enhance_ijazah(img_path)

        # 2. Eksekusi Cabang TTD & Simpan Gambar TTD
        status_ttd, morph_ttd = process_signature(crop_ttd)
        cv2.imwrite(f"{OUTPUT_FOLDER}/{base_name}_ttd_crop.png", crop_ttd)
        cv2.imwrite(f"{OUTPUT_FOLDER}/{base_name}_ttd_morfologi.png", morph_ttd)

        # 3. Eksekusi Filter & OCR pada Cabang Nomor
        filter_results = apply_filters(crop_nomor)

        for filter_name, img_filtered in filter_results.items():
            # OCR & Hitung CER
            text_ocr = process_ocr(img_filtered)
            cer_score = calculate_cer(GROUND_TRUTH, text_ocr)

            # Keputusan Akhir Verifikasi
            status_verifikasi = verify_ijazah(text_ocr, status_ttd)

            # Tampilkan ke terminal
            print(
                ROW_FMT.format(
                    filename,
                    filter_name,
                    text_ocr,
                    cer_score,
                    status_ttd,
                    status_verifikasi,
                )
            )

            # Simpan gambar nomor hasil filter
            cv2.imwrite(
                f"{OUTPUT_FOLDER}/{base_name}_nomor_{filter_name.lower()}.png",
                img_filtered,
            )

        print("-" * LINE_LEN)


if __name__ == "__main__":
    main()