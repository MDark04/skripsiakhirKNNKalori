import os
import math
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# --- FUNGSI 1: MENGHITUNG KEBUTUHAN KALORI (BMR & TDEE) ---
def hitung_bmr_tdee(gender, berat, tinggi, usia, aktivitas):
    # Menggunakan Rumus Mifflin-St Jeor
    if gender == 'pria':
        bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) + 5
    else:
        bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) - 161
    
    faktor = {'ringan': 1.2, 'sedang': 1.55, 'berat': 1.725}
    tdee = bmr * faktor.get(aktivitas, 1.2)
    return bmr, tdee

# --- FUNGSI 2: ALGORITMA KNN MULTI-DIMENSI ---
def rekomendasi_knn(target_kalori, preferensi='', k=5):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Deteksi otomatis nama file (huruf besar/kecil)
    path_kecil = os.path.join(BASE_DIR, 'nutrition.csv')
    path_besar = os.path.join(BASE_DIR, 'Nutrition.csv')
    
    if os.path.exists(path_kecil):
        nama_file = path_kecil
    elif os.path.exists(path_besar):
        nama_file = path_besar
    else:
        print("❌ ERROR: File CSV tidak ditemukan di folder!")
        return []

    try:
        # BACA CSV: Otomatis mendeteksi pemisah (koma atau titik koma)
        df = pd.read_csv(nama_file, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
        
        # Bersihkan nama kolom dari spasi dan jadikan huruf kecil semua
        df.columns = [str(col).strip().lower() for col in df.columns]
        print(f"✅ BACA CSV BERHASIL! Nama kolom: {df.columns.tolist()}")

        # PEMETAAN KOLOM CERDAS: Menyesuaikan apapun nama kolom di file CSV kamu
        kolom_map = {}
        for col in df.columns:
            if 'name' in col or 'nama' in col or 'menu' in col: kolom_map['name'] = col
            elif 'cal' in col or 'kalori' in col or 'energi' in col: kolom_map['calories'] = col
            elif 'prot' in col: kolom_map['proteins'] = col
            elif 'carb' in col or 'karbo' in col: kolom_map['carbohydrate'] = col
            elif 'fat' in col or 'lemak' in col: kolom_map['fat'] = col

        # Ubah nama kolom di DataFrame agar seragam sesuai standar logika kita
        df.rename(columns={v: k for k, v in kolom_map.items()}, inplace=True)

        # Pastikan kolom vital ada
        if 'name' not in df.columns or 'calories' not in df.columns:
            print("❌ ERROR: Kolom 'name' / 'calories' tidak ditemukan meski sudah dipetakan.")
            return []

        # Tangani jika ada nama menu yang kosong
        df['name'] = df['name'].fillna('Menu Tanpa Nama').astype(str)

        # 1. FILTER PREFERENSI (Content-Based)
        if preferensi:
            df_filter = df[df['name'].str.contains(preferensi, case=False, na=False)].copy()
            if not df_filter.empty:
                df = df_filter
            else:
                print(f"⚠️ Preferensi '{preferensi}' tidak ditemukan, mencari di seluruh dataset.")

        # 2. TARGET GIZI (1 Porsi)
        target_protein = (target_kalori * 0.20) / 4
        target_karbo = (target_kalori * 0.50) / 4
        target_lemak = (target_kalori * 0.30) / 9

        # 3. PERHITUNGAN EUCLIDEAN DISTANCE (KNN)
        jarak_list = []
        for index, row in df.iterrows():
            try:
                # Ambil nilai gizi, jika error / NaN, anggap 0
                cal = float(row.get('calories', 0))
                prot = float(row.get('proteins', 0))
                carbo = float(row.get('carbohydrate', 0))
                fat = float(row.get('fat', 0))
                
                jarak = math.sqrt(
                    (target_kalori - cal)**2 +
                    (target_protein - prot)**2 +
                    (target_karbo - carbo)**2 +
                    (target_lemak - fat)**2
                )
                jarak_list.append(jarak)
            except Exception:
                jarak_list.append(999999) # Abaikan baris yang error
        
        df['distance'] = jarak_list
        
        # Urutkan Jarak Terdekat (K-Nearest)
        rekomendasi = df.sort_values(by='distance').head(k).copy()
        
        # 4. HITUNG AKURASI MATCHING
        akurasi_list = []
        for _, row in rekomendasi.iterrows():
            selisih = row['distance']
            skor = 100 - ((selisih / target_kalori) * 100) if target_kalori > 0 else 0
            akurasi_list.append(round(max(0, skor), 1))
            
        rekomendasi['accuracy'] = akurasi_list
        
        # Bersihkan format desimal agar tampil rapi di HTML
        for col in ['calories', 'proteins', 'carbohydrate', 'fat']:
            if col in rekomendasi.columns:
                rekomendasi[col] = pd.to_numeric(rekomendasi[col], errors='coerce').fillna(0).round(1)

        print(f"✅ KNN SELESAI! Ditemukan {len(rekomendasi)} rekomendasi.")
        return rekomendasi.to_dict(orient='records')

    except Exception as e:
        print(f"❌ ERROR FATAL DI ALGORITMA KNN: {e}")
        return []

# --- ROUTING FLASK ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        try:
            # Ambil data dari form HTML
            berat = float(request.form['berat'])
            tinggi = float(request.form['tinggi'])
            usia = int(request.form['usia'])
            gender = request.form['gender']
            aktivitas = request.form['aktivitas']
            preferensi = request.form.get('preferensi', '').strip()
            
            # Eksekusi fungsi
            bmr, tdee = hitung_bmr_tdee(gender, berat, tinggi, usia, aktivitas)
            target = tdee / 3 # Target 1 porsi makan
            
            menu = rekomendasi_knn(target, preferensi)
            
            return render_template('result.html', 
                                   bmr=int(bmr), 
                                   tdee=int(tdee),
                                   target=int(target),
                                   preferensi=preferensi,
                                   menu=menu)
        except Exception as e:
            return f"<h3>Terjadi Kesalahan Input:</h3><p>{e}</p><a href='/'>Kembali</a>"

if __name__ == '__main__':
    # Jalankan server
    app.run(debug=True)