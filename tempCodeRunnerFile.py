#!/usr/bin/env python3
import argparse
import os
import cv2
import numpy as np

# --------------------PENGATURAN PROGRAM UNTUK TEMPAT PENYMPANAN GAMBAR DAN TEMPAT PENYIMPANAN SETELAH PROSES-----------------

FOLDER_CITRA = "contoh_ijazah"   # folder berisi 9 gambar
JUMLAH_GAMBAR = 9

# ROI: X0, Y0, X1, Y1
ROI = [0.60, 0.65, 0.90, 0.85]

HASIL_DIR = "hasil_ttd"

# ---------------------------------------MELOAD GAMBAR, ROTASI,CROP------------------------------------

# MEMUAT GAMBAR
def load_image(path):
    img = cv2.imread(path)

    if img is None:
        raise SystemExit(f"Gagal membaca gambar: {path}")

    return img

# MEMBACA 9 GAMBAR OTOMATIS
def baca_9_gambar(folder):
    ekstensi = (".jpg", ".jpeg", ".png")

    daftar = sorted(
        os.path.join(folder, nama)
        for nama in os.listdir(folder)
        if nama.lower().endswith(ekstensi)
    )

    if len(daftar) < JUMLAH_GAMBAR:
        raise SystemExit(
            f"Folder '{folder}' hanya memiliki {len(daftar)} gambar. "
            f"Harus tersedia {JUMLAH_GAMBAR} gambar."
        )

    return daftar[:JUMLAH_GAMBAR]

# ROTASI PORTRAIT -> LANDSCAPE
def rotate_to_landscape(img):
    tinggi, lebar = img.shape[:2]

    if tinggi > lebar:
        img = cv2.rotate(
            img,
            cv2.ROTATE_90_CLOCKWISE
        )

    return img

# CROP CITRA
def crop_roi(img, roi):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = roi

    return img[
        int(y0 * h):int(y1 * h),
        int(x0 * w):int(x1 * w)
    ].copy()



# ------------------------------- ANALISIS TANDA TANGAN DAN MENGONVERSI GRAYSCALE-----------------------

