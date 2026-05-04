import urllib.request
import urllib.parse
import json

def test_overpass():
    url = "https://overpass-api.de/api/interpreter"
    
    # Gunakan area sangat kecil agar cepat (sekitar 100 meter)
    # south, west, north, east
    s, w, n, e = -6.2010, 106.8000, -6.2000, 106.8010
    
    query = f"""[out:json][timeout:30];(way["highway"]({s},{w},{n},{e}););(._;>;);out body;"""
    
    data = urllib.parse.urlencode({'data': query}).encode()
    
    headers = {
        'User-Agent': 'NavigasiIndonesia/1.1',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    print("Sedang mengirim request ke Overpass...")
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode())
            count = len(res_data.get('elements', []))
            print(f"Status: SUCCESS")
            print(f"Jumlah elemen yang diterima: {count}")
            if count > 0:
                print("Contoh data pertama:", res_data['elements'][0].get('tags', 'Node (No Tags)'))
    except Exception as e:
        print(f"Status: FAILED")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_overpass()
