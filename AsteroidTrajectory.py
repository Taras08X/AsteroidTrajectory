from vpython import *
import math
import folium
import webbrowser
import os
import time

# Constants
G = 6.67430e-11  # Gravitational constant
AU = 1.496e11    # Astronomical unit in meters
EARTH_ROTATION_PERIOD = 86400  # Earth's rotation period in seconds (1 day)
MOON_DISTANCE = 384400 * 1000  # Distance to Moon in meters
EARTH_RADIUS = 6.371e6  # Earth's radius in meters

# Zoom limits
MIN_ZOOM_RANGE = 1.2 * AU  # Minimum zoom distance
MAX_ZOOM_RANGE = 10 * AU   # Maximum zoom distance

# Planet data with scaled-up sizes for visibility
PLANET_DATA = {
    'Sun': {'mass': 1.989e30, 'radius': 0.25, 'distance': 0, 'velocity': 0, 'color': color.yellow, 'trail': color.orange},
    'Earth': {'mass': 5.972e24, 'radius': 0.12, 'distance': 1.0, 'velocity': 29.78, 'color': color.white, 'trail': color.cyan},
    'Moon': {'mass': 7.347e22, 'radius': 0.055, 'distance': 0.00257, 'velocity': 1.022, 'color': color.white, 'trail': vector(0.9,0.9,0.9), 'parent': 'Earth'}
}

# Real asteroids database
REAL_ASTEROIDS = {
    "99942 Apophis": {
        "description": "Potentially hazardous asteroid, closest approach to Earth in 2029",
        "diameter_km": 0.34,
        "mass_kg": 6.1e10,
        "orbit_distance_au": 1.1,
        "velocity_kms": 30.7,
        "threat_level": "Medium",
        "discovery_year": 2004,
        "coordinates": [40.7128, -74.0060]  # New York
    },
    "101955 Bennu": {
        "description": "B-type asteroid, target of OSIRIS-REx mission",
        "diameter_km": 0.49,
        "mass_kg": 7.8e10,
        "orbit_distance_au": 1.2,
        "velocity_kms": 28.0,
        "threat_level": "Low",
        "discovery_year": 1999,
        "coordinates": [51.5074, -0.1278]  # London
    },
    "1 Ceres": {
        "description": "Largest object in the asteroid belt, dwarf planet",
        "diameter_km": 939.4,
        "mass_kg": 9.1e20,
        "orbit_distance_au": 2.8,
        "velocity_kms": 17.9,
        "threat_level": "None",
        "discovery_year": 1801,
        "coordinates": [41.9028, 12.4964]  # Rome
    },
    "4 Vesta": {
        "description": "Second most massive asteroid in the asteroid belt",
        "diameter_km": 525.4,
        "mass_kg": 2.6e20,
        "orbit_distance_au": 2.4,
        "velocity_kms": 19.3,
        "threat_level": "None",
        "discovery_year": 1807,
        "coordinates": [48.8566, 2.3522]  # Paris
    },
    "1036 Ganymed": {
        "description": "Large Amor-type asteroid, first discovered of its type",
        "diameter_km": 31.7,
        "mass_kg": 3.3e16,
        "orbit_distance_au": 1.6,
        "velocity_kms": 23.5,
        "threat_level": "Very Low",
        "discovery_year": 1924,
        "coordinates": [52.5200, 13.4050]  # Berlin
    },
    "1566 Icarus": {
        "description": "Apollo group asteroid with highly eccentric orbit",
        "diameter_km": 1.4,
        "mass_kg": 3.6e12,
        "orbit_distance_au": 1.1,
        "velocity_kms": 34.0,
        "threat_level": "Low",
        "discovery_year": 1949,
        "coordinates": [35.6762, 139.6503]  # Tokyo
    },
    "433 Eros": {
        "description": "Amor group asteroid, first asteroid orbited by a spacecraft",
        "diameter_km": 16.8,
        "mass_kg": 6.7e15,
        "orbit_distance_au": 1.5,
        "velocity_kms": 24.4,
        "threat_level": "Very Low",
        "discovery_year": 1898,
        "coordinates": [55.7558, 37.6176]  # Moscow
    },
    "2101 Adonis": {
        "description": "Apollo group asteroid, potentially hazardous object",
        "diameter_km": 1.0,
        "mass_kg": 1.8e12,
        "orbit_distance_au": 1.0,
        "velocity_kms": 31.2,
        "threat_level": "Medium",
        "discovery_year": 1936,
        "coordinates": [50.4501, 30.5234]  # Kyiv
    }
}

