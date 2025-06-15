# 🏢 Complete Network Monitor

A powerful, cross-platform network monitoring solution with attendance tracking and WiFi-based distance estimation. Perfect for offices, schools, warehouses, or any environment where you need to track device presence and movement.



## ✨ Features

### 🎯 Core Functionality
- **Real-time Network Scanning** - Discover all devices on your network
- **Attendance Tracking** - Automatic arrival/departure detection
- **Distance Estimation** - WiFi signal-based proximity detection (0-100m)
- **Cross-Platform** - Works on Windows, Linux, and macOS
- **Web Dashboard** - Modern, responsive interface accessible from any device
- **Sound Alerts** - Customizable notifications for arrivals/departures

### 📊 Advanced Features
- **Multi-Zone Detection** - On-site, Near, Leaving, Away zones
- **Custom Device Names** - Label devices for easy identification
- **Device Categories** - Employee, Visitor, Equipment, Other
- **Export Reports** - CSV attendance logs with timestamps
- **Persistent Storage** - Device configurations saved between sessions
- **Working Hours** - Define monitoring schedules

### 🔧 Technical Highlights
- Zero external dependencies for core functionality
- Automatic MAC address vendor detection
- Configurable scan intervals
- RESTful API for integration
- Real-time WebSocket updates
- Mobile-responsive design

## 🚀 Quick Start

### Prerequisites
- Python 3.6 or higher
- pip (Python package manager)
- Administrator/sudo privileges (for MAC detection)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ClaytonDixon/complete-network-monitor.git
cd complete-network-monitor
```

2. **Install dependencies**
```bash
pip install flask flask-cors
```

3. **Run the monitor**
```bash
# Linux/Mac
sudo python3 complete-monitor-with-distance.py

# Windows (as Administrator)
python complete-monitor-with-distance.py
```

4. **Access the dashboard**
Open your browser and navigate to: `http://localhost:8000`

## 📖 Usage

### Basic Workflow

1. **Scan Network** - Click "🔍 Scan Network" to discover devices
2. **Configure Devices** - Click "⚙️ Configure" on devices you want to track
3. **Start Monitoring** - Click "▶️ Start Monitoring" to begin tracking
4. **View Reports** - Check the Attendance tab for daily summaries

### Distance Tracking

Enable WiFi-based distance estimation:
1. Click "📡 Toggle Distance"
2. Go to Distance tab for calibration
3. Select your environment type
4. Fine-tune based on your space

## 📋 Requirements

### System Requirements
- **OS**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **Python**: 3.6 or higher
- **Memory**: 512MB RAM minimum
- **Network**: Local network access

### Python Dependencies
```txt
flask>=2.0.0
flask-cors>=3.0.0
```

### Optional System Packages (Linux)
```bash
sudo apt-get install net-tools beep
```

## 🛠️ Configuration

### Environment Variables
```bash
# Port configuration (default: 8000)
export MONITOR_PORT=8080

# Enable debug mode
export FLASK_DEBUG=1
```

### Configuration Files
- `device_monitor.json` - Device configurations and states
- `attendance_alerts.json` - Alert history
- `attendance_log.csv` - Attendance records

### Calibration Settings
```json
{
  "referenceRSSI": -40,
  "pathLossExponent": 2.0,
  "distanceThreshold": 50
}
```

## 🔌 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web dashboard |
| GET | `/devices` | List all devices |
| POST | `/scan` | Trigger network scan |
| POST | `/scan_with_distance` | Scan with distance estimation |
| GET | `/alerts` | Get recent alerts |
| POST | `/update_device` | Update device configuration |
| POST | `/start_monitoring` | Start monitoring |
| POST | `/stop_monitoring` | Stop monitoring |
| GET | `/export_attendance` | Export attendance CSV |

### Example API Usage
```bash
# Get all devices
curl http://localhost:8000/devices

# Start monitoring
curl -X POST http://localhost:8000/start_monitoring

# Update device
curl -X POST http://localhost:8000/update_device \
  -H "Content-Type: application/json" \
  -d '{"ip":"192.168.1.100","name":"John Laptop","monitored":true}'
```

## 🚨 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| No MAC addresses | Run with sudo/admin privileges |
| Port already in use | Change port or kill existing process |
| No devices found | Check network connectivity and firewall |
| No sound alerts | Install system beep package |
| Can't access remotely | Check firewall rules for port 8000 |

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
python3 complete-network-monitor.py
```
