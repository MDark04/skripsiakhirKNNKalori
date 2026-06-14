import pandas as pd
import os

print("=== MULAI DIAGNOSA DATABASE ===")
file_path = 'nutrition.csv'

# 1. Cek Apakah File Ada?
if not os.path.exists(file_path):
    print("❌ ERROR FATAL: File 'nutrition.csv' TIDAK DITEMUKAN!")
    print("   Tips: Pastikan file ini ada di folder:", os.getcwd())
    print("   Tips: Cek apakah namanya 'nutrition.csv.txt'? (Windows sering menyembunyikan .txt)")
else:
    print("✅ File ditemukan.")

    # 2. Cek Apakah Bisa Dibaca & Header Benar?
    try:
        df = pd.read_csv(file_path)
        print("✅ File terbaca oleh Pandas.")
        print(f"   Jumlah Data: {len(df)} baris")
        print("   Header Kolom:", list(df.columns))

        # Cek Kolom Wajib (Harus Huruf Kecil Semua)
        wajib = ['calories', 'name', 'proteins', 'fat', 'carbohydrate', 'image']
        kurang = [col for col in wajib if col not in df.columns]

        if kurang:
            print(f"❌ ERROR HEADER: Kolom ini hilang/salah ketik: {kurang}")
            print("   Solusi: Buka CSV, ubah header jadi huruf kecil semua (bahasa Inggris).")
        else:
            print("🎉 SEMPURNA! Database aman. Masalahnya mungkin di logika KNN.")
            
    except Exception as e:
        print("❌ File ada tapi RUSAK/KOSONG. Error:", e)

print("=== SELESAI ===")