class CelestialBody:
    def __init__(self, name, mass, pos, vel, radius, body_color, trail_color):
        self.name = name
        self.mass = mass
        self.pos = vector(pos[0], pos[1], pos[2])
        self.vel = vector(vel[0], vel[1], vel[2])
        self.force = vector(0, 0, 0)
        self.rotation_angle = 0
        self.original_radius = radius
        self.current_radius = radius
        self.destroyed = False
        
        # Create sphere with enhanced visual effects and textures
        if name == "Sun":
            # Sun with glow effect
            self.sphere = sphere(
                pos=self.pos,
                radius=radius * AU,
                color=color.yellow,
                make_trail=True,
                trail_color=trail_color,
                trail_radius=radius * AU * 0.1,
                shininess=1.0,
                emissive=True
            )
            # Additional glow
            self.glow = sphere(
                pos=self.pos,
                radius=radius * AU * 1.4,
                color=color.orange,
                opacity=0.2
            )
            # Inner glow
            self.inner_glow = sphere(
                pos=self.pos,
                radius=radius * AU * 1.1,
                color=color.red,
                opacity=0.1
            )
            
        elif name == "Earth":
            # Earth with texture and atmosphere
            self.sphere = sphere(
                pos=self.pos,
                radius=radius * AU,
                color=vector(1, 1, 1),
                make_trail=True,
                trail_color=trail_color,
                trail_radius=radius * AU * 0.01,
                shininess=0.7,
                texture=textures.earth
            )
            # Add atmosphere
            self.atmosphere = sphere(
                pos=self.pos,
                radius=radius * AU * 1.05,
                color=vector(0.4, 0.7, 1.0),
                opacity=0.3
            )
            
        else:
            # Asteroid or Moon
            self.sphere = sphere(
                pos=self.pos,
                radius=radius * AU,
                color=body_color,
                make_trail=True,
                trail_color=trail_color,
                trail_radius=radius * AU * 0.05,
                shininess=0.1
            )

    def update_rotation(self, time_step):
        """Update planet rotation"""
        if self.name == "Earth":
            # Earth rotation around its axis
            rotation_speed = 2 * math.pi / EARTH_ROTATION_PERIOD  # radians per second
            self.rotation_angle += rotation_speed * time_step
            
            # Visual rotation effect through color change
            rotation_factor = math.sin(self.rotation_angle) * 0.1 + 1.0
            self.sphere.color = vector(0.2 * rotation_factor, 0.5, 1.0 * rotation_factor)
            
            # Rotate atmosphere
            if hasattr(self, 'atmosphere'):
                self.atmosphere.rotate(angle=rotation_speed * time_step, axis=vector(0, 0, 1))
        
        elif self.name == "Moon":
            # Moon rotation around its axis (synchronized with orbit)
            rotation_speed = 2 * math.pi / (27.3 * 24 * 3600)  # 27.3 days
            self.rotation_angle += rotation_speed * time_step

    def scale_for_distance(self, distance_factor):
        """Scale object size based on distance for better visibility"""
        if self.name in ["Earth", "Asteroid"]:
            # Increase size when closer
            scale_factor = max(1.0, 5.0 / (distance_factor + 1.0))
            self.current_radius = self.original_radius * scale_factor
            self.sphere.radius = self.current_radius * AU
            
            if hasattr(self, 'atmosphere'):
                self.atmosphere.radius = self.current_radius * AU * 1.05

def calculate_gravitational_force(body1, body2):
    """Calculate gravitational force between two bodies"""
    r_vec = body2.pos - body1.pos
    r_mag = mag(r_vec)
    if r_mag == 0:
        return vector(0, 0, 0)
    
    r_unit = r_vec / r_mag
    force_mag = G * body1.mass * body2.mass / (r_mag ** 2)
    return force_mag * r_unit

def calculate_moon_orbital_velocity(earth_mass, distance):
    """Calculate Moon's orbital velocity for circular orbit around Earth"""
    return math.sqrt(G * earth_mass / distance)

def create_moon_orbit_line(earth_pos, radius):
    """Create a thin Moon orbit line"""
    orbit_points = []
    num_points = 100
    
    for i in range(num_points + 1):  # +1 to close the circle
        angle = 2 * math.pi * i / num_points
        x = earth_pos.x + radius * math.cos(angle)
        y = earth_pos.y + radius * math.sin(angle)
        z = earth_pos.z
        orbit_points.append(vector(x, y, z))
    
    return curve(
        pos=orbit_points,
        color=vector(0.7, 0.7, 0.7),
        radius=radius * 0.002,  # Very thin line
        opacity=0.6
    )

def create_explosion(pos, size=1.0):
    """Create explosion effect"""
    explosion_effects = []
    
    # Main explosion
    explosion_sphere = sphere(
        pos=pos,
        radius=size * AU * 0.3,
        color=color.orange,
        opacity=0.8,
        emissive=True
    )
    explosion_effects.append(explosion_sphere)
    
    # Inner explosion
    inner_explosion = sphere(
        pos=pos,
        radius=size * AU * 0.15,
        color=color.yellow,
        opacity=0.9,
        emissive=True
    )
    explosion_effects.append(inner_explosion)
    
    # Particles
    for i in range(20):
        angle = random() * 2 * math.pi
        speed = random() * AU * 0.001
        particle_pos = pos + vector(
            cos(angle) * speed * 0.1,
            sin(angle) * speed * 0.1,
            (random() - 0.5) * speed * 0.1
        )
        
        particle = sphere(
            pos=particle_pos,
            radius=size * AU * 0.02,
            color=vector(1, random() * 0.5, 0),
            emissive=True
        )
        explosion_effects.append(particle)
    
    return explosion_effects

