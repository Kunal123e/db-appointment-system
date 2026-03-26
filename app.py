import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

# 🔗 MongoDB Atlas Connection (from ENV variable)
uri = os.environ.get("MONGO_URI")
client = MongoClient(uri)

# Database & Collection
db = client["appointmentDB"]
collection = db["appointments"]

# Home Page
@app.route("/")
def index():
    appointments = collection.find().sort("datetime", 1)
    return render_template("index.html", appointments=appointments)

# Add Appointment
@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    date = request.form.get("date")
    time = request.form.get("time")
    purpose = request.form.get("purpose")

    if not name or not date or not time or not purpose:
        return "All fields are required!"

    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    # Prevent double booking
    existing = collection.find_one({"datetime": dt})
    if existing:
        return "Time slot already booked!"

    data = {
        "user": {
            "name": name
        },
        "datetime": dt,
        "purpose": purpose,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    collection.insert_one(data)
    return redirect(url_for("index"))

# Delete Appointment
@app.route("/delete/<id>")
def delete(id):
    collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("index"))

# Update Page
@app.route("/update/<id>")
def update_page(id):
    appointment = collection.find_one({"_id": ObjectId(id)})
    return render_template("update.html", appointment=appointment)

# Update Appointment
@app.route("/update/<id>", methods=["POST"])
def update(id):
    name = request.form.get("name")
    date = request.form.get("date")
    time = request.form.get("time")
    purpose = request.form.get("purpose")

    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    # Prevent double booking except current record
    existing = collection.find_one({
        "datetime": dt,
        "_id": {"$ne": ObjectId(id)}
    })

    if existing:
        return "Time slot already booked!"

    collection.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "user.name": name,
                "datetime": dt,
                "purpose": purpose,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return redirect(url_for("index"))

# Change Status
@app.route("/status/<id>/<new_status>")
def change_status(id, new_status):
    allowed = ["pending", "completed", "cancelled"]

    if new_status not in allowed:
        return "Invalid status!"

    collection.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return redirect(url_for("index"))

# Search Appointment
@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword")

    results = collection.find({
        "user.name": {"$regex": keyword, "$options": "i"}
    })

    return render_template("index.html", appointments=results)

# Run App
if __name__ == "__main__":
    app.run()
