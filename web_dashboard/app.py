from flask import Flask, render_template, jsonify, request
import threading
import time

app = Flask(__name__)

sim_state = {
    "status": "Idle",              
    "current_station": "Station A",
    "pickup_target": "None",
    "dropoff_target": "None",
    "progress": 0.0,               
    "passenger_in_seat": False,    
    "debounce_counter": 0,
}

STATION_POSITIONS = {"Station A": 0.0, "Station B": 25.0, "Station C": 50.0, "Station D": 75.0}
DEBOUNCE_THRESHOLD = 4

def update_vehicle_physics():
    global sim_state
    while True:
        time.sleep(0.05) 
        
        # 1. AUTO-EMERGENCY STOP (Passenger falls out mid-transit)
        if sim_state["status"] == "In Transit" and not sim_state["passenger_in_seat"]:
            sim_state["status"] = "Emergency Stop"
            print("🚨 AUTO-BRAKE: Passenger lost mid-transit!")
            continue

        # If in Emergency Stop, FREEZE coordinates. Do not update progress.
        if sim_state["status"] == "Emergency Stop":
            continue

        # 2. DEBOARDING LOGIC
        if sim_state["status"] == "Waiting for Disembark":
            if not sim_state["passenger_in_seat"]:
                sim_state["status"] = "Idle"
                sim_state["pickup_target"] = "None"
                sim_state["dropoff_target"] = "None"
            continue

        # 3. MOVEMENT LOGIC
        if sim_state["status"] in ["Heading to Pickup", "In Transit"]:
            target = sim_state["pickup_target"] if sim_state["status"] == "Heading to Pickup" else sim_state["dropoff_target"]
            target_pos = STATION_POSITIONS[target]
            
            sim_state["progress"] = (sim_state["progress"] + 0.3) % 100.0
            
            diff = abs(sim_state["progress"] - target_pos)
            if diff < 1.0 or diff > 99.0: 
                sim_state["progress"] = target_pos
                sim_state["current_station"] = target
                
                if sim_state["status"] == "Heading to Pickup":
                    sim_state["status"] = "Arrived at Pickup"
                elif sim_state["status"] == "In Transit":
                    sim_state["status"] = "Waiting for Disembark"

threading.Thread(target=update_vehicle_physics, daemon=True).start()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/telemetry', methods=['GET'])
def get_telemetry(): return jsonify(sim_state)

@app.route('/book_trip', methods=['POST'])
def book_trip():
    data = request.json
    sim_state["pickup_target"] = data.get('pickup')
    sim_state["dropoff_target"] = data.get('dropoff')
    sim_state["status"] = "Arrived at Pickup" if sim_state["current_station"] == sim_state["pickup_target"] else "Heading to Pickup"
    return jsonify({"success": True})

@app.route('/action', methods=['POST'])
def vehicle_action():
    action = request.json.get('command')
    
    if action == "start":
        if not sim_state["passenger_in_seat"]: return jsonify({"success": False, "msg": "Please board the vehicle first."})
        sim_state["status"] = "In Transit"
    elif action == "emergency_stop":
        sim_state["status"] = "Emergency Stop"
    elif action == "resume":
        if not sim_state["passenger_in_seat"]: return jsonify({"success": False, "msg": "Passenger must be securely seated to resume."})
        sim_state["status"] = "In Transit"
        
    return jsonify({"success": True})

@app.route('/camera_feed_update', methods=['POST'])
def camera_feed_update():
    if request.json.get('duck_detected', False):
        sim_state["debounce_counter"] = 0
        sim_state["passenger_in_seat"] = True
    else:
        if sim_state["status"] in ["Arrived at Pickup", "In Transit", "Waiting for Disembark"]:
            sim_state["debounce_counter"] += 1
            if sim_state["debounce_counter"] >= DEBOUNCE_THRESHOLD:
                sim_state["passenger_in_seat"] = False
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)