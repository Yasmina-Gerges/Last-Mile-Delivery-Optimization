from flask import Flask, request, jsonify
from ortools.linear_solver import pywraplp
import math

app = Flask(__name__)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

@app.route('/solve_routes', methods=['POST'])
def solve_routes():
    try:
        data = request.get_json()
        
        riders = data['riders']
        orders = data['orders']
        rider_positions = data['rider_positions']
        rider_speed = data.get('rider_speed', 50)
        fixed_rider_cost = data.get('fixed_rider_cost', 1.2)
        distance_cost_per_km = data.get('distance_cost', 0.22)  # ADDED: get distance cost from Java
        
        num_riders = len(riders)
        num_orders = len(orders)
        
        # Get current time
        current_time = 0
        if orders:
            current_time = orders[0].get('order_time', 0)
        
        # Build distance matrix and check feasibility
        distance_matrix = []
        feasible_matrix = []
        
        for i in range(num_riders):
            dist_row = []
            feasible_row = []
            for j in range(num_orders):
                # ===== MODIFIED: Pickup and Delivery Modeling =====
                # Calculate distance from rider to restaurant (pickup)
                dist_to_restaurant = haversine_distance(
                    rider_positions[i]['lat'], rider_positions[i]['lon'],
                    orders[j]['restaurant_lat'], orders[j]['restaurant_lon']
                )
                
                # Calculate distance from restaurant to customer (delivery)
                dist_to_customer = haversine_distance(
                    orders[j]['restaurant_lat'], orders[j]['restaurant_lon'],
                    orders[j]['customer_lat'], orders[j]['customer_lon']
                )
                
                # Total distance = rider -> restaurant -> customer
                dist = dist_to_restaurant + dist_to_customer
                dist_row.append(dist)
                
                # Check if delivery is feasible within deadline
                travel_time = dist / rider_speed
                order_time = orders[j].get('order_time', current_time)
                deadline = orders[j].get('customer_deadline', 2.0)
                arrival_time = current_time + travel_time
                latest_allowed = order_time + deadline
                
                feasible = arrival_time <= latest_allowed
                feasible_row.append(1 if feasible else 0)
                
                if not feasible:
                    print(f"Rider {riders[i]['id']} cannot deliver order {orders[j]['id']} within deadline")
            
            distance_matrix.append(dist_row)
            feasible_matrix.append(feasible_row)
        
        # Create solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        
        # Decision variables
        x = {}
        for i in range(num_riders):
            for j in range(num_orders):
                if feasible_matrix[i][j]:
                    x[i, j] = solver.IntVar(0, 1, f'x_{i}_{j}')
        
        y = {}
        for i in range(num_riders):
            y[i] = solver.IntVar(0, 1, f'y_{i}')
        
        # Each order assigned to exactly one feasible rider
        for j in range(num_orders):
            feasible_riders = [x[i, j] for i in range(num_riders) if feasible_matrix[i][j]]
            if feasible_riders:
                solver.Add(solver.Sum(feasible_riders) == 1)
            else:
                print(f"ERROR: Order {orders[j]['id']} has no feasible riders!")
                return jsonify({'status': 'no_solution_found', 'reason': 'no_feasible_rider'}), 400
        
        # Link x and y
        M = num_orders
        for i in range(num_riders):
            if any(feasible_matrix[i][j] for j in range(num_orders)):
                solver.Add(solver.Sum([x[i, j] for j in range(num_orders) if feasible_matrix[i][j]]) <= M * y[i])
        
        # Each rider takes at most 1 order
        for i in range(num_riders):
            if any(feasible_matrix[i][j] for j in range(num_orders)):
                solver.Add(solver.Sum([x[i, j] for j in range(num_orders) if feasible_matrix[i][j]]) <= 1)
        
        # ===== CORRECTED OBJECTIVE FUNCTION =====
        # Fixed cost for active riders
        objective = solver.Sum([fixed_rider_cost * y[i] for i in range(num_riders)])
        # Distance cost with proper multiplier (distance × cost per km)
        for i in range(num_riders):
            for j in range(num_orders):
                if feasible_matrix[i][j]:
                    objective += distance_matrix[i][j] * distance_cost_per_km * x[i, j]
        solver.Minimize(objective)
        
        status = solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL:
            assignments = []
            riders_used_set = set()
            total_distance = 0
            
            for i in range(num_riders):
                for j in range(num_orders):
                    if feasible_matrix[i][j] and x[i, j].solution_value() > 0.5:
                        assignments.append({
                            'rider_id': riders[i]['id'],
                            'order_id': orders[j]['id'],
                            'distance': distance_matrix[i][j]
                        })
                        total_distance += distance_matrix[i][j]
                        riders_used_set.add(riders[i]['id'])
            
            # Calculate total cost using the same formula as objective
            total_distance_cost = total_distance * distance_cost_per_km
            total_fixed_cost = len(riders_used_set) * fixed_rider_cost
            total_cost = total_distance_cost + total_fixed_cost
            
            routes = []
            for rider_id in riders_used_set:
                order_list = []
                for a in assignments:
                    if a['rider_id'] == rider_id:
                        order_list.append(a['order_id'])
                routes.append({
                    'rider_id': rider_id,
                    'order_sequence': order_list,
                    'total_distance': 0
                })
            
            print(f"SUCCESS: {len(assignments)} orders assigned to {len(routes)} riders")
            print(f"Total distance: {total_distance:.2f} km")
            print(f"Total cost: ${total_cost:.2f} (${total_distance_cost:.2f} distance + ${total_fixed_cost:.2f} fixed)")
            
            return jsonify({
                'status': 'optimal',
                'total_distance': total_distance,
                'total_cost': total_cost,  # Now returns correct total cost
                'riders_used': len(riders_used_set),
                'routes': routes,
                'assignments': assignments
            })
        else:
            print("No solution found by solver")
            return jsonify({'status': 'no_solution_found'}), 400
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)