def animate_explosion(explosion_effects, frame_count):
    """Animate explosion effect"""
    if frame_count > 100:
        # Remove effects after 100 frames
        for effect in explosion_effects:
            if effect.visible:
                effect.visible = False
                del effect
        return []
    
    # Increase explosion size
    opacity = max(0, 1 - frame_count * 0.01)
    
    if explosion_effects:  # Check if list is not empty
        for i, effect in enumerate(explosion_effects):
            if effect.visible:
                if i < 2:  # Main explosion spheres
                    effect.radius *= 1.02
                    effect.opacity = opacity
                else:  # Particles
                    # Move particles outward
                    if len(explosion_effects) > 0:
                        direction = effect.pos - explosion_effects[0].pos
                        if mag(direction) > 0:
                            effect.pos += direction * 0.001
                    effect.opacity = opacity
    
    return explosion_effects

def create_impact_map(lat, lon, mass, velocity, angle_deg):
    """Create 2D impact map for asteroid"""
    print(f"Creating impact map for coordinates: {lat}, {lon}")
    
    # Calculate energy
    total_energy = 0.5 * mass * velocity**2
    angle_radians = math.radians(angle_deg)
    effective_energy = total_energy * math.sin(angle_radians)
    
    # Classify asteroid
    if effective_energy < 1e15:
        category = "Small"
        consequences = "Local damage, minor atmospheric effects."
        scale_factor = 3
    elif effective_energy < 1e18:
        category = "Medium"
        consequences = "Significant destruction, strong shockwave."
        scale_factor = 8
    else:
        category = "Large"
        consequences = "Global consequences, significant climate impact."
        scale_factor = 20
    
    # Calculate impact radius
    base_radius = (effective_energy ** (1/3.85)) * scale_factor / 1000  # km
    if base_radius > 20000:
        base_radius = 20000  # Limit to Earth's size
    
    print(f"Asteroid category: {category}")
    print(f"Effective energy: {effective_energy:.2e} J")
    print(f"Impact radius: {base_radius:.1f} km")
    
    # Risk zones
    zones = [
        (base_radius * 0.3, 'red', 'High-risk zone'),
        (base_radius * 0.6, 'orange', 'Medium-risk zone'),
        (base_radius, 'yellow', 'Low-risk zone')
    ]
    
    # Create map
    zoom = 6 if base_radius < 200 else 4 if base_radius < 800 else 3

    bounds = [
        [lat - 90, lon - 180],
        [lat + 90, lon + 180]
    ]

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        min_zoom=2,
        max_zoom=8,
        max_bounds=True
    )
    m.fit_bounds(bounds)
    
    # Impact point marker
    folium.Marker(
        location=[lat, lon],
        popup=(f"Asteroid impact\n"
               f"Mass: {mass:.2e} kg\n"
               f"Velocity: {velocity:.2e} m/s\n"
               f"Angle: {angle_deg}°\n"
               f"Energy: {effective_energy:.2e} J\n"
               f"Category: {category}\n"
               f"Consequences: {consequences}"),
        icon=folium.Icon(color="red", icon="star")
    ).add_to(m)
    
    # Colored risk zones
    for radius_km, color, label in zones:
        folium.Circle(
            location=[lat, lon],
            radius=radius_km * 1000,
            color=color,
            fill=True,
            fill_opacity=0.3,
            popup=f"{label} ({radius_km:.1f} km)"
        ).add_to(m)
    
    # Save and open map
    output_file = "asteroid_impact_map.html"
    m.save(output_file)
    print(f"Map saved as '{output_file}'")
    
    # Automatically open in browser
    try:
        webbrowser.open(f'file://{os.path.abspath(output_file)}')
        print("Map opened in browser!")
    except Exception as e:
        print(f"Failed to open browser: {e}")
    
    return output_file

def limit_camera_zoom():
    """Limit camera zoom"""
    if scene.range < MIN_ZOOM_RANGE:
        scene.range = MIN_ZOOM_RANGE
    elif scene.range > MAX_ZOOM_RANGE:
        scene.range = MAX_ZOOM_RANGE

def set_camera_center_to_sun():
    """Set camera center to Sun"""
    scene.center = vector(0, 0, 0)

# Create scene with enhanced design
scene = canvas(
    title="Asteroid Simulation",
    width=1920,
    height=800,
    center=vector(0,0,0),
    background=color.black
)
scene.width = 2000
scene.height = 800

# Add background stars
for i in range(100):
    star_pos = vector(
        random() * 10 * AU - 5 * AU,
        random() * 10 * AU - 5 * AU, 
        random() * 10 * AU - 5 * AU
    )
    sphere(
        pos=star_pos,
        radius=AU * 0.002,
        color=color.white,
        emissive=True
    )

# Global variables
bodies = []
running = False
pre_simulation_running = True  # For initial motion
time_step = 86400 * 0.1  # 0.1 days
moon_orbit_curve = None
auto_zoom_enabled = True
impact_occurred = False
explosion_effects = []
explosion_frame_count = 0
default_camera_range = 2.8 * AU
zoomed_in = False
map_created = False

