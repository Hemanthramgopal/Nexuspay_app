"""Initialize the local SQLite catalog used by NexusPay."""

import json
import sqlite3


def setup_database() -> None:
    """Recreate the local catalog with agent-readable product metadata."""
    conn = sqlite3.connect("catalog.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            base_price INTEGER NOT NULL,
            min_price INTEGER NOT NULL,
            stock INTEGER NOT NULL,
            compatibility_tags TEXT NOT NULL,
            recommended_addon_id TEXT,
            specifications TEXT
        )
        """
    )

    inventory = [
        ("smartphone", "Nexus Galaxy Smartphone", "electronics", "A mobile phone device to call friends, browse the web, and take photos.", 25000, 22000, 10, ["usb-c", "fast-charging", "mobile"], "usb_c_charger", {"os": "Android", "display": "6.7 inch OLED", "charging_wattage": 65}),
        ("laptop", "Ultrabook Pro 14", "electronics", "A high-performance laptop computer perfect for software development, coding, and heavy workloads.", 55000, 51000, 7, ["usb-c", "thunderbolt", "workstation"], "premium_monitor", {"ram": "32GB", "processor": "M3-tier", "storage": "1TB SSD"}),
        ("gaming_laptop", "Pro Gaming Laptop 15.6\"", "electronics", "A powerful gaming laptop with high-performance hardware for gaming, streaming, and demanding creative workloads.", 65000, 55000, 6, ["gaming", "laptop", "high-performance", "streaming"], "wireless_headphones", {"display": "15.6 inch", "graphics": "Dedicated gaming GPU", "storage": "1TB SSD"}),
        ("gaming_console", "NextGen Gaming Console", "electronics", "Home entertainment system for playing video games and streaming media.", 10000, 9000, 3, ["gaming", "hdmi", "wireless"], "wireless_headphones", {"storage": "1TB", "resolution": "4K", "controller_support": "Wireless"}),
        ("mechanical_keyboard_87keys", "Mechanical Keyboard 87 Keys", "electronics", "Tactile typing peripheral for programmers, coders, and gamers.", 4000, 3500, 12, ["mechanical", "usb-c", "gaming", "desk-setup"], "ergonomic_mouse", {"switches": "Tactile Blue", "layout": "Tenkeyless 87-key", "rgb": True}),
        ("premium_monitor", "27-inch 4K Premium Monitor", "electronics", "High resolution external screen display for visual clarity.", 18000, 16000, 5, ["4k", "hdmi", "displayport", "usb-c"], "mechanical_keyboard_87keys", {"resolution": "3840x2160", "refresh_rate": "144Hz", "panel": "IPS"}),
        ("ergonomic_mouse", "Ergonomic Wireless Mouse", "accessories", "Comfortable pointing device for long hours of desk work.", 2000, 1800, 20, ["wireless", "ergonomic", "desk-setup"], "mechanical_keyboard_87keys", {"connectivity": "Bluetooth and 2.4GHz", "buttons": 6, "battery_life": "70 hours"}),
        ("usb_c_charger", "65W Fast USB-C Charger", "accessories", "Power adapter brick and cable to quickly charge devices.", 800, 750, 30, ["usb-c", "fast-charging", "power-delivery"], "smartphone", {"wattage": 65, "ports": 2, "power_delivery": True}),
        ("wireless_headphones", "Noise-Cancelling Headphones", "audio", "Over-ear audio device for listening to music, great for travel.", 3500, 3000, 18, ["wireless", "bluetooth", "noise-cancelling"], "bluetooth_speaker", {"battery_life": "35 hours", "codec": "AAC", "microphones": 4}),
        ("smartwatch", "Nexus Smartwatch", "wearable", "Wrist-worn fitness tracker and notification device.", 8000, 7000, 15, ["wearable", "bluetooth", "usb-c"], "usb_c_charger", {"display": "1.8 inch AMOLED", "water_resistance": "5 ATM", "gps": True}),
        ("tablet", "Pro Display Tablet", "mobile", "Touchscreen slate computer for reading, drawing, and media consumption.", 20000, 18000, 8, ["usb-c", "tablet", "stylus"], "usb_c_charger", {"display": "12.9 inch LCD", "storage": "256GB", "stylus_support": True}),
        ("bluetooth_speaker", "Boom Bass Speaker", "audio", "Portable wireless music player, perfect for the gym or parties.", 3000, 2500, 25, ["bluetooth", "portable", "water-resistant"], "wireless_headphones", {"output_power": "40W", "battery_life": "18 hours", "water_resistance": "IPX7"}),
    ]
    cursor.executemany(
        """
        INSERT INTO products (
            id, name, category, description, base_price, min_price, stock,
            compatibility_tags, recommended_addon_id, specifications
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (*product[:7], json.dumps(product[7]), product[8], json.dumps(product[9]))
            for product in inventory
        ],
    )
    conn.commit()
    conn.close()
    
    print("Local SQLite database 'catalog.db' updated with agent-readable metadata.")

if __name__ == "__main__":
    setup_database()
