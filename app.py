from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import os

app = Flask(__name__)


def hitung_bmr_tdee(gender, berat, tinggi, usia, aktivitas):
    if gender == 'pria':
        bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) + 5
    else:
        bmr = (10 * berat) + (6.25 * tinggi) - (5 * usia) - 161
    
    faktor = {'ringan': 1.2, 'sedang': 1.55, 'berat': 1.725}
    tdee = bmr * faktor.get(aktivitas, 1.2)
    return bmr, tdee


def rekomendasi_knn(target_kalori, k=5):
    nama_file = 'nutrition.csv'
    
    if not os.path.exists(nama_file):
        print("❌ ERROR: File nutrition.csv tidak ditemukan!")
        return []

    try:
        df = pd.read_csv(nama_file)

        df.columns = [col.lower() for col in df.columns]

        if 'calories' not in df.columns:
            print("❌ ERROR: Kolom 'calories' tidak ditemukan di CSV.")
            return []

        jarak_list = []
        for index, row in df.iterrows():
            try:
                cal = float(row['calories'])
                jarak = abs(target_kalori - cal)
                jarak_list.append(jarak)
            except ValueError:
                jarak_list.append(99999)
        
        df['distance'] = jarak_list
        rekomendasi = df.sort_values(by='distance').head(k).copy()
        akurasi_list = []
        for _, row in rekomendasi.iterrows():
            selisih = row['distance']
            if target_kalori > 0:
                persen_error = (selisih / target_kalori) * 100
                skor = 100 - persen_error
            else:
                skor = 0
            skor = max(0, skor)
            akurasi_list.append(round(skor, 1))
            
        rekomendasi['accuracy'] = akurasi_list
        
        print(f"✅ Sukses! Ditemukan {len(rekomendasi)} rekomendasi.")
        return rekomendasi.to_dict(orient='records')

    except Exception as e:
        print(f"❌ TERJADI ERROR SISTEM: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        try:
            berat = float(request.form['berat'])
            tinggi = float(request.form['tinggi'])
            usia = int(request.form['usia'])
            gender = request.form['gender']
            aktivitas = request.form['aktivitas']
            bmr, tdee = hitung_bmr_tdee(gender, berat, tinggi, usia, aktivitas)
            target = tdee / 3
            menu = rekomendasi_knn(target)
            return render_template('result.html', 
                                   bmr=int(bmr), 
                                   tdee=int(tdee),
                                   target=int(target),
                                   menu=menu)
        except Exception as e:
            return f"<h3>Terjadi Kesalahan Input:</h3><p>{e}</p><a href='/'>Kembali</a>"

if __name__ == '__main__':
    app.run(debug=True)