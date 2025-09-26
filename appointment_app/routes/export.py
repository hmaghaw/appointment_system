from flask import Blueprint, jsonify, send_file, request
from ..services.form_polydial_to_clover import Restaurant
from ..database import get_db_cursor
import os
import tempfile

bp = Blueprint('export', __name__, url_prefix='/api/export')


@bp.route('/to_clover', methods=['GET'])
def export_to_clover():
    """
    Export restaurant data to Clover format
    ---
    tags:
      - Export
    security:
      - JWT: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - business_id
          properties:
            business_id:
              type: integer
              description: ID of the business to export
    responses:
      200:
        description: Excel file with Clover-formatted data
        content:
          application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
            schema:
              type: string
              format: binary
      400:
        description: Invalid input
      401:
        description: Unauthorized
    """
    business_id = request.args.get('business_id', type=int)

    if not business_id:
        return jsonify({"error": "business_id is required"}), 400

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            # Initialize and export data
            restaurant = Restaurant(business_id=business_id, xlsx_file=tmp.name)
            restaurant.export_items()

            # Send the file
            return send_file(
                tmp.name,
                as_attachment=True,
                download_name=f"clover_export_business_{business_id}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up the temporary file
        try:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
        except:
            pass