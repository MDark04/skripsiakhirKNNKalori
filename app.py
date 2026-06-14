import os
import math
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# --- FUNGSI 1: MENGHITUNG KEBUTUHAN KALORI (BMR & TDEE) ---
def hitung_bmr_tdee(gender, berat, tinggi, usia, aktivitas):
    if gender == 'pria':
        bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) + 5
    else:
        bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) - 161
    
    faktor = {'ringan': 1.2, 'sedang': 1.55, 'berat': 1.725}
    tdee = bmr * faktor.get(aktivitas, 1.2)
    return bmr, tdee

# --- FUNGSI 2: ALGORITMA KNN DENGAN INTEGRASI NOTIFIKASI ERROR ---
def rekomendasi_knn(target_kalori, preferensi='', k=5):
    try:
        df = pd.read_csv('nutrition.csv', sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Pemetaan otomatis kolom database
        kolom_map = {}
        for col in df.columns:
            if 'name' in col or 'nama' in col: kolom_map['name'] = col
            elif 'cal' in col or 'kalori' in col: kolom_map['calories'] = col
            elif 'prot' in col: kolom_map['proteins'] = col
            elif 'carb' in col or 'karbo' in col: kolom_map['carbohydrate'] = col
            elif 'fat' in col or 'lemak' in col: kolom_map['fat'] = col
        df.rename(columns={v: k for k, v in kolom_map.items()}, inplace=True)
        
        for col in ['calories', 'proteins', 'carbohydrate', 'fat']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        status_preferensi = "ok"
        warning_target = False
        
        # Poin Ketiga: Validasi Filter Kategori Preferensi Makanan
        if preferensi and 'name' in df.columns:
            df_filter = df[df['name'].str.contains(preferensi, case=False, na=False)]
            if df_filter.empty:
                status_preferensi = "not_found" # Flag error jika tidak ditemukan makanan yang sesuai
            else:
                df = df_filter
        
        # Hitung target makronutrisi ideal untuk porsi tunggal (1/3 TDEE)
        target_protein = (target_kalori * 0.20) / 4
        target_karbo = (target_kalori * 0.50) / 4
        target_lemak = (target_kalori * 0.30) / 9
        
        if not df.empty:
            df['distance'] = df.apply(lambda row: math.sqrt(
                (target_kalori - row.get('calories', 0))**2 +
                (target_protein - row.get('proteins', 0))**2 +
                (target_karbo - row.get('carbohydrate', 0))**2 +
                (target_lemak - row.get('fat', 0))**2
            ), axis=1)
            
            rekomendasi = df.sort_values(by='distance').head(k).copy()
            rekomendasi['accuracy'] = (100 - (rekomendasi['distance'] / target_kalori * 100)).clip(0, 100).round(1)
            
            # Poin Keempat: Deteksi jika rekomendasi makanan terbaik berada di bawah 90% target energi
            if not rekomendasi.empty:
                top_calories = rekomendasi.iloc[0]['calories']
                if top_calories < (0.9 * target_kalori):
                    warning_target = True
                    
            return rekomendasi.to_dict(orient='records'), status_preferensi, warning_target
        return [], status_preferensi, warning_target
    except Exception as e:
        print(f"Error KNN: {e}")
        return [], "error", False

# --- ROUTING ALUR FLASK ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        # Menangkap data input form
        berat = float(request.form['berat'])
        tinggi = float(request.form['tinggi'])
        usia = int(request.form['usia'])
        gender = request.form['gender']
        aktivitas = request.form['aktivitas']
        preferensi = request.form.get('preferensi', '').strip()
        
        # Eksekusi kalkulasi kebutuhan energi dasar
        bmr, tdee = hitung_bmr_tdee(gender, berat, tinggi, usia, aktivitas)
        target = tdee / 3
        
        # Hitung angka target gram makronutrisi porsi makan untuk lembar transparansi
        target_protein = round((target * 0.20) / 4, 1)
        target_karbo = round((target * 0.50) / 4, 1)
        target_lemak = round((target * 0.30) / 9, 1)
        
        faktor_aktivitas = {'ringan': 1.2, 'sedang': 1.55, 'berat': 1.725}.get(aktivitas, 1.2)
        
        menu, status_preferensi, warning_target = rekomendasi_knn(target, preferensi)
        
        return render_template('result.html', 
                               bmr=int(bmr), tdee=int(tdee), target=int(target),
                               berat=berat, tinggi=tinggi, usia=usia, gender=gender,
                               aktivitas=aktivitas, multiplier=faktor_aktivitas,
                               target_protein=target_protein, target_karbo=target_karbo,
                               target_lemak=target_lemak, preferensi=preferensi,
                               menu=menu, status_preferensi=status_preferensi,
                               warning_target=warning_target)
    except Exception as e:
        return f"Terjadi kesalahan input data: {e}"

if __name__ == '__main__':
    app.run(debug=True)