# User interface and styles
scene.append_to_caption("""
<style>
    body {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        background: radial-gradient(ellipse at center,  #0B0C23 0%, #000000 100%);
        color: #ffffff;
        line-height: 1.6;
        padding: 20px;
    }
    
    .section {
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, rgba(85, 98, 112, 0.1) 100%);
        border: 1px solid rgba(78, 205, 196, 0.3);
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
    }
    
    .section h2, .section h3 {
        color: #4ecdc4;
        margin-bottom: 20px;
    }
    
    button {
        background: rgba(78, 205, 196, 0.2) !important;
        border: 1px solid rgba(78, 205, 196, 0.5) !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        color: #4ecdc4 !important;
        cursor: pointer !important;
        margin: 5px;
    }
    
    button:hover {
        background: rgba(78, 205, 196, 0.3) !important;
    }
    
    input[type="number"] {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(78, 205, 196, 0.3);
        border-radius: 10px;
        padding: 8px 12px;
        color: #ffffff;
        width: 100px;
        text-align: center;
    }
    
    .impact-warning {
        background: linear-gradient(45deg, #ff4444, #cc0000);
        border: 2px solid #ff6666;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        animation: flash 1s infinite alternate;
    }
    
    .real-asteroids-section {
        background: linear-gradient(135deg, rgba(255, 165, 0, 0.1) 0%, rgba(255, 69, 0, 0.1) 100%);
        border: 1px solid rgba(255, 165, 0, 0.3);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    @keyframes flash {
        0% { opacity: 1; }
        100% { opacity: 0.7; }
    }
</style>
""")

# Header
scene.append_to_caption('<div class="section">')
scene.append_to_caption('<h1>Integrated Asteroid Simulation</h1>')
scene.append_to_caption('<p>3D orbital simulation + 2D impact map after collision</p>')
scene.append_to_caption('<p>Earth orbits the Sun from the start!</p>')
scene.append_to_caption('</div>')

# Asteroid settings
scene.append_to_caption('<div class="section">')
scene.append_to_caption('<h2>Asteroid Settings</h2>')
scene.append_to_caption('Mass (kg): ')
asteroid_mass_input = winput(bind=lambda: None, type="numeric", text="1e15")
scene.append_to_caption('<br>Position X (AU): ')
asteroid_x_input = winput(bind=lambda: None, type="numeric", text="2.0")
scene.append_to_caption(' Y (AU): ')
asteroid_y_input = winput(bind=lambda: None, type="numeric", text="0")
scene.append_to_caption(' Z (AU): ')
asteroid_z_input = winput(bind=lambda: None, type="numeric", text="0")
scene.append_to_caption('<br>Velocity X (km/s): ')
asteroid_vx_input = winput(bind=lambda: None, type="numeric", text="0")
scene.append_to_caption(' Y (km/s): ')
asteroid_vy_input = winput(bind=lambda: None, type="numeric", text="21.0")
scene.append_to_caption(' Z (km/s): ')
asteroid_vz_input = winput(bind=lambda: None, type="numeric", text="0")

# Impact map parameters
scene.append_to_caption('<br><h3>Impact Map Parameters</h3>')
scene.append_to_caption('Impact Latitude: ')
impact_lat_input = winput(bind=lambda: None, type="numeric", text="50.45")
scene.append_to_caption(' Impact Longitude: ')
impact_lon_input = winput(bind=lambda: None, type="numeric", text="30.52")
scene.append_to_caption('<br>Entry Angle (°): ')
impact_angle_input = winput(bind=lambda: None, type="numeric", text="45")

# Quick presets
def preset_comet():
    asteroid_x_input.text = "5.0"
    asteroid_y_input.text = "0"
    asteroid_z_input.text = "0"
    asteroid_vx_input.text = "0"
    asteroid_vy_input.text = "8.0"
    asteroid_vz_input.text = "0"
    asteroid_mass_input.text = "1e14"
    impact_lat_input.text = "48.86"  # Paris
    impact_lon_input.text = "2.35"
    impact_angle_input.text = "30"

def preset_near_earth():
    asteroid_x_input.text = "1.2"
    asteroid_y_input.text = "0"
    asteroid_z_input.text = "0"
    asteroid_vx_input.text = "0"
    asteroid_vy_input.text = "25.0"
    asteroid_vz_input.text = "0"
    asteroid_mass_input.text = "1e16"
    impact_lat_input.text = "40.71"  # New York
    impact_lon_input.text = "-74.01"
    impact_angle_input.text = "60"

def preset_impact():
    asteroid_x_input.text = "1.5"
    asteroid_y_input.text = "0"
    asteroid_z_input.text = "0"
    asteroid_vx_input.text = "-15.0"
    asteroid_vy_input.text = "20.0"
    asteroid_vz_input.text = "0"
    asteroid_mass_input.text = "5e16"
    impact_lat_input.text = "50.45"  # Kyiv
    impact_lon_input.text = "30.52"
    impact_angle_input.text = "45"

