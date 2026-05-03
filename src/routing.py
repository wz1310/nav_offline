"""
Routing engine — load graph dari file lokal, hitung rute terpendek.
Data disimpan di app storage sebagai file .graphml
"""

import os
import pickle

# Lokasi penyimpanan data (kompatibel Android & desktop)
try:
    from android.storage import app_storage_path  # type: ignore
    DATA_DIR = app_storage_path()
except ImportError:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

GRAPH_FILE = os.path.join(DATA_DIR, "road_graph.pkl")
AREAS_FILE = os.path.join(DATA_DIR, "downloaded_areas.txt")

os.makedirs(DATA_DIR, exist_ok=True)


def data_exists() -> bool:
    """Cek apakah graph sudah pernah di-download."""
    return os.path.exists(GRAPH_FILE)


def save_graph(G) -> None:
    """Simpan graph ke disk."""
    with open(GRAPH_FILE, "wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_graph():
    """Load graph dari disk. Return None jika belum ada."""
    if not data_exists():
        return None
    with open(GRAPH_FILE, "rb") as f:
        return pickle.load(f)


def find_route(G, orig_lat: float, orig_lon: float,
               dest_lat: float, dest_lon: float) -> dict:
    """
    Hitung rute terpendek antara dua koordinat.

    Returns dict:
        {
            "coords": [(lat, lon), ...],
            "distance_km": float,
            "segments": int,
            "error": str | None
        }
    """
    import networkx as nx

    result = {"coords": [], "distance_km": 0.0, "segments": 0, "error": None}

    if G is None:
        result["error"] = "Graph belum dimuat."
        return result

    try:
        # Cari node terdekat dengan koordinat
        orig_node = _nearest_node(G, orig_lat, orig_lon)
        dest_node = _nearest_node(G, dest_lat, dest_lon)

        if orig_node is None or dest_node is None:
            result["error"] = "Tidak ada jalan di dekat koordinat tersebut."
            return result

        if orig_node == dest_node:
            result["error"] = "Titik awal dan tujuan terlalu dekat."
            return result

        # Shortest path
        try:
            route_nodes = nx.shortest_path(G, orig_node, dest_node, weight="length")
        except nx.NetworkXNoPath:
            result["error"] = "Tidak ada rute yang menghubungkan kedua titik."
            return result
        except nx.NodeNotFound as e:
            result["error"] = f"Node tidak ditemukan: {e}"
            return result

        # Ambil koordinat tiap node
        coords = []
        for n in route_nodes:
            nd = G.nodes[n]
            lat = nd.get("y", nd.get("lat"))
            lon = nd.get("x", nd.get("lon"))
            if lat is not None and lon is not None:
                coords.append((float(lat), float(lon)))

        # Hitung total jarak
        total_m = 0.0
        for i in range(len(route_nodes) - 1):
            u, v = route_nodes[i], route_nodes[i + 1]
            edge_data = None
            if G.has_edge(u, v, 0):
                edge_data = G.edges[u, v, 0]
            elif G.has_edge(u, v):
                edge_data = list(G[u][v].values())[0]
            if edge_data:
                total_m += edge_data.get("length", 0) or 0

        result["coords"] = coords
        result["distance_km"] = round(total_m / 1000, 2)
        result["segments"] = len(route_nodes)

    except Exception as e:
        result["error"] = f"Error routing: {e}"

    return result


def _nearest_node(G, lat: float, lon: float):
    """Cari node terdekat ke koordinat (lat, lon) secara brute-force."""
    best_node = None
    best_dist = float("inf")

    for node, data in G.nodes(data=True):
        nlat = data.get("y", data.get("lat"))
        nlon = data.get("x", data.get("lon"))
        if nlat is None or nlon is None:
            continue
        d = (float(nlat) - lat) ** 2 + (float(nlon) - lon) ** 2
        if d < best_dist:
            best_dist = d
            best_node = node

    return best_node