def analisis_ttd(roi_bgr, min_ink=0.004, max_ink=0.25):
    # Grayscale
    gray = cv2.cvtColor(
        roi_bgr,
        cv2.COLOR_BGR2GRAY
    )

    Hroi, Wroi = gray.shape
    luas_roi = Hroi * Wroi

    
    # METODE THRESHOLDING GLOBAL DAN OTSU
    # ====================================================
    # 1. METODE GLOBAL THRESHOLD
    nilai_global = 127

    _, bw_global = cv2.threshold(
        gray,
        nilai_global,
        255,
        cv2.THRESH_BINARY_INV
    )
    # 2. METODE OTSU
    nilai_otsu, bw_otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    hasil = {}

    for nama_metode, bw in [
        ("GLOBAL", bw_global),
        ("OTSU", bw_otsu)
    ]:
       
        # MORFOLOGI: CLOSING DAN CLOSING
        # ====================================================
        # 1. OPENING
        kernel_h = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (max(15, Wroi // 12), 1)
        )

        kernel_v = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, max(15, Hroi // 12))
        )

        horiz = cv2.morphologyEx(
            bw,
            cv2.MORPH_OPEN,
            kernel_h
        )

        vert = cv2.morphologyEx(
            bw,
            cv2.MORPH_OPEN,
            kernel_v
        )

        # Buang garis horizontal dan vertikal
        garis = cv2.bitwise_or(
            horiz,
            vert
        )

        tanpa_garis = cv2.subtract(
            bw,
            garis
        )

        # 2. CLOSING
        kernel_close = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (5, 5)
        )

        tanpa_garis = cv2.morphologyEx(
            tanpa_garis,
            cv2.MORPH_CLOSE,
            kernel_close
        )


        # KARAKTERISTIK LUAS SEGMENTASI
        # ====================================================

        jumlah_foreground = int(
            np.count_nonzero(tanpa_garis)
        )

        jumlah_background = int(
            tanpa_garis.size - jumlah_foreground
        )

        persentase_foreground = (
            jumlah_foreground /
            tanpa_garis.size
        ) * 100

        ink_ratio = (
            jumlah_foreground /
            luas_roi
        )

       
        # SEGMENTASI OBJEK DAN PENYARINGAN NOISE 
        # ====================================================
        n, lbl, stats, cent = cv2.connectedComponentsWithStats(
            tanpa_garis,
            connectivity=8
        )

        min_area = max(
            30,
            luas_roi * 0.0004
        )

        idx = [
            i
            for i in range(1, n)
            if stats[
                i,
                cv2.CC_STAT_AREA
            ] >= min_area
        ]

        
        # INISIALISASI FITUR
        # ====================================================

        blob = {
            "bbox": None,
            "komponen": len(idx),
            "ink_ratio": ink_ratio,
            "jumlah_foreground": jumlah_foreground,
            "jumlah_background": jumlah_background,
            "persentase_foreground": persentase_foreground,
            "tinggi_teks": 0,
            "h_ratio": 0,
            "area_frac": 0,
            "extent": 0,
            "width_frac": 0,
            "luas_objek": 0,
            "lebar_objek": 0,
            "tinggi_objek": 0,
            "aspect_ratio": 0
        }

        verdict = False
        score = 0.0


        # ANALISIS KOMPONEN TERBESAR
        # ====================================================

        if idx:
            heights = np.array([
                stats[
                    i,
                    cv2.CC_STAT_HEIGHT
                ]
                for i in idx
            ])

            tinggi_teks = float(
                np.median(heights)
            )

            cand = max(
                idx,
                key=lambda i: stats[
                    i,
                    cv2.CC_STAT_AREA
                ]
            )

            cx = stats[
                cand,
                cv2.CC_STAT_LEFT
            ]

            cy = stats[
                cand,
                cv2.CC_STAT_TOP
            ]

            cw = stats[
                cand,
                cv2.CC_STAT_WIDTH
            ]

            ch = stats[
                cand,
                cv2.CC_STAT_HEIGHT
            ]

            carea = int(
                stats[
                    cand,
                    cv2.CC_STAT_AREA
                ]
            )

            # Karakteristik objek
            h_ratio = ch / max(
                1.0,
                tinggi_teks
            )

            area_frac = carea / luas_roi

            extent = carea / max(
                1,
                cw * ch
            )

            width_frac = cw / Wroi

            aspect_ratio = cw / max(
                1,
                ch
            )

            blob.update({
                "bbox": (
                    cx,
                    cy,
                    cx + cw,
                    cy + ch
                ),
                "tinggi_teks": tinggi_teks,
                "h_ratio": h_ratio,
                "area_frac": area_frac,
                "extent": extent,
                "width_frac": width_frac,
                "luas_objek": carea,
                "lebar_objek": cw,
                "tinggi_objek": ch,
                "aspect_ratio": aspect_ratio
            })


            # ATURAN SEDERHANA
            # =================================================

            c_ink = (
                min_ink
                <= ink_ratio
                <= max_ink
            )

            c_tall = (
                h_ratio >= 1.8
            )

            c_area = (
                area_frac >= 0.006
            )

            c_stroke = (
                extent <= 0.45
            )

            c_width = (
                width_frac >= 0.12
            )

            score = float(
                np.mean([
                    c_ink,
                    c_tall,
                    c_area,
                    c_stroke,
                    c_width
                ])
            )

            verdict = bool(
                c_tall
                and c_stroke
                and c_ink
                and (c_area or c_width)
            )

            blob.update({
                "rule_ink": c_ink,
                "rule_tinggi": c_tall,
                "rule_luas": c_area,
                "rule_stroke": c_stroke,
                "rule_lebar": c_width
            })

       
        # SIMPAN HASIL METODE
        # ====================================================

        hasil[nama_metode] = {
            "threshold": (
                nilai_global
                if nama_metode == "GLOBAL"
                else nilai_otsu
            ),
            "verdict": verdict,
            "score": score,
            "blob": blob,
            "bw": bw,
            "tanpa_garis": tanpa_garis
        }

    hasil_global = hasil["GLOBAL"]
    hasil_otsu = hasil["OTSU"]

    return (
        hasil_otsu["verdict"],
        hasil_otsu["score"],
        hasil_otsu["blob"],
        {
            "bw": hasil_otsu["bw"],
            "tanpa_garis": hasil_otsu["tanpa_garis"],
            "bw_global": hasil_global["bw"],
            "tanpa_garis_global": hasil_global["tanpa_garis"],
            "hasil_global": hasil_global,
            "hasil_otsu": hasil_otsu
        }
    )


# SIMPAN HASIL SATU GAMBAR
# ============================================================

