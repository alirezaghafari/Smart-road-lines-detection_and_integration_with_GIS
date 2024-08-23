/*
This Swift code is designed to address the challenge of low geographic data collection rates on mobile phones, specifically iPhones, where the rate is approximately 1 Hz. Due to this low sampling rate, positional data collected even multiple times per second will be identical within each second and only updated after a full second. This limitation can impact the accuracy of road line registration processes.

To mitigate the effects of low geographic data sampling rates, this program uses an innovative approach to capture location data at a much higher frequency of 50 Hz. The primary advantage of this high-frequency data collection is that we can precisely determine the exact time when the mobile sensor's geographic coordinates were updated.

The program achieves this by continuously recording location data every 20 milliseconds (which corresponds to 50 Hz) and storing this data in a JSON file. This ensures that each recorded data point is timestamped accurately, allowing us to select frames for road line prediction operations based on the exact timing of data updates. Consequently, this reduces the error from a maximum of 6 meters to a maximum of 12 centimeters for a vehicle traveling at 6 meters per second, which significantly improves the accuracy of the positional data.
*/

import SwiftUI
import CoreLocation
import CoreMotion
var filename: String = DateFormatter.localizedString(from: Date(), dateStyle: .medium, timeStyle: .medium) + ".json"



// Define a custom struct for location data
struct LocationData: Codable {
    let time: String
    let latitude: Double
    let longitude: Double
    let altitude: Double
    let horizontalAccuracy: Double
    let verticalAccuracy: Double
    let speed: Double
    let speedAccuracy: Double
    var magneticHeading: Double?

    init(time: String, latitude: Double, longitude: Double, altitude: Double, horizontalAccuracy: Double, verticalAccuracy: Double, speed: Double, speedAccuracy: Double, accelerationX: Double? = nil, accelerationY: Double? = nil, accelerationZ: Double? = nil, roll: Double? = nil, pitch: Double? = nil, yaw: Double? = nil, rotationRateX: Double? = nil, rotationRateY: Double? = nil, rotationRateZ: Double? = nil, magneticHeading: Double? = nil) {
        self.time = time
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.horizontalAccuracy = horizontalAccuracy
        self.verticalAccuracy = verticalAccuracy
        self.speed = speed
        self.speedAccuracy = speedAccuracy
        self.magneticHeading = magneticHeading
    }
}

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private var locationManager = CLLocationManager()
    private let motionManager = CMMotionManager()
    @Published var locations: [LocationData] = []

    private var buffer: [LocationData] = [] // Buffer to store locations temporarily

    override init() {
        super.init()

        locationManager.delegate = self
        locationManager.requestAlwaysAuthorization()
        locationManager.allowsBackgroundLocationUpdates = true
        locationManager.startUpdatingLocation()
        locationManager.startUpdatingHeading() // Start updating magnetic heading


        Timer.scheduledTimer(withTimeInterval: 0.02, repeats: true) { timer in
            if let location = self.locationManager.location {
                let dateFormatter = DateFormatter()
                dateFormatter.dateFormat = "yyyyMMdd.HHmmss.SSS"
                let currentTime = dateFormatter.string(from: Date())
                let locationData = LocationData(time: currentTime, latitude: location.coordinate.latitude, longitude: location.coordinate.longitude, altitude: location.altitude, horizontalAccuracy: location.horizontalAccuracy, verticalAccuracy: location.verticalAccuracy, speed: location.speed, speedAccuracy: location.speedAccuracy, magneticHeading: self.locationManager.heading?.magneticHeading) // Add magneticHeading to LocationData
                self.buffer.append(locationData)

                // If buffer reaches 20 entries, append to main locations array and reset buffer
                if self.buffer.count >= 20 {
                    self.locations.append(contentsOf: self.buffer)
                    self.buffer.removeAll()
                    self.saveLocationsToJSON()
                }
            
            }
        }
    }

    // Save locations to JSON file
    func saveLocationsToJSON() {
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let data = try encoder.encode(locations)
            if let jsonString = String(data: data, encoding: .utf8) {
                let fileURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent(filename)
                try jsonString.write(to: fileURL, atomically: true, encoding: .utf8)
            }
        } catch {
            print("Error saving locations to JSON: \(error.localizedDescription)")
        }
    }

    // CLLocationManagerDelegate method to receive updated heading
    func locationManager(_ manager: CLLocationManager, didUpdateHeading newHeading: CLHeading) {
        guard newHeading.headingAccuracy >= 0 else { return } // Check if heading is reliable
        if let lastLocationIndex = self.locations.indices.last {
            self.locations[lastLocationIndex].magneticHeading = newHeading.magneticHeading
        }
    }
}

struct ContentView: View {
    @ObservedObject var locationManager = LocationManager()

    var body: some View {
        VStack {
            Text("Recording:")
                .font(.headline)
                .padding()

        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}



