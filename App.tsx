import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, TextInput } from 'react-native';
import MapLibreGL from '@maplibre/maplibre-react-native';
import { StatusBar } from 'expo-status-bar';

// Setup MapLibre
MapLibreGL.setAccessToken(null);

export default function App() {
  const [destination, setDestination] = useState('');
  const [isNavigating, setIsNavigating] = useState(false);

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      
      <MapLibreGL.MapView
        style={styles.map}
        styleURL="https://demotiles.maplibre.org/style.json"
        logoEnabled={false}
      >
        <MapLibreGL.Camera
          zoomLevel={12}
          centerCoordinate={[106.8456, -6.2088]} // Jakarta
        />
        
        <MapLibreGL.UserLocation visible={true} />
      </MapLibreGL.MapView>

      <View style={styles.overlay}>
        <View style={styles.searchContainer}>
          <TextInput
            style={styles.input}
            placeholder="Cari Tujuan (Google Maps Style)..."
            placeholderTextColor="#999"
            value={destination}
            onChangeText={setDestination}
          />
        </View>

        <TouchableOpacity 
          style={styles.navButton}
          onPress={() => setIsNavigating(!isNavigating)}
        >
          <Text style={styles.navButtonText}>
            {isNavigating ? "BERHENTI" : "MULAI NAVIGASI"}
          </Text>
        </TouchableOpacity>
      </View>

      {isNavigating && (
        <View style={styles.navPanel}>
          <Text style={styles.navTitle}>Navigasi Aktif</Text>
          <Text style={styles.navSub}>Menuju: {destination || "Titik Pilihan"}</Text>
          <Text style={styles.navDetail}>Jarak: 4.2 km | Estimasi: 12 mnt</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f1117',
  },
  map: {
    flex: 1,
  },
  overlay: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
  },
  searchContainer: {
    backgroundColor: 'white',
    borderRadius: 25,
    paddingHorizontal: 20,
    height: 50,
    justifyContent: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  input: {
    fontSize: 16,
    color: '#333',
  },
  navButton: {
    backgroundColor: '#1a73e8',
    marginTop: 15,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 3,
  },
  navButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  navPanel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 25,
    elevation: 10,
  },
  navTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a73e8',
    marginBottom: 5,
  },
  navSub: {
    fontSize: 16,
    color: '#333',
    marginBottom: 5,
  },
  navDetail: {
    fontSize: 14,
    color: '#666',
  },
});