def simpan_hasil(
    nama_file,
    img,
    roi,
    dbg,
    blob,
    verdict,
    roi_coords,
    debug=False
):
    os.makedirs(
        HASIL_DIR,
        exist_ok=True
    )

    base = os.path.splitext(
        os.path.basename(nama_file)
    )[0]

    cv2.imwrite(
        os.path.join(
            HASIL_DIR,
            f"{base}_ttd_roi.png"
        ),
        roi
    )

    if debug:
        cv2.imwrite(
            os.path.join(
                HASIL_DIR,
                f"{base}_global_biner.png"
            ),
            dbg["bw_global"]
        )

        cv2.imwrite(
            os.path.join(
                HASIL_DIR,
                f"{base}_global_morfologi.png"
            ),
            dbg["tanpa_garis_global"]
        )

        cv2.imwrite(
            os.path.join(
                HASIL_DIR,
                f"{base}_otsu_biner.png"
            ),
            dbg["bw"]
        )

        cv2.imwrite(
            os.path.join(
                HASIL_DIR,
                f"{base}_otsu_morfologi.png"
            ),
            dbg["tanpa_garis"]
        )

    # Anotasi
    anot = img.copy()
    h, w = img.shape[:2]

    x0, y0, x1, y1 = roi_coords

    rx0 = int(x0 * w)
    ry0 = int(y0 * h)
    rx1 = int(x1 * w)
    ry1 = int(y1 * h)

    cv2.rectangle(
        anot,
        (rx0, ry0),
        (rx1, ry1),
        (0, 180, 255),
        4
    )

    if blob["bbox"]:
        xs, ys, xe, ye = blob["bbox"]

        warna = (
            (0, 200, 0)
            if verdict
            else (0, 0, 255)
        )

        cv2.rectangle(
            anot,
            (rx0 + xs, ry0 + ys),
            (rx0 + xe, ry0 + ye),
            warna,
            4
        )

    cv2.imwrite(
        os.path.join(
            HASIL_DIR,
            f"{base}_ttd_anotasi.png"
        ),
        anot
    )



# MENAMPILKAN HASIL SATU GAMBAR
# ============================================================
def tampilkan_hasil(
    nomor,
    nama_file,
    img,
    roi,
    dbg
):
    hasil_global = dbg["hasil_global"]
    hasil_otsu = dbg["hasil_otsu"]

    bg = hasil_global["blob"]
    bo = hasil_otsu["blob"]

    print("\n" + "=" * 60)
    print(
        f"GAMBAR {nomor}/9 : {nama_file}".center(60)
    )
    print("=" * 60)

    print("\nMETODE THRESHOLDING")
    print("-" * 60)
    print(f"Global : {hasil_global['threshold']}")
    print(f"Otsu   : {hasil_otsu['threshold']:.0f}")

    print("\nMETODE GLOBAL THRESHOLD")
    print("-" * 60)
    print(f"Foreground       : {bg['jumlah_foreground']} piksel")
    print(f"Background       : {bg['jumlah_background']} piksel")
    print(f"Foreground (%)   : {bg['persentase_foreground']:.3f}%")
    print(f"Kepadatan tinta  : {bg['ink_ratio'] * 100:.3f}%")
    print(f"Jumlah komponen  : {bg['komponen']}")
    print("Opening          : dilakukan")
    print("Closing          : dilakukan")
    print(f"Skor             : {hasil_global['score']:.2f}")
    print(
        "Hasil            : "
        + (
            "SIGNATURE PRESENT"
            if hasil_global["verdict"]
            else "SIGNATURE ABSENT"
        )
    )

    print("\nMETODE OTSU")
    print("-" * 60)
    print(f"Foreground       : {bo['jumlah_foreground']} piksel")
    print(f"Background       : {bo['jumlah_background']} piksel")
    print(f"Foreground (%)   : {bo['persentase_foreground']:.3f}%")
    print(f"Kepadatan tinta  : {bo['ink_ratio'] * 100:.3f}%")
    print(f"Jumlah komponen  : {bo['komponen']}")
    print("Opening          : dilakukan")
    print("Closing          : dilakukan")
    print(f"Skor             : {hasil_otsu['score']:.2f}")
    print(
        "Hasil            : "
        + (
            "SIGNATURE PRESENT"
            if hasil_otsu["verdict"]
            else "SIGNATURE ABSENT"
        )
    )

    print("\nFITUR RULE-BASED")
    print("-" * 60)
    print(f"Tinggi vs teks   : {bo['h_ratio']:.2f}")
    print(f"Luas objek       : {bo['luas_objek']} piksel")
    print(f"Luas / ROI       : {bo['area_frac'] * 100:.3f}%")
    print(f"Lebar objek      : {bo['lebar_objek']} piksel")
    print(f"Tinggi objek     : {bo['tinggi_objek']} piksel")
    print(f"Aspect ratio     : {bo['aspect_ratio']:.2f}")
    print(f"Extent           : {bo['extent']:.3f}")
    print(f"Lebar relatif    : {bo['width_frac']:.3f}")

    print("\nATURAN")
    print("-" * 60)
    print(f"  Ink       : {bo.get('rule_ink', False)}")
    print(f"  Tinggi    : {bo.get('rule_tinggi', False)}")
    print(f"  Luas      : {bo.get('rule_luas', False)}")
    print(f"  Stroke    : {bo.get('rule_stroke', False)}")
    print(f"  Lebar     : {bo.get('rule_lebar', False)}")

    print("\nPERBANDINGAN GLOBAL VS OTSU")
    print("-" * 60)
    print(
        f"Global : foreground={bg['jumlah_foreground']} | "
        f"komponen={bg['komponen']} | "
        f"score={hasil_global['score']:.2f} | "
        f"{'PRESENT' if hasil_global['verdict'] else 'ABSENT'}"
    )
    print(
        f"Otsu   : foreground={bo['jumlah_foreground']} | "
        f"komponen={bo['komponen']} | "
        f"score={hasil_otsu['score']:.2f} | "
        f"{'PRESENT' if hasil_otsu['verdict'] else 'ABSENT'}"
    )