def preset_belt():
    asteroid_x_input.text = "2.8"
    asteroid_y_input.text = "0"
    asteroid_z_input.text = "0"
    asteroid_vx_input.text = "0"
    asteroid_vy_input.text = "18.0"
    asteroid_vz_input.text = "0"
    asteroid_mass_input.text = "5e15"
    impact_lat_input.text = "35.68"  # Tokyo
    impact_lon_input.text = "139.69"
    impact_angle_input.text = "35"

def apply_real_asteroid(asteroid_name):
    """Apply parameters of a real asteroid"""
    if asteroid_name in REAL_ASTEROIDS:
        data = REAL_ASTEROIDS[asteroid_name]
        
        # Calculate mass based on diameter if needed
        if 'mass_kg' in data:
            mass = data['mass_kg']
        else:
            # Approximate asteroid density 2000 kg/m³
            radius_m = (data['diameter_km'] * 1000) / 2
            volume = (4/3) * math.pi * (radius_m ** 3)
            mass = volume * 2000
        
        # Set parameters
        asteroid_x_input.text = str(data['orbit_distance_au'])
        asteroid_y_input.text = "0"
        asteroid_z_input.text = "0"
        asteroid_vx_input.text = "0"
        asteroid_vy_input.text = str(data['velocity_kms'])
        asteroid_vz_input.text = "0"
        asteroid_mass_input.text = f"{mass:.2e}"
        
        # Coordinates for impact map
        impact_lat_input.text = str(data['coordinates'][0])
        impact_lon_input.text = str(data['coordinates'][1])
        
        # Angle based on threat level
        if data['threat_level'] == "High":
            impact_angle_input.text = "30"
        elif data['threat_level'] == "Medium":
            impact_angle_input.text = "45"
        else:
            impact_angle_input.text = "60"
        
        print(f"Loaded parameters for asteroid: {asteroid_name}")
        print(f"Diameter: {data['diameter_km']} km")
        print(f"Mass: {mass:.2e} kg")
        print(f"Threat level: {data['threat_level']}")

def show_asteroid_examples():
    """Show list of real asteroids"""
    example_text = """
REAL ASTEROIDS - NASA/ESA CATALOG

Click an asteroid button below to apply its parameters:

"""
    
    # Add each asteroid to the list
    for name, data in REAL_ASTEROIDS.items():
        threat_label = {
            "None": "Green",
            "Very Low": "Yellow",
            "Low": "Orange",
            "Medium": "Red",
            "High": "Critical"
        }.get(data['threat_level'], "Neutral")
        
        example_text += f"""
{name}
   Description: {data['description']}
   Diameter: {data['diameter_km']} km
   Mass: {data['mass_kg']:.2e} kg  
   Orbit: {data['orbit_distance_au']} AU
   Velocity: {data['velocity_kms']} km/s
   Threat: {data['threat_level']} ({threat_label})
   Discovered: {data['discovery_year']}
   
"""
    
    # Update info text
    info_text.text = example_text

scene.append_to_caption('<br>')
button(text="Comet", bind=preset_comet)
button(text="Near Earth", bind=preset_near_earth)
button(text="Impact", bind=preset_impact)
button(text="Asteroid Belt", bind=preset_belt)
button(text="Examples", bind=show_asteroid_examples)

# Add buttons for real asteroids
scene.append_to_caption('<div class="real-asteroids-section">')
scene.append_to_caption('<h3>Apply Real Asteroid Parameters</h3>')

# Create buttons for each asteroid
for asteroid_name in REAL_ASTEROIDS.keys():
    def make_asteroid_handler(name):
        return lambda: apply_real_asteroid(name)
    
    button_text = f"{asteroid_name.split()[1] if len(asteroid_name.split()) > 1 else asteroid_name}"
    button(text=button_text, bind=make_asteroid_handler(asteroid_name))

scene.append_to_caption('</div>')
scene.append_to_caption('</div>')

# Simulation settings
scene.append_to_caption('<div class="section">')
scene.append_to_caption('<h2>Simulation Parameters</h2>')
scene.append_to_caption('Time Step (days): ')
timestep_input = winput(bind=lambda: None, type="numeric", text="0.1")
scene.append_to_caption(' Animation Speed: ')
animation_speed_input = winput(bind=lambda: None, type="numeric", text="200")

# Toggle Moon orbit display
show_moon_orbit = False

def toggle_moon_orbit():
    global show_moon_orbit, moon_orbit_curve
    show_moon_orbit = not show_moon_orbit
    
    if show_moon_orbit:
        if len(bodies) >= 2:  # Check if Earth exists
            earth_pos = None
            for body in bodies:
                if body.name == "Earth":
                    earth_pos = body.pos
                    break
            if earth_pos:
                moon_orbit_curve = create_moon_orbit_line(earth_pos, MOON_DISTANCE)
        orbit_button.text = "Hide Orbit"
    else:
        if moon_orbit_curve:
            moon_orbit_curve.visible = False
            del moon_orbit_curve
            moon_orbit_curve = None
        orbit_button.text = "Show Orbit"

