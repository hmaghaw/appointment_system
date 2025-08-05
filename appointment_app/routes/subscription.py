from flask import Blueprint, jsonify, request
from database import get_db_cursor

# Create blueprint
bp = Blueprint('subscription', __name__)

@bp.route('/subscription-plans', methods=['POST'])
def get_subscription_plans():
    """
    Get all subscription plans with their features, grouped by billing cycle
    
    Request Body (JSON):
    {
        "customer_id": 17  # ID of the customer
    }
    
    Returns: JSON object with 'monthly' and 'yearly' arrays of plans,
             with is_current_plan flag set for the customer's current plan
    """
    try:
        data = request.get_json() or {}
        business_id = data.get('business_id')
        
        if not business_id:
            return jsonify({"error": "business_id is required in the request body"}), 400
            
        with get_db_cursor(dictionary=True) as cursor:
            # Get the customer's business and current subscription plan
            cursor.execute("""
                SELECT subscription_plan_id 
                FROM business 
                WHERE business_id = %s
            """, (business_id,))
            
            business = cursor.fetchone()
            if not business:
                return jsonify({"error": "Customer or business not found"}), 404
                
            current_plan_id = business.get('subscription_plan_id')
            
            # Query to get all active subscription plans with their features
            cursor.execute("""
                SELECT 
                    sp.subscription_plan_id,
                    sp.plan_name,
                    sp.plan_description,
                    sp.billing_cycle,
                    sp.original_price,
                    sp.final_price,
                    sp.annual_savings,
                    sp.estimated_monthly_roi,
                    spf.feature_name,
                    spf.feature_value,
                    spf.display_order
                FROM 
                    subscription_plan sp
                LEFT JOIN 
                    subscription_plan_feature spf ON sp.subscription_plan_id = spf.subscription_plan_id
                WHERE 
                    sp.is_active = TRUE
                ORDER BY 
                    sp.billing_cycle,
                    sp.display_order,
                    spf.display_order
            """)
            
            # Process the results
            plans = {}
            button_prefix = "Change to"
            for row in cursor.fetchall():
                button_title = f"{button_prefix} {row['plan_name']}"
                plan_id = row['subscription_plan_id']
                billing_cycle = row['billing_cycle']
                
                # Initialize the billing cycle array if it doesn't exist
                if billing_cycle not in plans:
                    plans[billing_cycle] = {}
                
                # Initialize the plan if it doesn't exist
                if plan_id not in plans[billing_cycle]:
                    if plan_id == current_plan_id:
                        is_current_plan = True
                        button_title = "Current Plan"
                    else:
                        is_current_plan = False
                    plans[billing_cycle][plan_id] = {
                        'subscription_plan_id': plan_id,
                        'plan_name': row['plan_name'],
                        'plan_description': row['plan_description'],
                        'original_price': float(row['original_price']) if row['original_price'] is not None else None,
                        'final_price': float(row['final_price']) if row['final_price'] is not None else None,
                        'estimated_monthly_roi': float(row['estimated_monthly_roi']) if row['estimated_monthly_roi'] is not None else None,
                        'is_current_plan': is_current_plan,
                        'button_title': button_title,

                        'features': []
                    }
                    if is_current_plan:
                        button_prefix = "Change to"
                    # Add annual_savings only if it's not None
                    if row['annual_savings'] is not None:
                        plans[billing_cycle][plan_id]['annual_savings'] = float(row['annual_savings'])
                
                # Add feature if it exists
                if row['feature_name']:
                    plans[billing_cycle][plan_id]['features'].append({
                        'feature_name': row['feature_name'],
                        'feature_value': row['feature_value']
                    })
            
            # Convert the nested dictionaries to the required format
            result = {
                'monthly': list(plans.get('monthly', {}).values()),
                'yearly': list(plans.get('yearly', {}).values())
            }
            
            return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch subscription plans',
            'details': str(e)
        }), 500