# ------------------------------------- PROGRAM MAIN-------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Deteksi tanda tangan pada gambar ijazah."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=FOLDER_CITRA,
        help=f"folder gambar masukan (default: {FOLDER_CITRA})"
    )
    parser.add_argument(
        "--roi",
        nargs=4,
        type=float,
        metavar=("X0", "Y0", "X1", "Y1"),
        default=ROI,
        help="area ROI dalam koordinat relatif 0-1: X0 Y0 X1 Y1"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="simpan gambar perantara thresholding dan morfologi"
    )
    args = parser.parse_args()
    roi_coords = args.roi

    if not (
        0 <= roi_coords[0] < roi_coords[2] <= 1
        and 0 <= roi_coords[1] < roi_coords[3] <= 1
    ):
        parser.error("--roi harus memenuhi 0 <= X0 < X1 <= 1 dan 0 <= Y0 < Y1 <= 1")

    print("=" * 60)
    print(
        "DETEKSI TANDA TANGAN - 9 GAMBAR".center(60)
    )
    print("=" * 60)

    if not os.path.isdir(args.folder):
        raise SystemExit(
            f"Folder tidak ditemukan: {args.folder}"
        )

    daftar_gambar = baca_9_gambar(
        args.folder
    )

    os.makedirs(
        HASIL_DIR,
        exist_ok=True
    )

    ringkasan = []

    print(f"Folder input : {args.folder}")
    print(f"Jumlah gambar: {len(daftar_gambar)}")
    print(f"Folder hasil : {HASIL_DIR}")

   
    # MELAKUKAN PROSES 9 GAMBAR
    # ========================================================
    for nomor, berkas in enumerate(
        daftar_gambar,
        start=1
    ):
        nama_file = os.path.basename(berkas)

        print(f"\n[{nomor}/9] Memproses: {nama_file}")

        try:
            # Load
            img = load_image(berkas)

            # Rotasi
            img = rotate_to_landscape(img)

            # Crop ROI
            roi = crop_roi(
                img,
                roi_coords
            )

            # Analisis
            verdict, score, blob, dbg = analisis_ttd(
                roi
            )

            # Tampilkan hasil lengkap
            tampilkan_hasil(
                nomor,
                nama_file,
                img,
                roi,
                dbg
            )

            # Simpan hasil
            simpan_hasil(
                berkas,
                img,
                roi,
                dbg,
                blob,
                verdict,
                roi_coords,
                args.debug
            )

            hasil_global = dbg["hasil_global"]
            hasil_otsu = dbg["hasil_otsu"]

            ringkasan.append([
                nomor,
                nama_file,
                hasil_global["threshold"],
                hasil_global["blob"]["jumlah_foreground"],
                hasil_global["blob"]["komponen"],
                hasil_global["score"],
                (
                    "SIGNATURE PRESENT"
                    if hasil_global["verdict"]
                    else "SIGNATURE ABSENT"
                ),
                hasil_otsu["threshold"],
                hasil_otsu["blob"]["jumlah_foreground"],
                hasil_otsu["blob"]["komponen"],
                hasil_otsu["score"],
                (
                    "SIGNATURE PRESENT"
                    if hasil_otsu["verdict"]
                    else "SIGNATURE ABSENT"
                )
            ])

        except Exception as e:
            print(
                f"[GAGAL] {nama_file}: {e}"
            )

    
    # RINGKASAN
    # ========================================================
    print("\n" + "=" * 60)
    print(
        "RINGKASAN 9 GAMBAR".center(60)
    )
    print("=" * 60)

    for data in ringkasan:
        (
            nomor,
            nama,
            threshold_global,
            fg_global,
            komponen_global,
            score_global,
            hasil_global,
            threshold_otsu,
            fg_otsu,
            komponen_otsu,
            score_otsu,
            hasil_otsu
        ) = data

        print(f"{nomor:02d}. {nama}")
        print(
            f"    Global : {hasil_global} "
            f"(score={score_global:.2f})"
        )
        print(
            f"    Otsu   : {hasil_otsu} "
            f"(score={score_otsu:.2f})"
        )


    print("\n" + "=" * 60)
    print("[OK] Semua 9 gambar selesai diproses.")
    print(f"[OK] Hasil disimpan di: {HASIL_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
