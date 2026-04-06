from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import date

app = Flask(__name__)

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"students": [], "attendance": {}, "classes": ["Mathematics", "Physics", "Chemistry", "Computer Science", "English"]}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html',
        students=data["students"],
        classes=data["classes"],
        today=str(date.today())
    )

@app.route('/stats')
def stats():
    data = load_data()
    today = request.args.get('date', str(date.today()))
    branch = request.args.get('branch', 'All')

    students = data["students"]
    if branch != 'All':
        students = [s for s in students if s.get("branch") == branch]

    sids = {s["id"] for s in students}

    present_today = sum(
        1 for sid in sids
        if data["attendance"].get(sid, {}).get(today) == "present"
    )

    all_records = [v for sid, v in data["attendance"].items() if sid in sids]
    total_records = sum(len(v) for v in all_records)
    present_records = sum(sum(1 for s in v.values() if s == "present") for v in all_records)
    overall_pct = round((present_records / total_records * 100), 1) if total_records > 0 else 0

    return jsonify({
        "total_students": len(students),
        "present_today": present_today,
        "overall_pct": overall_pct
    })

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    req = request.get_json()
    date_str = req.get('date', str(date.today()))
    records = req.get('records', {})

    data = load_data()
    for sid, status in records.items():
        if sid not in data["attendance"]:
            data["attendance"][sid] = {}
        data["attendance"][sid][date_str] = status
    save_data(data)

    present = sum(1 for s in records.values() if s == "present")
    absent = len(records) - present
    return jsonify({"success": True, "present": present, "absent": absent})

@app.route('/report')
def report():
    data = load_data()
    report_data = []
    for s in data["students"]:
        records = data["attendance"].get(s["id"], {})
        total = len(records)
        present = sum(1 for v in records.values() if v == "present")
        pct = round((present / total * 100), 1) if total > 0 else 0
        report_data.append({
            **s,
            "total_classes": total,
            "present": present,
            "absent": total - present,
            "percentage": pct,
            "status": "Good" if pct >= 75 else ("Average" if pct >= 60 else "Low")
        })
    return jsonify(report_data)

@app.route('/add_student', methods=['POST'])
def add_student():
    req = request.get_json()
    data = load_data()
    new_id = f"S{str(len(data['students'])+1).zfill(3)}"
    student = {
        "id": new_id,
        "name": req["name"],
        "roll": req["roll"],
        "branch": req.get("branch", "IT")
    }
    data["students"].append(student)
    data["attendance"][new_id] = {}
    save_data(data)
    return jsonify({"success": True, "student": student})

if __name__ == '__main__':
    app.run(debug=True)