def toggle_auto_zoom():
    global auto_zoom_enabled
    auto_zoom_enabled = not auto_zoom_enabled
    if not auto_zoom_enabled:
        scene.range = default_camera_range
        scene.center = vector(0, 0, 0)
    zoom_button.text = f"{'Disable' if auto_zoom_enabled else 'Enable'} Zoom"

scene.append_to_caption('<br>')
orbit_button = button(text="Show Orbit", bind=toggle_moon_orbit)
zoom_button = button(text="Disable Zoom", bind=toggle_auto_zoom)
scene.append_to_caption('</div>')

def create_initial_system():
    """Create initial Sun-Earth-Moon system"""
    global bodies, time_step, moon_orbit_curve
    
    # Clear previous objects
    for body in bodies:
        if hasattr(body, 'sphere') and body.sphere:
            body.sphere.visible = False
        if hasattr(body, 'glow') and body.glow:
            body.glow.visible = False
        if hasattr(body, 'inner_glow') and body.inner_glow:
            body.inner_glow.visible = False
        if hasattr(body, 'atmosphere') and body.atmosphere:
            body.atmosphere.visible = False
    bodies.clear()
    
    # Read time parameters
    try:
        time_step = float(timestep_input.text) * 86400
    except ValueError:
        time_step = 86400 * 0.1
    
    # Create Sun
    sun = CelestialBody(
        name="Sun",
        mass=PLANET_DATA['Sun']['mass'],
        pos=[0, 0, 0],
        vel=[0, 0, 0],
        radius=PLANET_DATA['Sun']['radius'],
        body_color=PLANET_DATA['Sun']['color'],
        trail_color=PLANET_DATA['Sun']['trail']
    )
    bodies.append(sun)
    
    # Create Earth
    earth_distance = PLANET_DATA['Earth']['distance'] * AU
    earth_velocity = PLANET_DATA['Earth']['velocity'] * 1000
    
    earth = CelestialBody(
        name="Earth",
        mass=PLANET_DATA['Earth']['mass'],
        pos=[earth_distance, 0, 0],
        vel=[0, earth_velocity, 0],
        radius=PLANET_DATA['Earth']['radius'],
        body_color=PLANET_DATA['Earth']['color'],
        trail_color=PLANET_DATA['Earth']['trail']
    )
    bodies.append(earth)
    
    # Create Moon with correct orbital velocity
    moon_orbital_velocity = calculate_moon_orbital_velocity(PLANET_DATA['Earth']['mass'], MOON_DISTANCE)
    
    moon = CelestialBody(
        name="Moon",
        mass=PLANET_DATA['Moon']['mass'],
        pos=[earth_distance + MOON_DISTANCE, 0, 0],
        vel=[0, earth_velocity + moon_orbital_velocity, 0],
        radius=PLANET_DATA['Moon']['radius'],
        body_color=PLANET_DATA['Moon']['color'],
        trail_color=PLANET_DATA['Moon']['trail']
    )
    bodies.append(moon)
    
    # Set camera center to Sun
    set_camera_center_to_sun()

def add_asteroid_to_system():
    """Add asteroid to existing system"""
    global bodies
    
    # Remove previous asteroid if exists
    for body in bodies[:]:  # Create copy for safe removal
        if body.name == "Asteroid":
            # Remove asteroid visual objects
            if hasattr(body, 'sphere') and body.sphere:
                body.sphere.visible = False
                del body.sphere
            bodies.remove(body)
    
    # Create new asteroid
    try:
        asteroid_pos = [
            float(asteroid_x_input.text) * AU,
            float(asteroid_y_input.text) * AU,
            float(asteroid_z_input.text) * AU
        ]
        asteroid_vel = [
            float(asteroid_vx_input.text) * 1000,
            float(asteroid_vy_input.text) * 1000,
            float(asteroid_vz_input.text) * 1000
        ]
        asteroid_mass = float(asteroid_mass_input.text)
    except ValueError:
        # Default values on error
        asteroid_pos = [2.0 * AU, 0, 0]
        asteroid_vel = [0, 21000, 0]
        asteroid_mass = 1e15
    
    asteroid = CelestialBody(
        name="Asteroid",
        mass=asteroid_mass,
        pos=asteroid_pos,
        vel=asteroid_vel,
        radius=0.06,
        body_color=color.red,
        trail_color=color.orange
    )
    bodies.append(asteroid)

def start_simulation():
    global running, pre_simulation_running
    if not running:
        # Add asteroid to system
        add_asteroid_to_system()
        running = True
        pre_simulation_running = False  # Stop initial motion
        start_button.text = "Pause"
    else:
        running = False
        start_button.text = "Start"

def reset_simulation():
    global running, impact_occurred, explosion_effects, explosion_frame_count, zoomed_in, map_created, pre_simulation_running
    running = False
    pre_simulation_running = True  # Restore initial motion
    impact_occurred = False
    explosion_effects = []
    explosion_frame_count = 0
    zoomed_in = False
    map_created = False
    scene.range = default_camera_range
    set_camera_center_to_sun()  # Set camera center to Sun
    start_button.text = "Start"
    
    # Create new initial system
    create_initial_system()
    
    # Clear trails
    for body in bodies:
        if hasattr(body, 'sphere') and hasattr(body.sphere, 'clear_trail'):
            body.sphere.clear_trail()

