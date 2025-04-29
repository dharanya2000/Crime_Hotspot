from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import zipfile
import os
from sklearn.preprocessing import LabelEncoder
from folium.plugins import HeatMap
import folium
import os

app = Flask(__name__)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    extract_path = 'extracted_data'
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    zip_path = os.path.join(extract_path, file.filename)
    file.save(zip_path)
    extract_and_process_data(zip_path)
    return redirect(url_for('result'))
@app.route('/result')
def result():
    return render_template('result.html')
def extract_and_process_data(zip_path):
    extract_path = "extracted_data"
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    csv_files = [f for f in os.listdir(extract_path) if f.endswith(".csv")]
    if not csv_files:
        print("❌ ERROR: No CSV file found in ZIP archive!")
        return "No CSV file found in ZIP archive."   
    csv_path = os.path.join(extract_path, csv_files[0])
    df = pd.read_csv(csv_path)
    print("\n📌 First 5 Rows of Uploaded Dataset:")
    print(df.head())
    possible_lat_cols = ["latitude", "lat", "y", "Y", "Y.1"]
    possible_lon_cols = ["longitude", "lon", "x", "X", "X.1"]
    lat_col = next((col for col in df.columns if col in possible_lat_cols), None)
    lon_col = next((col for col in df.columns if col in possible_lon_cols), None)
    if lat_col == "Y" and "Y.1" in df.columns:
        lat_col = "Y.1"
    if lon_col == "X" and "X.1" in df.columns:
        lon_col = "X.1"
    if not lat_col or not lon_col:
        print("❌ ERROR: Missing Latitude/Longitude Columns!")
        return "Missing required latitude/longitude columns."
    print(f"✅ Correct Latitude Column: {lat_col}")
    print(f"✅ Correct Longitude Column: {lon_col}")

    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    if df[lat_col].abs().max() > 90:
        print("⚠️ WARNING: Latitude values exceed valid range! Swapping Latitude & Longitude.")
        df.rename(columns={lat_col: "temp_lon", lon_col: "temp_lat"}, inplace=True)
        df.rename(columns={"temp_lon": lon_col, "temp_lat": lat_col}, inplace=True)
    df = df[(df[lat_col].between(-90, 90)) & (df[lon_col].between(-180, 180))]
    if df.empty:
        print("❌ ERROR: No valid latitude/longitude coordinates found!")
        return "Error: No valid latitude/longitude coordinates found."
    df.loc[(df[lat_col] == 0) & (df[lon_col] == 0), [lat_col, lon_col]] = None
    df = df.dropna(subset=[lat_col, lon_col])

    if df.empty:
        print("❌ ERROR: After fixing (0,0), no valid points remain!")
        return "Error: After fixing (0,0), no valid points remain."
    
    print("\n📌 Sample Coordinates (After Cleaning):")
    print(df[[lat_col, lon_col]].head(5))
    heatmap_path = "static/crime_hotspots.html"
    if os.path.exists(heatmap_path):
        os.remove(heatmap_path)
        print("🗑️ Old heatmap deleted.")
    # 🔹 Generate a new heatmap
    crime_map = folium.Map(location=[df[lat_col].mean(), df[lon_col].mean()], zoom_start=10)
    heat_data = df[[lat_col, lon_col]].dropna().values.tolist()
    HeatMap(heat_data, radius=15).add_to(crime_map)
    crime_map.save(heatmap_path)
    print("✅ New Heatmap Generated Successfully!\n")


if __name__ == '__main__':
     app.run(debug=True, use_reloader=False)