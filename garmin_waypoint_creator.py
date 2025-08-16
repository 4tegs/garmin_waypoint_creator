# ##########################################################################################
# garmin_waypoint_creator
# Hans Straßgütl
#
# copy this program in a folder and start building waypoints as you will need them later 
# for Basecamp or other Garmin software to build your routes.
# ..........................................................................................
# More information: readme.md
# 
# Changes:
#   2025 08 03      Started. Claude.ai as a support.
#   2025 08 17      Added waypoint move functionality.
#                   Edit Function improved.              
# 
# ##########################################################################################
# Version 1.5
# ------------------------------------------------------------------------------------------
# Global Imports
# ------------------------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import tkintermapview
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom
import random
import string
import os
import glob
import requests
from PIL import Image, ImageTk
from io import BytesIO
import threading
import sys

class GarminWaypointCreator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Garmin Waypoint Creator by Hans Straßgütl - Version 1.5")
        self.root.geometry("1200x800")
        
        # Waypoint data
        self.current_waypoint = None
        self.waypoint_lat = None
        self.waypoint_lon = None
        self.edit_window = None
        self.waypoint_saved = False
        
        # Move functionality
        self.move_mode = False
        self.temp_move_marker = None
        
        # Store map markers for cleanup
        self.map_markers = []
        
        # Icon cache for loaded images
        self.icon_cache = {}
        self.icon_images = {}  # For Tkinter PhotoImage objects
        
        # Get the directory where the script is located
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            self.base_dir = sys._MEIPASS
        else:
            # If running as script
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.icons_dir = os.path.join(self.base_dir, "icons_garmin")
        
        # Garmin icons mapping
        self.garmin_icons = {
            "Campground": "Campground",
            "RV Park": "RV Park",
            "Scenic Area": "Scenic Area",
            "Museum": "Museum",
            "Church": "Church",
            "Information": "Information",
            "Parking Area": "Parking Area",
            "Restaurant": "Restaurant",
            "Winery": "Winery",
            "Hotel": "Hotel",
            "Lodge": "Lodge",
            "Funicular"         	: "Funicular.png",
            "Gas Station": "Gas Station",
            "Bar": "Bar",
            "Library": "Library",
            "Theater": "Theater",
            "Swimming Area": "Swimming Area",
            "Waypoint": "Waypoint",
            "Summit": "Summit",
            "Geocache": "Geocache",
            "Car": "Car",
            "Flag": "Flag",
            "Truck Stop": "Truck Stop",
            "Airport": "Airport",
            "Shopping": "Shopping",
            "School": "School",
            "Cemetery": "Cemetery",
            "Park": "Park",
            "Picnic Area": "Picnic Area",
            "Restroom": "Restroom",
            "Telephone": "Telephone",
            "Medical Facility": "Medical Facility",
            "Pharmacy": "Pharmacy",
            "Police Station": "Police Station",
            "Fire Department": "Fire Department",
            "Bank": "Bank",
            "Fast Food": "Fast Food",
            "Pizza": "Pizza",
            "Stadium": "Stadium",
            "Golf Course": "Golf Course",
            "Skiing Area": "Skiing Area",
            "Dam": "Dam",
            "Controlled Area": "Controlled Area",
            "Danger Area": "Danger Area",
            "Restricted Area": "Restricted Area",
            "Null": "Null",
            "Ball Park": "Ball Park",
            "Car Rental": "Car Rental",
            "City (Capitol)": "City (Capitol)",
            "City (Large)": "City (Large)",
            "City (Medium)": "City (Medium)",
            "City (Small)": "City (Small)",
            "Civil": "Civil",
            "Coast Guard": "Coast Guard",
            "Contact, Afro": "Contact, Afro",
            "Contact, Alien": "Contact, Alien",
            "Contact, Ball Cap": "Contact, Ball Cap",
            "Contact, Big Ears": "Contact, Big Ears",
            "Contact, Biker": "Contact, Biker",
            "Contact, Bug": "Contact, Bug",
            "Contact, Cat": "Contact, Cat",
            "Contact, Dog": "Contact, Dog",
            "Contact, Dreadlocks": "Contact, Dreadlocks",
            "Contact, Female1": "Contact, Female1",
            "Contact, Female2": "Contact, Female2",
            "Contact, Female3": "Contact, Female3",
            "Contact, Goatee": "Contact, Goatee",
            "Contact, Kung-Fu": "Contact, Kung-Fu",
            "Contact, Pirate": "Contact, Pirate",
            "Contact, Ranger": "Contact, Ranger",
            "Contact, Smiley": "Contact, Smiley",
            "Contact, Spike": "Contact, Spike",
            "Contact, Sumo": "Contact, Sumo"
        }
        
        self.setup_ui()
        
        # Load icons in background
        self.load_garmin_icons()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Map frame
        self.map_frame = ttk.Frame(main_frame)
        self.map_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        self.info_label = ttk.Label(self.map_frame, text="Klicken Sie auf die Karte, um einen Waypoint zu erstellen")
        self.info_label.pack(pady=5)
        
        # Create map widget
        self.map_widget = tkintermapview.TkinterMapView(self.map_frame, width=1000, height=600, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        
        # Set position to Burgos and zoom
        self.map_widget.set_position(42.34378014586935, -3.6960958297369473)  # Burgos coordinates
        self.map_widget.set_zoom(8)
        
        # Set map source to OpenStreetMap
        self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        
        # Add click event
        self.map_widget.add_left_click_map_command(self.on_map_click)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Refresh button
        refresh_button = ttk.Button(button_frame, text="Waypoints aktualisieren", command=self.load_waypoints)
        refresh_button.pack(side=tk.LEFT)
        
        # Close button
        close_button = ttk.Button(button_frame, text="Programm schließen", command=self.close_program)
        close_button.pack(side=tk.RIGHT)
        
        # Load existing waypoints after UI setup
        self.root.after(100, self.load_waypoints)
        
    def load_garmin_icons(self):
        """Load Garmin icons from the local icons_garmin folder"""
        if not os.path.exists(self.icons_dir):
            print(f"Icons directory not found: {self.icons_dir}")
            print("Please create 'icons_garmin' folder next to the program with PNG icons")
            return
            
        try:
            # Scan for all PNG files in the icons directory
            icon_files = glob.glob(os.path.join(self.icons_dir, "*.png"))
            
            for icon_path in icon_files:
                try:
                    # Get filename without extension
                    icon_filename = os.path.basename(icon_path)
                    icon_name = icon_filename.replace('.png', '')
                    
                    # Check if this icon is in our Garmin icons mapping
                    if icon_name in self.garmin_icons:
                        # Load image
                        image = Image.open(icon_path)
                        
                        # Create different sizes
                        # For map display (24x24 pixels)
                        image_map = image.resize((24, 24), Image.Resampling.LANCZOS)
                        photo_map = ImageTk.PhotoImage(image_map)
                        
                        # For icon selection dialog (32x32 pixels)
                        image_large = image.resize((32, 32), Image.Resampling.LANCZOS)
                        photo_large = ImageTk.PhotoImage(image_large)
                        
                        # Store in cache
                        self.icon_cache[icon_name] = {
                            'map': photo_map,
                            'large': photo_large,
                            'path': icon_path
                        }
                        
                except Exception as e:
                    print(f"Failed to load icon {icon_path}: {e}")
                    
            print(f"Loaded {len(self.icon_cache)} Garmin icons from {self.icons_dir}")
            
            if len(self.icon_cache) == 0:
                print("No icons loaded. Make sure PNG files are named exactly like the Garmin icon names.")
                print("Example: 'Scenic Area.png', 'Restaurant.png', 'Gas Station.png', etc.")
                
        except Exception as e:
           print(f"Error loading Garmin icons: {e}")
                   
    def load_waypoints(self):
        """Load and display all GPX waypoints from the current directory"""
        # Clear existing markers
        for marker in self.map_markers:
            marker.delete()
        self.map_markers.clear()
        
        # Find all GPX files in current directory
        gpx_files = glob.glob("*.gpx")
        
        for gpx_file in gpx_files:
            try:
                # Parse GPX file
                tree = ET.parse(gpx_file)
                root = tree.getroot()
                
                # Handle namespace
                ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
                
                # Find waypoints
                for wpt in root.findall('.//gpx:wpt', ns):
                    lat = float(wpt.get('lat'))
                    lon = float(wpt.get('lon'))
                    
                    # Get waypoint name
                    name_elem = wpt.find('gpx:name', ns)
                    name = name_elem.text if name_elem is not None else "Unbenannt"
                    
                    # Get symbol/icon
                    sym_elem = wpt.find('gpx:sym', ns)
                    symbol = sym_elem.text if sym_elem is not None else "Waypoint"
                    
                    # Get icon for marker
                    icon_image = None
                    # Find the key for the symbol value
                    icon_key = None
                    for key, value in self.garmin_icons.items():
                        if value == symbol:
                            icon_key = key
                            break
                    
                    if icon_key and icon_key in self.icon_cache:
                        icon_image = self.icon_cache[icon_key]['map']
                    
                    # Create marker
                    if icon_image:
                        marker = self.map_widget.set_marker(
                            lat, lon, 
                            text=name,
                            text_color="black",
                            font=("Arial", 8),
                            icon=icon_image,
                            command=lambda coord, file=gpx_file, wpt_name=name: self.on_waypoint_click(coord, file, wpt_name)
                        )
                    else:
                        marker = self.map_widget.set_marker(
                            lat, lon, 
                            text=name,
                            text_color="black",
                            font=("Arial", 8),
                            command=lambda coord, file=gpx_file, wpt_name=name: self.on_waypoint_click(coord, file, wpt_name)
                        )
                    self.map_markers.append(marker)
                    
            except Exception as e:
                print(f"Fehler beim Laden von {gpx_file}: {e}")
                
    def on_waypoint_click(self, coordinates, filename, waypoint_name):
        """Handle click on existing waypoint marker"""
        # Load the waypoint data for editing
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
            
            # Find the specific waypoint by name
            for wpt in root.findall('.//gpx:wpt', ns):
                name_elem = wpt.find('gpx:name', ns)
                if name_elem is not None and name_elem.text == waypoint_name:
                    # Set current waypoint data
                    self.waypoint_lat = float(wpt.get('lat'))
                    self.waypoint_lon = float(wpt.get('lon'))
                    self.current_waypoint = filename
                    self.waypoint_saved = True
                    
                    # Open edit window with existing data
                    self.open_edit_window(wpt, ns)
                    break
                    
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden des Waypoints: {e}")
            
    def on_map_click(self, coordinates_tuple):
        # Check if we're in move mode
        if self.move_mode:
            self.handle_move_click(coordinates_tuple)
            return
            
        # Store coordinates and open edit window for new waypoint
        self.waypoint_lat = coordinates_tuple[0]
        self.waypoint_lon = coordinates_tuple[1]
        self.current_waypoint = None  # New waypoint
        self.waypoint_saved = False
        
        # Open edit window
        self.open_edit_window()
        
    def handle_move_click(self, coordinates_tuple):
        """Handle map click when in move mode"""
        # Update waypoint coordinates
        self.waypoint_lat = coordinates_tuple[0]
        self.waypoint_lon = coordinates_tuple[1]
        
        # Remove temporary marker
        if self.temp_move_marker:
            self.temp_move_marker.delete()
            self.temp_move_marker = None
        
        # Exit move mode
        self.move_mode = False
        self.info_label.config(text="Klicken Sie auf die Karte, um einen Waypoint zu erstellen")
        
        # Update coordinates in edit window
        if hasattr(self, 'coord_label'):
            self.coord_label.config(text=f"Koordinaten: {self.waypoint_lat:.6f}, {self.waypoint_lon:.6f}")
        
        # Auto-save waypoint with new coordinates
        if self.current_waypoint and hasattr(self, 'name_var') and self.name_var.get().strip():
            self.auto_save_waypoint()
        
        # Bring edit window back to front
        if self.edit_window:
            self.edit_window.deiconify()  # Show window again
            self.edit_window.lift()
            self.edit_window.focus_set()
            self.edit_window.grab_set()  # Restore grab
            
        # Refresh waypoints to show new position
        self.load_waypoints()
        
    def start_move_mode(self):
        """Start move mode for waypoint"""
        self.move_mode = True
        self.info_label.config(text="VERSCHIEBEN-MODUS: Klicken Sie auf die neue Position für den Waypoint")
        
        # Add temporary marker at current position to show what's being moved
        icon_name = self.icon_var.get()
        icon_image = None
        if icon_name in self.icon_cache:
            icon_image = self.icon_cache[icon_name]['map']
        
        if icon_image:
            self.temp_move_marker = self.map_widget.set_marker(
                self.waypoint_lat, self.waypoint_lon,
                text="VERSCHIEBEN",
                text_color="red",
                font=("Arial", 8, "bold"),
                icon=icon_image
            )
        else:
            self.temp_move_marker = self.map_widget.set_marker(
                self.waypoint_lat, self.waypoint_lon,
                text="VERSCHIEBEN",
                text_color="red",
                font=("Arial", 8, "bold")
            )
        
        # Minimize edit window
        if self.edit_window:
            self.edit_window.withdraw()
            
        # Release grab so map clicks can be processed
        self.edit_window.grab_release()
        
    def open_edit_window(self, existing_wpt=None, ns=None):
        if self.edit_window:
            self.edit_window.destroy()
            
        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("Waypoint bearbeiten")
        self.edit_window.geometry("550x750")
        self.edit_window.transient(self.root)
        self.edit_window.grab_set()
        
        # Center the window
        self.edit_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 250, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(self.edit_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Coordinates display
        coord_frame = ttk.Frame(main_frame)
        coord_frame.pack(fill=tk.X, pady=(0, 10))
        self.coord_label = ttk.Label(coord_frame, text=f"Koordinaten: {self.waypoint_lat:.6f}, {self.waypoint_lon:.6f}")
        self.coord_label.pack()
        
        # Name field
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Name:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, font=("Arial", 10))
        self.name_entry.pack(fill=tk.X, pady=(2, 0))
        self.name_var.trace('w', self.on_name_change)
        
        # Icon selection with images
        icon_frame = ttk.Frame(main_frame)
        icon_frame.pack(fill=tk.X, pady=5)
        ttk.Label(icon_frame, text="Icon:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Create a frame for icon selection
        icon_select_frame = ttk.Frame(icon_frame)
        icon_select_frame.pack(fill=tk.X, pady=(2, 0))
        
        # Icon display label
        self.icon_display_label = ttk.Label(icon_select_frame, text="")
        self.icon_display_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Icon combobox
        self.icon_var = tk.StringVar(value="Scenic Area")  # Default icon
        icon_combo = ttk.Combobox(icon_select_frame, textvariable=self.icon_var, values=list(self.garmin_icons.keys()), 
                                  state="readonly", font=("Arial", 10))
        icon_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        icon_combo.bind('<<ComboboxSelected>>', self.on_icon_change)
        
        # Update icon display initially
        self.update_icon_display()
        
        # Description field
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(desc_frame, text="Beschreibung:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(desc_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        
        self.desc_text = tk.Text(text_frame, height=8, font=("Arial", 10), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.desc_text.yview)
        self.desc_text.configure(yscrollcommand=scrollbar.set)
        
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hyperlink fields
        link_frame = ttk.Frame(main_frame)
        link_frame.pack(fill=tk.X, pady=5)
        ttk.Label(link_frame, text="Hyperlinks:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.link_vars = []
        for i in range(3):
            link_subframe = ttk.Frame(link_frame)
            link_subframe.pack(fill=tk.X, pady=2)
            ttk.Label(link_subframe, text=f"Link {i+1}:", font=("Arial", 9)).pack(anchor=tk.W)
            link_var = tk.StringVar()
            self.link_vars.append(link_var)
            entry = ttk.Entry(link_subframe, textvariable=link_var, font=("Arial", 9))
            entry.pack(fill=tk.X, pady=(1, 0))
            link_var.trace('w', self.on_field_change)
        
        # Load existing waypoint data if editing
        if existing_wpt is not None and ns is not None:
            self.load_waypoint_data(existing_wpt, ns)
            
        # Update icon display after loading data
        self.root.after(100, self.update_icon_display)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Buttons
        self.save_button = ttk.Button(button_frame, text="Wegpunkt sichern", command=self.save_waypoint, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Move button (only for existing waypoints)
        if existing_wpt is not None:
            self.move_button = ttk.Button(button_frame, text="Wegpunkt verschieben", command=self.start_move_mode)
            self.move_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.new_button = ttk.Button(button_frame, text="Neuer Wegpunkt", command=self.new_waypoint, state=tk.DISABLED)
        self.new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add delete button for existing waypoints
        if existing_wpt is not None:
            self.delete_button = ttk.Button(button_frame, text="Löschen", command=self.delete_waypoint)
            self.delete_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Abbruch", command=self.cancel_edit)
        self.cancel_button.pack(side=tk.RIGHT)
        
        # Bind text widget changes
        self.desc_text.bind('<KeyRelease>', self.on_field_change)
        
        # Focus on name entry
        self.name_entry.focus()

    def get_icon_list_for_pyinstaller(self):
        """Generate list of icon files for PyInstaller spec file"""
        icon_files = []
        if os.path.exists(self.icons_dir):
            for icon_path in glob.glob(os.path.join(self.icons_dir, "*.png")):
                rel_path = os.path.relpath(icon_path, self.base_dir)
                icon_files.append((icon_path, rel_path))
        return icon_files
        
    def on_icon_change(self, event=None):
        """Handle icon selection change"""
        self.update_icon_display()
        self.update_save_button_state()  # Enable save button on icon change
        
    def update_icon_display(self):
        """Update the icon display next to the combobox"""
        icon_name = self.icon_var.get()
        if icon_name in self.icon_cache and 'large' in self.icon_cache[icon_name]:
            self.icon_display_label.config(image=self.icon_cache[icon_name]['large'])
            # Keep a reference to prevent garbage collection
            self.icon_display_label.image = self.icon_cache[icon_name]['large']
        else:
            self.icon_display_label.config(image="", text=icon_name[:10] + "..." if len(icon_name) > 10 else icon_name)
        
    def load_waypoint_data(self, wpt, ns):
        """Load data from existing waypoint into the edit form"""
        # Load name
        name_elem = wpt.find('gpx:name', ns)
        if name_elem is not None:
            self.name_var.set(name_elem.text)
        
        # Load description
        desc_elem = wpt.find('gpx:desc', ns)
        if desc_elem is not None:
            # Extract plain text from HTML description
            desc_text = desc_elem.text or ""
            # Simple HTML to text conversion
            import re
            # Remove HTML tags but keep content
            desc_text = re.sub(r'<h2>.*?</h2>', '', desc_text)
            desc_text = re.sub(r'<p><a.*?>(.*?)</a></p>', '', desc_text)  # Remove links from description
            desc_text = desc_text.strip()
            self.desc_text.insert("1.0", desc_text)
        
        # Load symbol/icon
        sym_elem = wpt.find('gpx:sym', ns)
        if sym_elem is not None:
            symbol = sym_elem.text
            # Find matching icon key
            for key, value in self.garmin_icons.items():
                if value == symbol:
                    self.icon_var.set(key)
                    break
        
        # Load links
        link_elements = wpt.findall('gpx:link', ns)
        for i, link_elem in enumerate(link_elements[:3]):  # Max 3 links
            href = link_elem.get('href')
            if href and i < len(self.link_vars):
                self.link_vars[i].set(href)
        
    def delete_waypoint(self):
        """Delete the current waypoint file"""
        if self.current_waypoint and os.path.exists(self.current_waypoint):
            result = messagebox.askyesno("Löschen bestätigen", 
                                       f"Möchten Sie den Waypoint '{self.current_waypoint}' wirklich löschen?")
            if result:
                try:
                    os.remove(self.current_waypoint)
                    messagebox.showinfo("Gelöscht", f"Waypoint {self.current_waypoint} wurde gelöscht.")
                    self.edit_window.destroy()
                    self.edit_window = None
                    # Refresh waypoints display
                    self.load_waypoints()
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Löschen: {e}")
    
    def on_name_change(self, *args):
        self.update_save_button_state()

        # Disable new button when editing after save
        if self.waypoint_saved and hasattr(self, 'new_button') and self.new_button.winfo_exists():
            self.new_button.config(state=tk.DISABLED)

    def on_field_change(self, *args):
        self.update_save_button_state()
        
        # Disable new button when editing after save
        if self.waypoint_saved and hasattr(self, 'new_button') and self.new_button.winfo_exists():
            self.new_button.config(state=tk.DISABLED)
    
    def update_save_button_state(self):
        """Update save button state based on name field"""
        if hasattr(self, 'save_button') and self.save_button.winfo_exists():
            if self.name_var.get().strip():
                self.save_button.config(state=tk.NORMAL)
            else:
                self.save_button.config(state=tk.DISABLED)
            
    def save_waypoint(self):
        if not self.name_var.get().strip():
            messagebox.showerror("Fehler", "Name ist erforderlich!")
            return
            
        # Generate random filename if new waypoint
        if not self.current_waypoint:
            self.current_waypoint = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + '.gpx'
        
        # Create GPX content
        gpx_content = self.create_gpx_content()
        
        # Save file
        try:
            with open(self.current_waypoint, 'w', encoding='utf-8') as f:
                f.write(gpx_content)
            
            # Create custom success popup that auto-closes
            self.show_auto_close_message("Erfolg", f"Waypoint gespeichert als: {self.current_waypoint}")
            
            # Enable new waypoint button and mark as saved
            self.new_button.config(state=tk.NORMAL)
            self.waypoint_saved = True
            
            # Refresh waypoints display without changing map position/zoom
            self.load_waypoints()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def show_auto_close_message(self, title, message):
        """Show a message dialog that auto-closes after 500ms"""
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("300x100")
        popup.transient(self.root)
        popup.grab_set()
        
        # Center the popup
        popup.geometry("+%d+%d" % (self.root.winfo_rootx() + 300, self.root.winfo_rooty() + 200))
        
        # Add message
        label = tk.Label(popup, text=message, wraplength=280, justify=tk.CENTER)
        label.pack(expand=True)
        
        # Auto-close after 500ms
        popup.after(500, popup.destroy)
    
    def auto_save_waypoint(self):
        """Automatically save waypoint without user notification"""
        try:
            # Create GPX content
            gpx_content = self.create_gpx_content()
            
            # Save file silently
            with open(self.current_waypoint, 'w', encoding='utf-8') as f:
                f.write(gpx_content)
                
        except Exception as e:
            print(f"Auto-save failed: {e}")  # Silent error logging
            
    def create_gpx_content(self):
        # Create GPX XML structure
        gpx = ET.Element('gpx', {
            'version': '1.1',
            'creator': 'Garmin Waypoint Creator',
            'xmlns': 'http://www.topografix.com/GPX/1/1',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns:gpxx': 'http://www.garmin.com/xmlschemas/GpxExtensions/v3',
            'xmlns:ctx': 'http://www.garmin.com/xmlschemas/CreationTimeExtension/v1',
            'xsi:schemaLocation': 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/CreationTimeExtension/v1 http://www.garmin.com/xmlschemas/CreationTimeExtensionv1.xsd'
        })
        
        # Add waypoint
        wpt = ET.SubElement(gpx, 'wpt', {
            'lat': str(self.waypoint_lat),
            'lon': str(self.waypoint_lon)
        })
        
        # Add name
        name_elem = ET.SubElement(wpt, 'name')
        name_elem.text = self.name_var.get().strip()
        
        # Create description with HTML
        desc_content = f"<h2>{self.name_var.get().strip()}</h2>\n"
        
        # Add description text
        desc_text = self.desc_text.get("1.0", tk.END).strip()
        if desc_text:
            desc_content += desc_text + "\n"
        
        # Add hyperlinks as HTML
        for link_var in self.link_vars:
            link = link_var.get().strip()
            if link:
                desc_content += f'<p><a href="{link}" target="_blank">{link}</a></p>\n'
        
        desc_elem = ET.SubElement(wpt, 'desc')
        desc_elem.text = desc_content
        
        # Add links as GPX standard elements (first)
        for link_var in self.link_vars:
            link = link_var.get().strip()
            if link:
                link_elem = ET.SubElement(wpt, 'link')
                link_elem.set('href', link)
        
        # Add symbol (icon) after links
        sym_elem = ET.SubElement(wpt, 'sym')
        sym_elem.text = self.garmin_icons[self.icon_var.get()]
        
        # Add Garmin extensions
        extensions = ET.SubElement(wpt, 'extensions')
        gpxx_elem = ET.SubElement(extensions, 'gpxx:WaypointExtension')
        
        # Add display mode (only SymbolAndName needed)
        display_mode = ET.SubElement(gpxx_elem, 'gpxx:DisplayMode')
        display_mode.text = 'SymbolAndName'
        
        # Add time at the end of extensions
        ctx_elem = ET.SubElement(extensions, 'ctx:CreationTimeExtension')
        ctx_elem.set('xmlns:ctx', 'http://www.garmin.com/xmlschemas/CreationTimeExtension/v1')
        ctx_time = ET.SubElement(ctx_elem, 'ctx:CreationTime')
        ctx_time.text = datetime.utcnow().isoformat() + 'Z'
        
        # Convert to pretty XML string
        rough_string = ET.tostring(gpx, encoding='unicode')
        reparsed = xml.dom.minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
        
    def new_waypoint(self):
        self.edit_window.destroy()
        self.edit_window = None
        
    def cancel_edit(self):
        # Reset move mode if active
        if self.move_mode:
            self.move_mode = False
            self.info_label.config(text="Klicken Sie auf die Karte, um einen Waypoint zu erstellen")
            if self.temp_move_marker:
                self.temp_move_marker.delete()
                self.temp_move_marker = None
        
        self.edit_window.destroy()
        self.edit_window = None
        
    def close_program(self):
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.close_program)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = GarminWaypointCreator()
        app.run()
    except ImportError as e:
        print("Fehler: tkintermapview ist nicht installiert.")
        print("Bitte installieren Sie es mit: pip install tkintermapview")
        print(f"Detaillierter Fehler: {e}")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        input("Drücken Sie Enter zum Beenden...")