def clear_trails():
    """Clear all orbital trails and remove asteroids"""
    global bodies
    
    # Clear trails for all bodies
    for body in bodies[:]:  # Create copy for safe removal
        if hasattr(body, 'sphere') and body.sphere:
            # Save current trail parameters
            original_trail_color = body.sphere.trail_color if hasattr(body.sphere, 'trail_color') else color.white
            original_trail_radius = body.sphere.trail_radius if hasattr(body.sphere, 'trail_radius') else None
            
            # Disable and re-enable trail to clear it
            body.sphere.make_trail = False
            body.sphere.make_trail = True
            
            # Restore trail parameters
            if hasattr(body.sphere, 'trail_color'):
                body.sphere.trail_color = original_trail_color
            if original_trail_radius and hasattr(body.sphere, 'trail_radius'):
                body.sphere.trail_radius = original_trail_radius
    
    # Remove all asteroids from system
    for body in bodies[:]:  # Create copy for safe removal
        if body.name == "Asteroid":
            # Remove asteroid visual objects
            if hasattr(body, 'sphere') and body.sphere:
                body.sphere.visible = False
                del body.sphere
            bodies.remove(body)
    
    print("Trails cleared and asteroids removed!")

# Controls
scene.append_to_caption('<div class="section">')
scene.append_to_caption('<h2>Controls</h2>')
start_button = button(text="Start", bind=start_simulation)
reset_button = button(text="Reset", bind=reset_simulation)
clear_button = button(text="Clear Trails", bind=clear_trails)
scene.append_to_caption('</div>')

# Status
scene.append_to_caption('<div class="section">')
scene.append_to_caption('<h3>Simulation Status</h3>')
info_text = wtext(text="Earth is already orbiting the Sun! Press 'Start' to add an asteroid...")
scene.append_to_caption('</div>')

# Set initial values
preset_impact()

# Create initial system
create_initial_system()

