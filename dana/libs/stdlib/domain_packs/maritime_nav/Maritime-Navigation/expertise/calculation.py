import math

def parse_position(position_str: str) -> tuple:
    """Parse position string like '01°15.0'N, 103°45.0'E' to decimal degrees."""
    # Remove spaces and split by comma
    parts = position_str.replace(' ', '').split(',')
    if len(parts) != 2:
        return (0.0, 0.0)
    
    lat_str, lon_str = parts
    
    # Parse latitude
    lat_deg = 0.0
    if '°' in lat_str and 'N' in lat_str:
        deg_part = lat_str.split('°')[0]
        min_part = lat_str.split('°')[1].split('N')[0]
        lat_deg = float(deg_part) + float(min_part) / 60.0
    elif '°' in lat_str and 'S' in lat_str:
        deg_part = lat_str.split('°')[0]
        min_part = lat_str.split('°')[1].split('S')[0]
        lat_deg = -(float(deg_part) + float(min_part) / 60.0)
    
    # Parse longitude
    lon_deg = 0.0
    if '°' in lon_str and 'E' in lon_str:
        deg_part = lon_str.split('°')[0]
        min_part = lon_str.split('°')[1].split('E')[0]
        lon_deg = float(deg_part) + float(min_part) / 60.0
    elif '°' in lon_str and 'W' in lon_str:
        deg_part = lon_str.split('°')[0]
        min_part = lon_str.split('°')[1].split('W')[0]
        lon_deg = -(float(deg_part) + float(min_part) / 60.0)
    
    return (lat_deg, lon_deg)


def calculate_distance_between_vessels(vessel_a_pos: str, vessel_b_pos: str) -> float:
    """Calculate distance between two vessels using Haversine formula."""
    lat1, lon1 = parse_position(vessel_a_pos)
    lat2, lon2 = parse_position(vessel_b_pos)
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in nautical miles
    earth_radius_nm = 3440.065
    distance = earth_radius_nm * c
    
    return round(distance, 2)


def calculate_relative_bearing(vessel_a_pos: str, vessel_b_pos: str, vessel_a_course: float) -> float:
    """Calculate relative bearing from Vessel A to Vessel B."""
    lat1, lon1 = parse_position(vessel_a_pos)
    lat2, lon2 = parse_position(vessel_b_pos)
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate bearing
    dlon = lon2_rad - lon1_rad
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    
    bearing = math.degrees(math.atan2(y, x))
    bearing = (bearing + 360) % 360  # Normalize to 0-360
    
    return round(bearing, 1)


def calculate_relative_speed(vessel_a_speed: float, vessel_a_course: float, 
                           vessel_b_speed: float, vessel_b_course: float) -> float:
    """Calculate relative speed between two vessels."""
    # Convert courses to radians
    course_a_rad = math.radians(vessel_a_course)
    course_b_rad = math.radians(vessel_b_course)
    
    # Calculate velocity components
    v_a_x = vessel_a_speed * math.sin(course_a_rad)
    v_a_y = vessel_a_speed * math.cos(course_a_rad)
    v_b_x = vessel_b_speed * math.sin(course_b_rad)
    v_b_y = vessel_b_speed * math.cos(course_b_rad)
    
    # Calculate relative velocity
    v_rel_x = v_b_x - v_a_x
    v_rel_y = v_b_y - v_a_y
    
    # Calculate relative speed magnitude
    relative_speed = math.sqrt(v_rel_x**2 + v_rel_y**2)
    
    return round(relative_speed, 1)


def calculate_cpa(vessel_a_pos: str, vessel_a_speed: float, vessel_a_course: float,
                 vessel_b_pos: str, vessel_b_speed: float, vessel_b_course: float) -> float:
    """Calculate Closest Point of Approach (CPA) in nautical miles."""
    # Get initial positions
    lat1, lon1 = parse_position(vessel_a_pos)
    lat2, lon2 = parse_position(vessel_b_pos)
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Convert courses to radians
    course_a_rad = math.radians(vessel_a_course)
    course_b_rad = math.radians(vessel_b_course)
    
    # Calculate velocity components (knots to nm/min)
    v_a_x = (vessel_a_speed / 60.0) * math.sin(course_a_rad)
    v_a_y = (vessel_a_speed / 60.0) * math.cos(course_a_rad)
    v_b_x = (vessel_b_speed / 60.0) * math.sin(course_b_rad)
    v_b_y = (vessel_b_speed / 60.0) * math.cos(course_b_rad)
    
    # Calculate relative velocity
    v_rel_x = v_b_x - v_a_x
    v_rel_y = v_b_y - v_a_y
    
    # Calculate relative position (convert to nm)
    earth_radius_nm = 3440.065
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Approximate conversion to nm (good for small distances)
    x_rel = dlon * earth_radius_nm * math.cos((lat1_rad + lat2_rad) / 2)
    y_rel = dlat * earth_radius_nm
    
    # Calculate CPA using vector projection
    if v_rel_x**2 + v_rel_y**2 == 0:
        # Vessels have same velocity, CPA is current distance
        cpa = math.sqrt(x_rel**2 + y_rel**2)
    else:
        # Calculate time to CPA
        t_cpa = -(x_rel * v_rel_x + y_rel * v_rel_y) / (v_rel_x**2 + v_rel_y**2)
        
        if t_cpa < 0:
            # CPA was in the past, current distance is minimum
            cpa = math.sqrt(x_rel**2 + y_rel**2)
        else:
            # Calculate CPA distance
            x_cpa = x_rel + v_rel_x * t_cpa
            y_cpa = y_rel + v_rel_y * t_cpa
            cpa = math.sqrt(x_cpa**2 + y_cpa**2)
    
    return round(cpa, 2)


def calculate_time_to_cpa(vessel_a_pos: str, vessel_a_speed: float, vessel_a_course: float,
                         vessel_b_pos: str, vessel_b_speed: float, vessel_b_course: float) -> float:
    """Calculate Time to Closest Point of Approach in minutes."""
    # Get initial positions
    lat1, lon1 = parse_position(vessel_a_pos)
    lat2, lon2 = parse_position(vessel_b_pos)
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Convert courses to radians
    course_a_rad = math.radians(vessel_a_course)
    course_b_rad = math.radians(vessel_b_course)
    
    # Calculate velocity components (knots to nm/min)
    v_a_x = (vessel_a_speed / 60.0) * math.sin(course_a_rad)
    v_a_y = (vessel_a_speed / 60.0) * math.cos(course_a_rad)
    v_b_x = (vessel_b_speed / 60.0) * math.sin(course_b_rad)
    v_b_y = (vessel_b_speed / 60.0) * math.cos(course_b_rad)
    
    # Calculate relative velocity
    v_rel_x = v_b_x - v_a_x
    v_rel_y = v_b_y - v_a_y
    
    # Calculate relative position (convert to nm)
    earth_radius_nm = 3440.065
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Approximate conversion to nm (good for small distances)
    x_rel = dlon * earth_radius_nm * math.cos((lat1_rad + lat2_rad) / 2)
    y_rel = dlat * earth_radius_nm
    
    # Calculate time to CPA
    if v_rel_x**2 + v_rel_y**2 == 0:
        # Vessels have same velocity, no CPA
        return float('inf')
    else:
        t_cpa = -(x_rel * v_rel_x + y_rel * v_rel_y) / (v_rel_x**2 + v_rel_y**2)
        if t_cpa < 0:
            # CPA was in the past
            return 0.0
        else:
            return round(t_cpa, 1)
