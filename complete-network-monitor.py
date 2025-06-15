#!/usr/bin/env python3
"""
Complete Cross-Platform Network Monitor with Distance Estimation
Includes: Attendance Tracking, WiFi Distance Estimation, and Departure Detection
Works on Windows, Linux, and macOS
"""

import subprocess
import socket
import time
import json
import re
import threading
import platform
import sys
import os
import math
from datetime import datetime, timedelta
from pathlib import Path

# Flask imports
try:
    from flask import Flask, jsonify, render_template_string, request, send_file
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("Flask not installed. Install with: pip install flask flask-cors")
    sys.exit(1)

# Platform-specific imports for sound
if platform.system() == 'Windows':
    try:
        import winsound
        HAS_WINSOUND = True
    except ImportError:
        HAS_WINSOUND = False
else:
    HAS_WINSOUND = False

# Enhanced HTML with both attendance and distance features
HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Network Monitor - Complete Edition</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; 
            margin: 0; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 1600px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 { 
            color: #333; 
            margin: 0 0 10px 0;
        }
        .controls {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        button { 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            cursor: pointer; 
            border-radius: 5px; 
            font-size: 16px;
            transition: background 0.3s;
        }
        button:hover { 
            background: #0056b3; 
        }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
        }
        .btn-danger {
            background: #dc3545;
        }
        .btn-danger:hover {
            background: #c82333;
        }
        .btn-success {
            background: #28a745;
        }
        .btn-success:hover {
            background: #218838;
        }
        .monitoring-status {
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }
        .monitoring-active {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .monitoring-inactive {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            border-bottom: 2px solid #ddd;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background: white;
            border: 1px solid #ddd;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
        }
        .tab.active {
            background: #007bff;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .alert-log {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
        }
        .alert-entry {
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #dc3545;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .alert-entry.arrival {
            border-left-color: #28a745;
        }
        .alert-entry.distance {
            border-left-color: #ffc107;
        }
        .alert-time {
            font-weight: bold;
            color: #666;
        }
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .device { 
            background: white; 
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .device:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .device.online { 
            border-left: 5px solid #28a745; 
        }
        .device.offline { 
            border-left: 5px solid #dc3545;
            opacity: 0.7;
        }
        .device.monitored {
            background: #e7f3ff;
            border: 2px solid #007bff;
        }
        .device-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .device-name { 
            font-weight: bold; 
            font-size: 20px;
            color: #333;
        }
        .device-status {
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .status-online {
            background: #d4edda;
            color: #155724;
        }
        .status-offline {
            background: #f8d7da;
            color: #721c24;
        }
        .device-info { 
            color: #666;
            line-height: 1.8;
        }
        .device-info strong {
            color: #333;
            display: inline-block;
            width: 120px;
        }
        .monitor-toggle {
            margin-top: 10px;
        }
        .attendance-summary {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .attendance-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .attendance-table th, .attendance-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .attendance-table th {
            background: #f8f9fa;
            font-weight: bold;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            width: 90%;
            max-width: 400px;
        }
        .modal h3 {
            margin-top: 0;
        }
        .modal input, .modal select {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
            box-sizing: border-box;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        .checkbox-label input[type="checkbox"] {
            width: auto;
            margin-right: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .platform-info {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 14px;
        }
        
        /* Distance estimation styles */
        .distance-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin-left: 10px;
        }
        .distance-onsite { background: #d4edda; color: #155724; }
        .distance-near { background: #fff3cd; color: #856404; }
        .distance-leaving { background: #ffeaa7; color: #d63031; }
        .distance-away { background: #f8d7da; color: #721c24; }
        
        .distance-meter {
            margin: 15px 0;
            position: relative;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            overflow: hidden;
        }
        .distance-fill {
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            background: linear-gradient(to right, #4caf50, #ffeb3b, #ff9800, #f44336);
            transition: width 0.5s;
        }
        .distance-marker {
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 20px;
            height: 20px;
            background: #333;
            border-radius: 50%;
            border: 3px solid white;
        }
        .signal-visual {
            margin: 10px 0;
        }
        .signal-bars {
            display: inline-flex;
            gap: 3px;
            align-items: flex-end;
            margin-left: 10px;
        }
        .signal-bar {
            width: 8px;
            background: #ddd;
            border-radius: 2px;
        }
        .signal-bar.active { background: #4caf50; }
        .signal-bar.weak { background: #ff9800; }
        
        .calibration-panel {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .calibration-form input {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .calibration-form label {
            display: block;
            margin-top: 10px;
            font-weight: bold;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 Network Monitor - Complete Edition</h1>
            <div id="monitoringStatus" class="monitoring-status monitoring-inactive">
                ⏸️ Monitoring: INACTIVE
            </div>
            <div class="platform-info">
                Running on: <strong id="platformInfo">Loading...</strong> | 
                Distance Mode: <span id="distanceMode">Disabled</span>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="scanNetwork()" id="scanBtn">🔍 Scan Network</button>
            <button onclick="startMonitoring()" id="startMonBtn" class="btn-success">▶️ Start Monitoring</button>
            <button onclick="stopMonitoring()" id="stopMonBtn" class="btn-danger" disabled>⏹️ Stop Monitoring</button>
            <button onclick="toggleDistanceMode()">📡 Toggle Distance</button>
            <button onclick="showSettings()">⚙️ Settings</button>
            <button onclick="exportAttendance()">📊 Export Attendance</button>
            <button onclick="clearAlerts()">🗑️ Clear Alerts</button>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalDevices">0</div>
                <div class="stat-label">Total Devices</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="onlineDevices">0</div>
                <div class="stat-label">Currently Present</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="monitoredDevices">0</div>
                <div class="stat-label">Monitored</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="onSiteDevices">0</div>
                <div class="stat-label">On-Site (<10m)</div>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('devices')">Devices</div>
            <div class="tab" onclick="showTab('alerts')">Alerts</div>
            <div class="tab" onclick="showTab('attendance')">Attendance</div>
            <div class="tab" onclick="showTab('distance')">Distance</div>
        </div>
        
        <!-- Devices Tab -->
        <div id="devicesTab" class="tab-content active">
            <div id="devices" class="device-grid"></div>
        </div>
        
        <!-- Alerts Tab -->
        <div id="alertsTab" class="tab-content">
            <div class="alert-log">
                <h3>Recent Activity</h3>
                <div id="alertList"></div>
            </div>
        </div>
        
        <!-- Attendance Tab -->
        <div id="attendanceTab" class="tab-content">
            <div class="attendance-summary">
                <h3>Today's Attendance</h3>
                <table class="attendance-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Device</th>
                            <th>Arrival</th>
                            <th>Departure</th>
                            <th>Duration</th>
                        </tr>
                    </thead>
                    <tbody id="attendanceTable">
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Distance Tab -->
        <div id="distanceTab" class="tab-content">
            <div class="calibration-panel">
                <h3>📐 Distance Calibration</h3>
                <div class="calibration-form">
                    <label>Reference RSSI at 1 meter (dBm):</label>
                    <input type="number" id="refRSSI" value="-40" min="-100" max="0">
                    
                    <label>Path Loss Exponent (2.0-4.0):</label>
                    <input type="number" id="pathLossExp" value="2.0" min="1.0" max="5.0" step="0.1">
                    
                    <label>Environment Type:</label>
                    <select id="envType" onchange="setEnvironment()">
                        <option value="open">Open Space (2.0)</option>
                        <option value="office">Office/Indoor (2.5-3.0)</option>
                        <option value="warehouse">Warehouse (3.0-3.5)</option>
                        <option value="outdoor">Outdoor with obstacles (3.5-4.0)</option>
                    </select>
                    
                    <label>Distance Alert Threshold (meters):</label>
                    <input type="number" id="distanceThreshold" value="50" min="10" max="200">
                    
                    <button onclick="updateCalibration()">Update Calibration</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div id="settingsModal" class="modal">
        <div class="modal-content">
            <h3>Monitoring Settings</h3>
            <label>Scan Interval (seconds):</label>
            <input type="number" id="scanInterval" value="30" min="10" max="300">
            
            <label>Alert Sound:</label>
            <select id="alertSound">
                <option value="yes">Enabled</option>
                <option value="no">Disabled</option>
            </select>
            
            <label>Working Hours:</label>
            <input type="time" id="workStart" value="08:00">
            <input type="time" id="workEnd" value="18:00">
            
            <div class="checkbox-label">
                <input type="checkbox" id="weekendsOnly">
                <label for="weekendsOnly">Monitor weekdays only</label>
            </div>
            
            <div class="checkbox-label">
                <input type="checkbox" id="enableDistance">
                <label for="enableDistance">Enable distance estimation</label>
            </div>
            
            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="closeSettings()">Cancel</button>
                <button onclick="saveSettings()">Save</button>
            </div>
        </div>
    </div>

    <!-- Edit Device Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <h3>Edit Device</h3>
            <p id="editDeviceInfo"></p>
            <label>Device Name:</label>
            <input type="text" id="deviceNameInput" placeholder="Enter name">
            
            <div class="checkbox-label">
                <input type="checkbox" id="monitorDevice">
                <label for="monitorDevice">Monitor this device</label>
            </div>
            
            <label>Device Type:</label>
            <select id="deviceType">
                <option value="employee">Employee</option>
                <option value="visitor">Visitor</option>
                <option value="equipment">Equipment</option>
                <option value="other">Other</option>
            </select>
            
            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="closeModal()">Cancel</button>
                <button onclick="saveDevice()">Save</button>
            </div>
        </div>
    </div>

    <script>
        let devices = [];
        let alerts = [];
        let monitoring = false;
        let monitoringInterval = null;
        let currentEditDevice = null;
        let distanceMode = false;
        let settings = {
            scanInterval: 30,
            alertSound: 'yes',
            workStart: '08:00',
            workEnd: '18:00',
            weekendsOnly: false,
            enableDistance: false,
            distanceThreshold: 50
        };
        let calibration = {
            referenceRSSI: -40,
            pathLossExponent: 2.0
        };

        // Load settings from localStorage
        const savedSettings = localStorage.getItem('monitorSettings');
        if (savedSettings) {
            settings = JSON.parse(savedSettings);
        }
        const savedCalibration = localStorage.getItem('wifiCalibration');
        if (savedCalibration) {
            calibration = JSON.parse(savedCalibration);
        }

        // Get platform info
        async function getPlatformInfo() {
            try {
                const response = await fetch('/platform_info');
                const info = await response.json();
                document.getElementById('platformInfo').textContent = info.platform;
            } catch (error) {
                document.getElementById('platformInfo').textContent = 'Unknown';
            }
        }

        function calculateDistance(rssi) {
            if (!rssi || rssi === 0) return null;
            const distance = Math.pow(10, (calibration.referenceRSSI - rssi) / (10 * calibration.pathLossExponent));
            return Math.round(distance * 10) / 10;
        }

        function getZone(distance) {
            if (!distance) return 'unknown';
            if (distance < 10) return 'onsite';
            if (distance < 30) return 'near';
            if (distance < 50) return 'leaving';
            return 'away';
        }

        function getSignalBars(rssi) {
            if (!rssi) return 0;
            if (rssi >= -50) return 5;
            if (rssi >= -60) return 4;
            if (rssi >= -70) return 3;
            if (rssi >= -80) return 2;
            return 1;
        }

        async function scanNetwork() {
            const btn = document.getElementById('scanBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Scanning...';
            
            try {
                const endpoint = distanceMode ? '/scan_with_distance' : '/scan';
                const response = await fetch(endpoint, { method: 'POST' });
                await new Promise(resolve => setTimeout(resolve, 3000));
                await refreshDevices();
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Scan Network';
            }
        }

        async function refreshDevices() {
            try {
                const response = await fetch('/devices');
                devices = await response.json();
                
                updateStats();
                displayDevices();
                updateAttendance();
                
            } catch (error) {
                console.error('Error refreshing:', error);
            }
        }

        function updateStats() {
            const total = devices.length;
            const online = devices.filter(d => d.online).length;
            const monitored = devices.filter(d => d.monitored).length;
            const onSite = devices.filter(d => d.estimated_distance && d.estimated_distance < 10).length;
            
            document.getElementById('totalDevices').textContent = total;
            document.getElementById('onlineDevices').textContent = online;
            document.getElementById('monitoredDevices').textContent = monitored;
            document.getElementById('onSiteDevices').textContent = onSite;
        }

        function displayDevices() {
            const container = document.getElementById('devices');
            
            if (devices.length === 0) {
                container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px;">No devices found. Click "Scan Network" to start.</div>';
                return;
            }
            
            // Sort: monitored first, then online, then by name
            devices.sort((a, b) => {
                if (a.monitored !== b.monitored) return b.monitored - a.monitored;
                if (a.online !== b.online) return b.online - a.online;
                return (a.custom_name || a.hostname || a.ip).localeCompare(b.custom_name || b.hostname || b.ip);
            });
            
            container.innerHTML = devices.map(device => {
                const name = device.custom_name || device.hostname || 'Unknown Device';
                const statusClass = device.online ? 'online' : 'offline';
                const monitoredClass = device.monitored ? 'monitored' : '';
                
                let distanceHTML = '';
                if (distanceMode && device.rssi) {
                    const distance = calculateDistance(device.rssi);
                    const zone = getZone(distance);
                    const signalBars = getSignalBars(device.rssi);
                    const distancePercent = Math.min(100, (distance / 100) * 100);
                    
                    // Signal bars
                    let signalHTML = '';
                    for (let i = 1; i <= 5; i++) {
                        const height = i * 6;
                        const active = i <= signalBars;
                        const weak = device.rssi < -70;
                        signalHTML += `<div class="signal-bar ${active ? (weak ? 'weak' : 'active') : ''}" style="height: ${height}px;"></div>`;
                    }
                    
                    distanceHTML = `
                        <div class="device-info">
                            <div><strong>Distance:</strong> ${distance}m <span class="distance-badge distance-${zone}">${zone.toUpperCase()}</span></div>
                            <div><strong>Signal (RSSI):</strong> ${device.rssi} dBm</div>
                        </div>
                        <div class="signal-visual">
                            <strong>Signal Strength:</strong>
                            <span class="signal-bars">${signalHTML}</span>
                        </div>
                        <div class="distance-meter">
                            <div class="distance-fill" style="width: ${distancePercent}%"></div>
                            <div class="distance-marker" style="left: ${distancePercent}%"></div>
                        </div>
                        <div style="text-align: center; margin-top: 5px; font-size: 12px; color: #666;">
                            0m — 25m — 50m — 75m — 100m
                        </div>
                    `;
                }
                
                return `
                    <div class="device ${statusClass} ${monitoredClass}">
                        <div class="device-header">
                            <div class="device-name">
                                ${name}
                                ${device.monitored ? '👁️' : ''}
                            </div>
                            <div class="device-status ${device.online ? 'status-online' : 'status-offline'}">
                                ${device.online ? 'PRESENT' : 'ABSENT'}
                            </div>
                        </div>
                        <div class="device-info">
                            <div><strong>IP:</strong> ${device.ip}</div>
                            <div><strong>MAC:</strong> ${device.mac || 'N/A'}</div>
                            <div><strong>Type:</strong> ${device.device_type || 'Unknown'}</div>
                            ${device.last_seen ? `<div><strong>Last seen:</strong> ${new Date(device.last_seen).toLocaleString()}</div>` : ''}
                        </div>
                        ${distanceHTML}
                        <button class="monitor-toggle" onclick="editDevice('${device.ip}')">
                            ⚙️ Configure
                        </button>
                    </div>
                `;
            }).join('');
        }

        async function startMonitoring() {
            monitoring = true;
            document.getElementById('startMonBtn').disabled = true;
            document.getElementById('stopMonBtn').disabled = false;
            document.getElementById('monitoringStatus').className = 'monitoring-status monitoring-active';
            document.getElementById('monitoringStatus').innerHTML = '🔴 Monitoring: ACTIVE';
            
            // Start monitoring
            await fetch('/start_monitoring', { method: 'POST' });
            
            // Set up periodic refresh
            monitoringInterval = setInterval(async () => {
                await refreshDevices();
                await checkAlerts();
            }, settings.scanInterval * 1000);
            
            // Initial check
            await checkAlerts();
        }

        async function stopMonitoring() {
            monitoring = false;
            document.getElementById('startMonBtn').disabled = false;
            document.getElementById('stopMonBtn').disabled = true;
            document.getElementById('monitoringStatus').className = 'monitoring-status monitoring-inactive';
            document.getElementById('monitoringStatus').innerHTML = '⏸️ Monitoring: INACTIVE';
            
            await fetch('/stop_monitoring', { method: 'POST' });
            
            if (monitoringInterval) {
                clearInterval(monitoringInterval);
                monitoringInterval = null;
            }
        }

        async function toggleDistanceMode() {
            distanceMode = !distanceMode;
            settings.enableDistance = distanceMode;
            
            document.getElementById('distanceMode').textContent = distanceMode ? 'Enabled' : 'Disabled';
            
            await fetch('/toggle_distance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: distanceMode })
            });
            
            if (distanceMode) {
                await scanNetwork();
            }
        }

        async function checkAlerts() {
            try {
                const response = await fetch('/alerts');
                const newAlerts = await response.json();
                
                if (newAlerts.length > alerts.length) {
                    // New alerts!
                    const latestAlert = newAlerts[0];
                    
                    if (settings.alertSound === 'yes') {
                        // Play notification sound
                        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmFgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
                        audio.play();
                    }
                    
                    // Show notification
                    showNotification(latestAlert);
                }
                
                alerts = newAlerts;
                displayAlerts();
                
            } catch (error) {
                console.error('Error checking alerts:', error);
            }
        }

        function showNotification(alert) {
            console.log(`ALERT: ${alert.device_name} - ${alert.message || (alert.type === 'departure' ? 'has left' : 'has arrived')}`);
        }

        function displayAlerts() {
            const container = document.getElementById('alertList');
            
            if (alerts.length === 0) {
                container.innerHTML = '<p>No activity recorded yet.</p>';
                return;
            }
            
            container.innerHTML = alerts.slice(0, 50).map(alert => {
                const time = new Date(alert.timestamp).toLocaleString();
                let cssClass = alert.type === 'arrival' ? 'arrival' : '';
                cssClass = alert.type === 'distance' ? 'distance' : cssClass;
                const icon = alert.type === 'arrival' ? '✅' : 
                           alert.type === 'distance' ? '📍' : '🚪';
                
                return `
                    <div class="alert-entry ${cssClass}">
                        <div class="alert-time">${time}</div>
                        <div>${icon} ${alert.message || `${alert.device_name} ${alert.type === 'departure' ? 'has left' : 'has arrived'}`}</div>
                        <div style="font-size: 12px; color: #999;">${alert.ip} - ${alert.mac || 'No MAC'}</div>
                    </div>
                `;
            }).join('');
        }

        function updateAttendance() {
            const tbody = document.getElementById('attendanceTable');
            const today = new Date().toDateString();
            
            // Get today's attendance from devices and alerts
            const attendance = devices
                .filter(d => d.monitored)
                .map(device => {
                    const arrivals = alerts.filter(a => 
                        a.ip === device.ip && 
                        a.type === 'arrival' && 
                        new Date(a.timestamp).toDateString() === today
                    );
                    const departures = alerts.filter(a => 
                        a.ip === device.ip && 
                        a.type === 'departure' && 
                        new Date(a.timestamp).toDateString() === today
                    );
                    
                    const firstArrival = arrivals.length > 0 ? new Date(arrivals[arrivals.length - 1].timestamp) : null;
                    const lastDeparture = departures.length > 0 ? new Date(departures[0].timestamp) : null;
                    
                    let duration = '';
                    if (firstArrival && lastDeparture) {
                        const diff = lastDeparture - firstArrival;
                        const hours = Math.floor(diff / 3600000);
                        const minutes = Math.floor((diff % 3600000) / 60000);
                        duration = `${hours}h ${minutes}m`;
                    } else if (firstArrival && device.online) {
                        const diff = new Date() - firstArrival;
                        const hours = Math.floor(diff / 3600000);
                        const minutes = Math.floor((diff % 3600000) / 60000);
                        duration = `${hours}h ${minutes}m (ongoing)`;
                    }
                    
                    return {
                        name: device.custom_name || device.hostname || 'Unknown',
                        device: device.device_type || 'Unknown',
                        arrival: firstArrival ? firstArrival.toLocaleTimeString() : '-',
                        departure: lastDeparture ? lastDeparture.toLocaleTimeString() : (device.online ? 'Still here' : '-'),
                        duration: duration || '-'
                    };
                });
            
            tbody.innerHTML = attendance.map(a => `
                <tr>
                    <td>${a.name}</td>
                    <td>${a.device}</td>
                    <td>${a.arrival}</td>
                    <td>${a.departure}</td>
                    <td>${a.duration}</td>
                </tr>
            `).join('');
        }

        function showTab(tab) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById(tab + 'Tab').classList.add('active');
        }

        function editDevice(ip) {
            const device = devices.find(d => d.ip === ip);
            if (!device) return;
            
            currentEditDevice = ip;
            document.getElementById('editDeviceInfo').textContent = `${ip} - ${device.mac || 'No MAC'}`;
            document.getElementById('deviceNameInput').value = device.custom_name || '';
            document.getElementById('monitorDevice').checked = device.monitored || false;
            document.getElementById('deviceType').value = device.device_type || 'employee';
            document.getElementById('editModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('editModal').style.display = 'none';
            currentEditDevice = null;
        }

        async function saveDevice() {
            if (!currentEditDevice) return;
            
            const data = {
                ip: currentEditDevice,
                name: document.getElementById('deviceNameInput').value.trim(),
                monitored: document.getElementById('monitorDevice').checked,
                device_type: document.getElementById('deviceType').value
            };
            
            try {
                await fetch('/update_device', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                closeModal();
                await refreshDevices();
            } catch (error) {
                alert('Error saving: ' + error.message);
            }
        }

        function showSettings() {
            document.getElementById('scanInterval').value = settings.scanInterval;
            document.getElementById('alertSound').value = settings.alertSound;
            document.getElementById('workStart').value = settings.workStart;
            document.getElementById('workEnd').value = settings.workEnd;
            document.getElementById('weekendsOnly').checked = settings.weekendsOnly;
            document.getElementById('enableDistance').checked = settings.enableDistance;
            document.getElementById('settingsModal').style.display = 'flex';
        }

        function closeSettings() {
            document.getElementById('settingsModal').style.display = 'none';
        }

        function saveSettings() {
            settings.scanInterval = parseInt(document.getElementById('scanInterval').value);
            settings.alertSound = document.getElementById('alertSound').value;
            settings.workStart = document.getElementById('workStart').value;
            settings.workEnd = document.getElementById('workEnd').value;
            settings.weekendsOnly = document.getElementById('weekendsOnly').checked;
            settings.enableDistance = document.getElementById('enableDistance').checked;
            
            localStorage.setItem('monitorSettings', JSON.stringify(settings));
            closeSettings();
            
            // Update distance mode
            distanceMode = settings.enableDistance;
            document.getElementById('distanceMode').textContent = distanceMode ? 'Enabled' : 'Disabled';
            
            // Restart monitoring with new interval if active
            if (monitoring) {
                stopMonitoring();
                startMonitoring();
            }
        }

        function setEnvironment() {
            const envType = document.getElementById('envType').value;
            const pathLossValues = {
                'open': 2.0,
                'office': 2.7,
                'warehouse': 3.2,
                'outdoor': 3.5
            };
            document.getElementById('pathLossExp').value = pathLossValues[envType];
        }

        function updateCalibration() {
            calibration.referenceRSSI = parseFloat(document.getElementById('refRSSI').value);
            calibration.pathLossExponent = parseFloat(document.getElementById('pathLossExp').value);
            settings.distanceThreshold = parseFloat(document.getElementById('distanceThreshold').value);
            
            localStorage.setItem('wifiCalibration', JSON.stringify(calibration));
            localStorage.setItem('monitorSettings', JSON.stringify(settings));
            
            // Send to server
            fetch('/update_calibration', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...calibration,
                    distanceThreshold: settings.distanceThreshold
                })
            });
            
            if (distanceMode) {
                scanNetwork();
            }
        }

        async function exportAttendance() {
            const date = new Date().toISOString().split('T')[0];
            window.location.href = `/export_attendance?date=${date}`;
        }

        async function clearAlerts() {
            if (confirm('Clear all alerts?')) {
                await fetch('/clear_alerts', { method: 'POST' });
                alerts = [];
                displayAlerts();
                updateAttendance();
            }
        }

        // Modal close handlers
        window.onclick = (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        };

        // Initialize calibration form
        document.getElementById('refRSSI').value = calibration.referenceRSSI;
        document.getElementById('pathLossExp').value = calibration.pathLossExponent;
        document.getElementById('distanceThreshold').value = settings.distanceThreshold || 50;
        document.getElementById('enableDistance').checked = settings.enableDistance || false;
        distanceMode = settings.enableDistance || false;
        document.getElementById('distanceMode').textContent = distanceMode ? 'Enabled' : 'Disabled';

        // Initial load
        getPlatformInfo();
        refreshDevices();
        
        // Load alerts
        fetch('/alerts').then(r => r.json()).then(a => {
            alerts = a;
            displayAlerts();
        });
    </script>
</body>
</html>
'''

# MAC vendors database
MAC_VENDORS = {
    '60:CF:84': 'ASUS',
    '0C:C4:13': 'Google',
    '1C:BF:C0': 'TP-Link',
    '48:B0:2D': 'NVIDIA Corporation',
    '78:80:38': 'Samsung Electronics',
    '04:D9:F5': 'Apple Inc.',
    '00:50:56': 'VMware',
    'F0:D4:15': 'Realtek',
    '04:7C:16': 'Realtek',
    '00:24:27': 'ASUS',
    '0A:00:27': 'VirtualBox',
    'F2:D4:15': 'Microsoft',
    '00:0C:29': 'VMware',
    'DC:A6:32': 'Raspberry Pi',
    'B8:27:EB': 'Raspberry Pi',
    'E4:5F:01': 'Raspberry Pi',
}

class CompleteNetworkMonitor:
    def __init__(self):
        self.devices = {}
        self.scanning = False
        self.monitoring = False
        self.distance_mode = False
        self.alerts = []
        self.save_file = Path("device_monitor.json")
        self.alerts_file = Path("attendance_alerts.json")
        self.attendance_file = Path("attendance_log.csv")
        self.platform = platform.system()
        self.calibration = {
            'referenceRSSI': -40,
            'pathLossExponent': 2.0,
            'distanceThreshold': 50
        }
        self.load_data()
        
    def load_data(self):
        """Load saved data"""
        # Load devices
        if self.save_file.exists():
            try:
                with open(self.save_file, 'r') as f:
                    saved = json.load(f)
                    for ip, data in saved.items():
                        self.devices[ip] = data
            except:
                pass
        
        # Load alerts
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r') as f:
                    self.alerts = json.load(f)
            except:
                self.alerts = []
    
    def save_data(self):
        """Save device data"""
        with open(self.save_file, 'w') as f:
            json.dump(self.devices, f, indent=2)
        
        with open(self.alerts_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)
    
    def get_vendor(self, mac):
        """Get vendor from MAC"""
        if not mac:
            return None
        
        oui = mac[:8]
        return MAC_VENDORS.get(oui)
    
    def get_local_network(self):
        """Get network info - cross platform"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            parts = local_ip.split('.')
            base = '.'.join(parts[:3])
            
            return base, local_ip
        except:
            return "192.168.1", "192.168.1.1"
    
    def ping(self, ip):
        """Cross-platform quick ping"""
        try:
            if self.platform == 'Windows':
                cmd = ['ping', '-n', '1', '-w', '200', ip]
            else:  # Linux/Mac
                cmd = ['ping', '-c', '1', '-W', '1', ip]
            
            result = subprocess.run(cmd, capture_output=True, timeout=1)
            return result.returncode == 0
        except:
            return False
    
    def ping_with_stats(self, ip):
        """Ping with response time for RSSI estimation"""
        try:
            if self.platform == 'Windows':
                cmd = ['ping', '-n', '5', '-w', '500', ip]
            else:
                cmd = ['ping', '-c', '5', '-W', '1', ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                # Extract average response time
                if self.platform == 'Windows':
                    avg_match = re.search(r'Average = (\d+)ms', result.stdout)
                else:
                    avg_match = re.search(r'avg/([\d.]+)/', result.stdout)
                
                if avg_match:
                    avg_time = float(avg_match.group(1))
                    
                    # Estimate RSSI from response time
                    if avg_time < 2:
                        return -40  # Very strong
                    elif avg_time < 5:
                        return -50  # Strong
                    elif avg_time < 10:
                        return -60  # Good
                    elif avg_time < 20:
                        return -70  # Fair
                    elif avg_time < 50:
                        return -80  # Weak
                    else:
                        return -90  # Very weak
        except:
            pass
        
        return -70  # Default
    
    def get_hostname(self, ip):
        """Get hostname - cross platform"""
        try:
            return socket.gethostbyaddr(ip)[0].split('.')[0]
        except:
            return None
    
    def get_mac(self, ip):
        """Get MAC address - cross platform"""
        try:
            # First ping to ensure ARP entry
            if self.platform == 'Windows':
                subprocess.run(['ping', '-n', '1', '-w', '100', ip], 
                             capture_output=True, timeout=0.5)
            else:
                subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                             capture_output=True, timeout=0.5)
            
            # Get ARP table
            if self.platform == 'Windows':
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
                # Windows format
                for line in result.stdout.split('\n'):
                    if ip in line:
                        parts = line.split()
                        for part in parts:
                            if '-' in part and len(part) == 17:
                                return part.upper().replace('-', ':')
            
            elif self.platform == 'Linux':
                # Try ip neighbor first
                try:
                    result = subprocess.run(['ip', 'neighbor', 'show'], 
                                          capture_output=True, text=True)
                    for line in result.stdout.split('\n'):
                        if ip in line and 'lladdr' in line:
                            parts = line.split()
                            idx = parts.index('lladdr')
                            if idx + 1 < len(parts):
                                return parts[idx + 1].upper()
                except:
                    # Fallback to arp
                    result = subprocess.run(['arp', '-n'], capture_output=True, text=True)
                    for line in result.stdout.split('\n'):
                        if ip in line:
                            mac_match = re.search(r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', line)
                            if mac_match:
                                return mac_match.group(0).upper()
            
            elif self.platform == 'Darwin':  # macOS
                result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
                mac_match = re.search(r'([0-9a-fA-F]{1,2}:){5}[0-9a-fA-F]{1,2}', result.stdout)
                if mac_match:
                    return mac_match.group(0).upper()
                    
        except:
            pass
        return None
    
    def calculate_distance(self, rssi):
        """Calculate distance from RSSI"""
        if rssi and rssi != 0:
            distance = math.pow(10, (self.calibration['referenceRSSI'] - rssi) / (10 * self.calibration['pathLossExponent']))
            return round(distance, 1)
        return None
    
    def get_zone(self, distance):
        """Get zone from distance"""
        if not distance:
            return "unknown"
        if distance < 10:
            return "on-site"
        elif distance < 30:
            return "near-site"
        elif distance < 50:
            return "leaving"
        else:
            return "away"
    
    def play_alert_sound(self, frequency=1000, duration=0.2):
        """Cross-platform alert sound"""
        try:
            if self.platform == 'Windows' and HAS_WINSOUND:
                winsound.Beep(int(frequency), int(duration * 1000))
            elif self.platform == 'Linux':
                # Try system beep
                subprocess.run(['beep', '-f', str(frequency), '-l', str(int(duration * 1000))], 
                             capture_output=True)
            elif self.platform == 'Darwin':  # macOS
                # Use system sound
                subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'], 
                             capture_output=True)
            else:
                # Terminal bell
                print('\a', end='', flush=True)
        except:
            # Silent fail - don't break on sound errors
            pass
    
    def scan(self):
        """Quick network scan"""
        if self.scanning:
            return
        
        self.scanning = True
        base, local_ip = self.get_local_network()
        
        print(f"\n[{self.platform}] Scanning {base}.0/24...")
        if self.distance_mode:
            print("Distance estimation: ENABLED")
        
        # Track previous online status and distances
        previous_online = {ip: device.get('online', False) for ip, device in self.devices.items()}
        previous_distances = {ip: device.get('estimated_distance') for ip, device in self.devices.items()}
        
        # Clear online status
        for device in self.devices.values():
            device['online'] = False
        
        # Quick scan
        online_count = 0
        for i in range(1, 255):
            ip = f"{base}.{i}"
            
            if self.ping(ip):
                online_count += 1
                print(f"✓ {ip}")
                
                if ip not in self.devices:
                    # New device
                    mac = self.get_mac(ip)
                    hostname = self.get_hostname(ip)
                    
                    self.devices[ip] = {
                        'ip': ip,
                        'mac': mac,
                        'hostname': hostname,
                        'vendor': self.get_vendor(mac),
                        'first_seen': datetime.now().isoformat(),
                        'monitored': False,
                        'device_type': 'employee'
                    }
                
                self.devices[ip]['online'] = True
                self.devices[ip]['last_seen'] = datetime.now().isoformat()
                
                # Distance estimation if enabled
                if self.distance_mode:
                    rssi = self.ping_with_stats(ip)
                    distance = self.calculate_distance(rssi)
                    
                    self.devices[ip]['rssi'] = rssi
                    self.devices[ip]['estimated_distance'] = distance
                    
                    # Check for distance changes
                    if self.monitoring and previous_distances.get(ip) and distance:
                        prev_distance = previous_distances[ip]
                        if abs(distance - prev_distance) > 10:  # Significant change
                            prev_zone = self.get_zone(prev_distance)
                            new_zone = self.get_zone(distance)
                            
                            if prev_zone != new_zone:
                                device = self.devices[ip]
                                message = f"{device.get('custom_name', device.get('hostname', ip))} moved from {prev_zone} to {new_zone} ({int(prev_distance)}m → {int(distance)}m)"
                                self.add_alert(device, 'distance', message)
                                print(f"📍 DISTANCE: {message}")
                                
                                # Special alert for leaving site
                                if distance > self.calibration.get('distanceThreshold', 50):
                                    self.play_alert_sound(300, 0.5)  # Low long beep
        
        # Check for departures/arrivals if monitoring
        if self.monitoring:
            for ip, device in self.devices.items():
                if device.get('monitored', False):
                    was_online = previous_online.get(ip, False)
                    is_online = device.get('online', False)
                    
                    if was_online and not is_online:
                        # Departure detected!
                        self.add_alert(device, 'departure')
                        print(f"🚪 DEPARTURE: {device.get('custom_name', device.get('hostname', ip))}")
                        self.play_alert_sound(500, 0.2)  # Low beep
                    
                    elif not was_online and is_online:
                        # Arrival detected!
                        self.add_alert(device, 'arrival')
                        print(f"✅ ARRIVAL: {device.get('custom_name', device.get('hostname', ip))}")
                        self.play_alert_sound(1000, 0.2)  # High beep
        
        self.scanning = False
        self.save_data()
        print(f"Scan complete. {online_count} devices online")
    
    def add_alert(self, device, alert_type, message=None):
        """Add attendance or distance alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'ip': device['ip'],
            'mac': device.get('mac'),
            'device_name': device.get('custom_name', device.get('hostname', 'Unknown')),
            'device_type': device.get('device_type', 'unknown')
        }
        
        if message:
            alert['message'] = message
        
        self.alerts.insert(0, alert)
        
        # Keep only last 1000 alerts
        self.alerts = self.alerts[:1000]
        
        # Log to CSV
        self.log_attendance(alert)
        
        self.save_data()
    
    def log_attendance(self, alert):
        """Log to attendance CSV"""
        import csv
        
        file_exists = self.attendance_file.exists()
        
        with open(self.attendance_file, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['Timestamp', 'Type', 'Name', 'IP', 'MAC', 'Device Type', 'Message'])
            
            writer.writerow([
                alert['timestamp'],
                alert['type'],
                alert['device_name'],
                alert['ip'],
                alert.get('mac', ''),
                alert.get('device_type', ''),
                alert.get('message', '')
            ])
    
    def start_monitoring(self):
        """Start monitoring in background"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                self.scan()
                time.sleep(30)  # Scan every 30 seconds
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False

# Create monitor instance
monitor = CompleteNetworkMonitor()

# Flask app
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/platform_info')
def platform_info():
    return jsonify({
        'platform': f"{platform.system()} {platform.release()}",
        'python': platform.python_version(),
        'hostname': socket.gethostname()
    })

@app.route('/devices')
def get_devices():
    return jsonify(list(monitor.devices.values()))

@app.route('/scan', methods=['POST'])
def scan_network():
    thread = threading.Thread(target=monitor.scan)
    thread.start()
    return jsonify({'status': 'scanning'})

@app.route('/scan_with_distance', methods=['POST'])
def scan_with_distance():
    monitor.distance_mode = True
    thread = threading.Thread(target=monitor.scan)
    thread.start()
    return jsonify({'status': 'scanning with distance'})

@app.route('/toggle_distance', methods=['POST'])
def toggle_distance():
    data = request.get_json()
    monitor.distance_mode = data.get('enabled', False)
    return jsonify({'status': 'updated', 'distance_mode': monitor.distance_mode})

@app.route('/alerts')
def get_alerts():
    return jsonify(monitor.alerts)

@app.route('/update_device', methods=['POST'])
def update_device():
    data = request.get_json()
    ip = data.get('ip')
    
    if ip in monitor.devices:
        device = monitor.devices[ip]
        device['custom_name'] = data.get('name', '')
        device['monitored'] = data.get('monitored', False)
        device['device_type'] = data.get('device_type', 'employee')
        
        monitor.save_data()
        return jsonify({'status': 'updated'})
    
    return jsonify({'error': 'Device not found'}), 404

@app.route('/update_calibration', methods=['POST'])
def update_calibration():
    data = request.get_json()
    monitor.calibration['referenceRSSI'] = data.get('referenceRSSI', -40)
    monitor.calibration['pathLossExponent'] = data.get('pathLossExponent', 2.0)
    monitor.calibration['distanceThreshold'] = data.get('distanceThreshold', 50)
    monitor.save_data()
    return jsonify({'status': 'updated'})

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    monitor.start_monitoring()
    return jsonify({'status': 'started'})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    monitor.stop_monitoring()
    return jsonify({'status': 'stopped'})

@app.route('/clear_alerts', methods=['POST'])
def clear_alerts():
    monitor.alerts = []
    monitor.save_data()
    return jsonify({'status': 'cleared'})

@app.route('/export_attendance')
def export_attendance():
    """Export attendance for a specific date"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Create temporary CSV
    import csv
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Action', 'Name', 'Device Type', 'IP', 'MAC', 'Distance', 'Message'])
        
        for alert in monitor.alerts:
            alert_date = datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d')
            if alert_date == date:
                device = monitor.devices.get(alert['ip'], {})
                distance = device.get('estimated_distance', '')
                
                writer.writerow([
                    datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S'),
                    alert['type'].upper(),
                    alert['device_name'],
                    alert.get('device_type', 'unknown'),
                    alert['ip'],
                    alert.get('mac', ''),
                    f"{distance}m" if distance else '',
                    alert.get('message', '')
                ])
        
        temp_path = f.name
    
    return send_file(temp_path, as_attachment=True, 
                    download_name=f'attendance_{date}.csv',
                    mimetype='text/csv')

def find_available_port():
    """Find an available port"""
    for port in [8000, 8080, 3000, 8888, 5000]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', port))
            s.close()
            return port
        except:
            continue
    return None

def main():
    print("\n" + "="*60)
    print(f"Complete Network Monitor ({platform.system()})")
    print("="*60)
    print("Features: Attendance Tracking + Distance Estimation")
    
    # Platform-specific notes
    if platform.system() == 'Linux':
        print("\n📝 Linux Notes:")
        print("- May need sudo for MAC address detection")
        print("- Install 'beep' for sound alerts: sudo apt-get install beep")
        print("- Ensure 'arp' or 'ip' commands are available")
    elif platform.system() == 'Darwin':
        print("\n📝 macOS Notes:")
        print("- Uses system sounds for alerts")
        print("- May need to allow network access in System Preferences")
    elif platform.system() == 'Windows':
        print("\n📝 Windows Notes:")
        print("- Run as Administrator for best results")
        print("- Windows Defender may prompt for network access")
    
    print("\n📡 Distance Estimation:")
    print("- Based on WiFi signal strength (RSSI)")
    print("- Accuracy: ±5-20m depending on environment")
    print("- Calibrate for your specific location")
    
    print("\n🎯 Distance Zones:")
    print("- On-site: 0-10m")
    print("- Near-site: 10-30m")
    print("- Leaving: 30-50m")
    print("- Away: >50m")
    
    # Find available port
    port = find_available_port()
    
    if not port:
        print("\n❌ No available ports!")
        return
    
    base, local_ip = monitor.get_local_network()
    
    print(f"\n✅ Starting on port {port}")
    print(f"\n📡 Access at:")
    print(f"   http://localhost:{port}")
    print(f"   http://{local_ip}:{port}")
    print(f"\n🌐 Monitoring network: {base}.0/24")
    print("\n⚙️  Features:")
    print("   - Attendance tracking (arrival/departure)")
    print("   - Distance estimation (when enabled)")
    print("   - Cross-platform support")
    print("   - Sound alerts")
    print("   - CSV export")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n\nStopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if platform.system() == 'Linux' and 'Permission' in str(e):
            print("Try running with sudo: sudo python3 script.py")

if __name__ == "__main__":
    if not HAS_FLASK:
        print("\n❌ Flask is required but not installed!")
        print("Install with: pip install flask flask-cors")
        sys.exit(1)
    
    main()