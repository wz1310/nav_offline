import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, TextInput, FlatList, ActivityIndicator, Alert } from 'react-native';
import MapLibreGL from '@maplibre/maplibre-react-native';
import { StatusBar } from 'expo-status-bar';
import * as Location from 'expo-location';
import { MaterialCommunityIcons, Ionicons, MaterialIcons } from '@expo/vector-icons';
import axios from 'axios';

// Setup MapLibre
MapLibreGL.setAccessToken(null);

const STYLE_URL = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

export default function App() {
  const [destination, setDestination] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [route, setRoute] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const mapCamera = useRef(null);

  useEffect(() => {
    (async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Permission to access location was denied');
        return;
      }

      let location = await Location.getCurrentPositionAsync({});
      setUserLocation([location.coords.longitude, location.coords.latitude]);
    })();
  }, []);

  const searchLocation = async (text) => {
    setDestination(text);
    if (text.length < 3) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await axios.get(
        `https://nominatim.openstreetmap.org/search?q=${text}&format=json&limit=5&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'NavOfflinePro/1.0'
          }
        }
      );
      setSuggestions(response.data);
    } catch (error) {
      console.error("Search error:", error);
    }
  };

  const selectDestination = async (item) => {
    const destCoords = [parseFloat(item.lon), parseFloat(item.lat)];
    setDestination(item.display_name);
    setSuggestions([]);
    
    if (userLocation) {
      await getRoute(userLocation, destCoords);
    }
  };

  const getRoute = async (start, end) => {
    setLoading(true);
    try {
      const response = await axios.get(
        `https://router.project-osrm.org/route/v1/driving/${start[0]},${start[1]};${end[0]},${end[1]}?overview=full&geometries=geojson`
      );
      
      if (response.data.routes && response.data.routes.length > 0) {
        setRoute(response.data.routes[0].geometry);
        
        // Fit bounds to route
        const coordinates = response.data.routes[0].geometry.coordinates;
        // Simple bounding box calculation
        const lons = coordinates.map(c => c[0]);
        const lats = coordinates.map(c => c[1]);
        const minLon = Math.min(...lons);
        const maxLon = Math.max(...lons);
        const minLat = Math.min(...lats);
        const maxLat = Math.max(...lats);

        mapCamera.current?.setCamera({
          bounds: {
            ne: [maxLon, maxLat],
            sw: [minLon, minLat],
          },
          padding: { paddingBottom: 100, paddingTop: 100, paddingLeft: 50, paddingRight: 50 },
          animationDuration: 1000,
        });
      }
    } catch (error) {
      Alert.alert("Error", "Gagal mendapatkan rute");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const startNavigation = () => {
    if (!route) {
      Alert.alert("Peringatan", "Silakan cari tujuan terlebih dahulu");
      return;
    }
    setIsNavigating(true);
    mapCamera.current?.setCamera({
      zoomLevel: 18,
      pitch: 60,
      heading: 0, // Should ideally follow user heading
      animationDuration: 1000,
    });
  };

  const downloadOffline = async () => {
    if (!route) {
      Alert.alert("Info", "Cari rute terlebih dahulu untuk mendownload peta area tersebut");
      return;
    }

    setIsDownloading(true);
    setDownloadProgress(0);

    try {
      const coordinates = route.coordinates;
      const lons = coordinates.map(c => c[0]);
      const lats = coordinates.map(c => c[1]);
      const bounds = [Math.max(...lons), Math.max(...lats), Math.min(...lons), Math.min(...lats)];

      const pack = await MapLibreGL.offlineManager.createPack({
        name: `route-${Date.now()}`,
        styleURL: STYLE_URL,
        minZoom: 12,
        maxZoom: 16,
        bounds: [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]
      }, (pack, status) => {
        setDownloadProgress(Math.round(status.percentage));
      });

      Alert.alert("Selesai", "Peta offline berhasil didownload!");
    } catch (error) {
      console.error(error);
      Alert.alert("Error", "Gagal mendownload peta offline");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      
      <MapLibreGL.MapView
        style={styles.map}
        styleURL={STYLE_URL}
        logoEnabled={false}
        attributionEnabled={false}
      >
        <MapLibreGL.Camera
          ref={mapCamera}
          followUserLocation={isNavigating}
          followUserMode={isNavigating ? "course" : "normal"}
          zoomLevel={isNavigating ? 18 : 12}
          pitch={isNavigating ? 60 : 0}
          centerCoordinate={userLocation || [106.8456, -6.2088]}
        />
        
        {userLocation && (
          <MapLibreGL.UserLocation 
            visible={true} 
            renderMode="arrow"
            androidRenderMode="gps"
          />
        )}

        {route && (
          <MapLibreGL.ShapeSource id="routeSource" shape={route}>
            <MapLibreGL.LineLayer
              id="routeLayer"
              style={{
                lineColor: '#4285F4',
                lineWidth: 8,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
          </MapLibreGL.ShapeSource>
        )}
      </MapLibreGL.MapView>

      {/* Header Navigation (Google Maps Style) */}
      {isNavigating ? (
        <View style={styles.navHeader}>
          <View style={styles.navHeaderLeft}>
            <MaterialCommunityIcons name="arrow-up-bold" size={40} color="white" />
          </View>
          <View style={styles.navHeaderRight}>
            <Text style={styles.navStreetName}>{destination.split(',')[0]}</Text>
            <Text style={styles.navDirection}>Lurus terus sejauh 1.2 km</Text>
          </View>
          <TouchableOpacity onPress={() => setIsNavigating(false)} style={styles.closeNav}>
            <Ionicons name="close" size={24} color="white" />
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.searchOverlay}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={20} color="#666" style={{ marginRight: 10 }} />
            <TextInput
              style={styles.input}
              placeholder="Cari Tujuan..."
              value={destination}
              onChangeText={searchLocation}
            />
            {loading && <ActivityIndicator size="small" color="#1a73e8" />}
          </View>
          {suggestions.length > 0 && (
            <View style={styles.suggestionsContainer}>
              <FlatList
                data={suggestions}
                keyExtractor={(item) => item.place_id.toString()}
                renderItem={({ item }) => (
                  <TouchableOpacity style={styles.suggestionItem} onPress={() => selectDestination(item)}>
                    <MaterialIcons name="location-on" size={20} color="#666" />
                    <Text style={styles.suggestionText} numberOfLines={1}>{item.display_name}</Text>
                  </TouchableOpacity>
                )}
              />
            </View>
          )}
        </View>
      )}

      {/* Floating Buttons */}
      <View style={styles.floatingControls}>
        <TouchableOpacity style={styles.fab} onPress={() => Alert.alert("Search", "Fitur pencarian diaktifkan")}>
          <Ionicons name="search" size={24} color="#555" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.fab}>
          <Ionicons name="volume-high" size={24} color="#555" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.fab} onPress={() => mapCamera.current?.setCamera({ heading: 0, animationDuration: 500 })}>
          <MaterialCommunityIcons name="compass-outline" size={24} color="#555" />
        </TouchableOpacity>
      </View>

      {/* Bottom Panel */}
      {!isNavigating && route && (
        <View style={styles.bottomPanel}>
          <View style={styles.routeInfo}>
            <Text style={styles.routeTime}>12 mnt</Text>
            <Text style={styles.routeDistance}>(4.2 km)</Text>
          </View>
          <View style={styles.actionButtons}>
            <TouchableOpacity style={styles.downloadBtn} onPress={downloadOffline} disabled={isDownloading}>
              <Ionicons name="cloud-download-outline" size={20} color="#1a73e8" />
              <Text style={styles.downloadBtnText}>
                {isDownloading ? `Downloading ${downloadProgress}%` : "Download Offline"}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.startBtn} onPress={startNavigation}>
              <MaterialCommunityIcons name="navigation" size={20} color="white" />
              <Text style={styles.startBtnText}>Mulai</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f0f0',
  },
  map: {
    flex: 1,
  },
  searchOverlay: {
    position: 'absolute',
    top: 50,
    left: 15,
    right: 15,
    zIndex: 10,
  },
  searchBar: {
    backgroundColor: 'white',
    borderRadius: 25,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    height: 50,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  suggestionsContainer: {
    backgroundColor: 'white',
    marginTop: 5,
    borderRadius: 15,
    elevation: 5,
    maxHeight: 250,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  suggestionText: {
    marginLeft: 10,
    fontSize: 14,
    color: '#333',
    flex: 1,
  },
  navHeader: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: '#34a853', // Google Green
    height: 100,
    paddingTop: 40,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    zIndex: 20,
  },
  navHeaderLeft: {
    marginRight: 15,
  },
  navHeaderRight: {
    flex: 1,
  },
  navStreetName: {
    color: 'white',
    fontSize: 22,
    fontWeight: 'bold',
  },
  navDirection: {
    color: 'white',
    fontSize: 14,
    opacity: 0.9,
  },
  closeNav: {
    padding: 5,
  },
  floatingControls: {
    position: 'absolute',
    right: 15,
    top: 150,
    alignItems: 'center',
  },
  fab: {
    backgroundColor: 'white',
    width: 45,
    height: 45,
    borderRadius: 22.5,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  bottomPanel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
  },
  routeInfo: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 15,
  },
  routeTime: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#34a853',
  },
  routeDistance: {
    fontSize: 16,
    color: '#666',
    marginLeft: 10,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  downloadBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#eee',
    borderRadius: 25,
    height: 50,
    marginRight: 10,
  },
  downloadBtnText: {
    marginLeft: 8,
    color: '#1a73e8',
    fontWeight: '600',
  },
  startBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1a73e8',
    borderRadius: 25,
    height: 50,
  },
  startBtnText: {
    marginLeft: 8,
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