# Main simulation loop
time_counter = 0
while True:
    rate(100)
    
    # Set camera center to Sun each frame
    set_camera_center_to_sun()
    
    # Limit camera zoom
    limit_camera_zoom()
    
    # Initial Earth motion around Sun (before main simulation)
    if pre_simulation_running and len(bodies) >= 2:
        try:
            animation_rate = float(animation_speed_input.text)
            rate(animation_rate)
        except (ValueError, AttributeError):
            rate(200)
        
        # Reset forces
        for body in bodies:
            if body.name != "Asteroid":  # Exclude asteroid from initial simulation
                body.force = vector(0, 0, 0)
        
        # Calculate gravitational forces (only between Sun, Earth, and Moon)
        for i in range(len(bodies) - (1 if len(bodies) > 3 else 0)):  # Exclude asteroid
            for j in range(i + 1, len(bodies) - (1 if len(bodies) > 3 else 0)):
                if bodies[i].name != "Asteroid" and bodies[j].name != "Asteroid":
                    force = calculate_gravitational_force(bodies[i], bodies[j])
                    bodies[i].force += force
                    bodies[j].force -= force
        
        # Update positions (only for Earth and Moon)
        for body in bodies:
            if body.name != "Sun" and body.name != "Asteroid":
                acceleration = body.force / body.mass
                body.vel += acceleration * time_step
                body.pos += body.vel * time_step
                body.sphere.pos = body.pos
                
                # Update additional effects
                if hasattr(body, 'atmosphere'):
                    body.atmosphere.pos = body.pos
            elif body.name == "Sun":
                # Update Sun's glow effects
                if hasattr(body, 'glow'):
                    body.glow.pos = body.pos
                if hasattr(body, 'inner_glow'):
                    body.inner_glow.pos = body.pos
            
            # Update planet rotation
            if body.name != "Asteroid":
                body.update_rotation(time_step)
    
    # Main simulation with asteroid
    if running and len(bodies) > 0:
        try:
            animation_rate = float(animation_speed_input.text)
            rate(animation_rate)
        except (ValueError, AttributeError):
            rate(200)
        
        # Animate explosion
        if explosion_effects:
            explosion_frame_count += 1
            explosion_effects = animate_explosion(explosion_effects, explosion_frame_count)
        
        if not impact_occurred:
            # Reset forces
            for body in bodies:
                body.force = vector(0, 0, 0)
            
            # Calculate gravitational forces
            for i in range(len(bodies)):
                for j in range(i + 1, len(bodies)):
                    force = calculate_gravitational_force(bodies[i], bodies[j])
                    bodies[i].force += force
                    bodies[j].force -= force
            
            # Update positions and rotation
            for body in bodies:
                if body.name != "Sun":
                    acceleration = body.force / body.mass
                    body.vel += acceleration * time_step
                    body.pos += body.vel * time_step
                    body.sphere.pos = body.pos
                    
                    # Update additional effects
                    if hasattr(body, 'atmosphere'):
                        body.atmosphere.pos = body.pos
                        
                else:
                    # Update Sun's glow effects
                    if hasattr(body, 'glow'):
                        body.glow.pos = body.pos
                    if hasattr(body, 'inner_glow'):
                        body.inner_glow.pos = body.pos
                
                # Update planet rotation
                body.update_rotation(time_step)
        
        # Find Earth and asteroid
        earth_pos = None
        moon_pos = None
        asteroid_pos = None
        earth_body = None
        asteroid_body = None
        
        for body in bodies:
            if body.name == "Earth":
                earth_pos = body.pos
                earth_body = body
            elif body.name == "Moon":
                moon_pos = body.pos
            elif body.name == "Asteroid":
                asteroid_pos = body.pos
                asteroid_body = body
        
        # Check for collision and auto-zoom
        if earth_pos and asteroid_pos and not impact_occurred:
            distance = mag(asteroid_pos - earth_pos)
            distance_au = distance / AU
            
            # Auto-zoom with limits
            if auto_zoom_enabled:
                zoom_threshold = 0.3 * AU  # Start zooming
                close_threshold = 0.05 * AU  # Strong zoom
                
                if distance < zoom_threshold:
                    zoomed_in = True
                    # Center camera between Earth and asteroid, but keep Sun as center
                    calculated_range = max(MIN_ZOOM_RANGE, min(distance * 3, MAX_ZOOM_RANGE))
                    scene.range = calculated_range
                elif zoomed_in:
                    # Return to normal view
                    scene.range = min(default_camera_range, MAX_ZOOM_RANGE)
                    zoomed_in = False
            
            # Check for collision (considering real sizes)
            collision_distance = (earth_body.current_radius + asteroid_body.current_radius) * AU
            if distance < collision_distance:
                impact_occurred = True
                
                # Create explosion effect
                impact_pos = (earth_pos + asteroid_pos) / 2
                explosion_effects = create_explosion(impact_pos, 2.0)
                explosion_frame_count = 0 
                
                # Change Earth's color (impact effect)
                earth_body.sphere.color = color.red
                if hasattr(earth_body, 'atmosphere'):
                    earth_body.atmosphere.color = color.orange
                
                # Stop asteroid
                asteroid_body.sphere.visible = False
                
                # Create impact map after collision
                if not map_created:
                    try:
                        # Get parameters for map
                        lat = float(impact_lat_input.text)
                        lon = float(impact_lon_input.text)
                        mass = float(asteroid_mass_input.text)
                        velocity = mag(asteroid_body.vel)
                        angle = float(impact_angle_input.text)
                        
                        # Create map
                        map_file = create_impact_map(lat, lon, mass, velocity, angle)
                        map_created = True
                        
                        print(f"COLLISION! Impact map created: {map_file}")
                        
                    except Exception as e:
                        print(f"Error creating map: {e}")
    
    # Update information
    if pre_simulation_running or running:
        time_counter += time_step
        days = time_counter / 86400
        
        earth_sun_distance = 0
        earth_moon_distance = 0
        asteroid_earth_distance = 0
        danger_status = "Safe"
        
        # Find body positions
        earth_pos = None
        asteroid_pos = None
        
        for body in bodies:
            if body.name == "Earth":
                earth_pos = body.pos
                earth_sun_distance = mag(earth_pos) / AU
            elif body.name == "Asteroid":
                asteroid_pos = body.pos
        
        if earth_pos and asteroid_pos and not impact_occurred:
            asteroid_earth_distance = mag(asteroid_pos - earth_pos) / AU
            
            # Check for dangerous proximity
            danger_distance = 0.001  # AU
            if asteroid_earth_distance < danger_distance:
                danger_status = "DANGER!"
            elif asteroid_earth_distance < 0.2:
                danger_status = "Close"
            else:
                danger_status = "Safe"
        elif impact_occurred:
            asteroid_earth_distance = 0
            danger_status = "COLLISION! Map created!"
        
        # Calculate Earth's rotation speed
        earth_rotation_days = (time_counter / EARTH_ROTATION_PERIOD) % 1
        
        zoom_status = "Zoom Enabled" if auto_zoom_enabled else "Zoom Disabled"
        camera_status = "Zoomed" if zoomed_in else "Normal"
        map_status = "Map Created" if map_created else "Awaiting Collision"
        
        simulation_status = "Earth Orbiting" if pre_simulation_running else "Asteroid Active"
        
        info_text.text = f"""
Day: {days:.1f} | Earth Rotation: {earth_rotation_days:.2f}
Earth ↔ Sun: {earth_sun_distance:.3f} AU
Mode: {simulation_status}

Asteroid ↔ Earth: {asteroid_earth_distance:.4f} AU
Status: {danger_status}
{zoom_status} | {camera_status} | {map_status}

Zoom: {scene.range/AU:.2f} AU (limits: {MIN_ZOOM_RANGE/AU:.1f}-{MAX_ZOOM_RANGE/AU:.0f} AU)
Camera Center: Sun (0, 0, 0)
        """
