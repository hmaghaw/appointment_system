from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime

bp = Blueprint('appointments', __name__)

@bp.route('/', methods=['GET'])
def get_appointments():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM appointment")
        appointments = cursor.fetchall()
    return jsonify(appointments)

@bp.route('/', methods=['POST'])
def create_appointment():
    data = request.get_json()
    # Add your appointment creation logic here
    return jsonify({"message": "Appointment created"}), 201
