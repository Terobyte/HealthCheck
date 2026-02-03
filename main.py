import flet as ft
import threading
import network_sender
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API keys are loaded
gemini_key = os.getenv("GEMINI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not all([gemini_key, telegram_token, telegram_chat_id]):
    print("⚠️  Warning: Some API keys are missing from .env file")
    print("   Application will continue but Telegram/Gemini may not work")


class HealthCheckApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Health Check"
        self.page.theme_mode = ft.ThemeMode.DARK
        
        # Set window properties for full native look
        self.page.window_width = 800
        self.page.window_height = 700
        self.page.window_min_width = 600
        self.page.window_min_height = 500
        
        # Set background color (blue tint with transparency)
        self.page.bgcolor = ft.Colors.with_opacity(0.95, ft.Colors.BLUE_900)
        self.page.window_bgcolor = ft.Colors.with_opacity(0.95, ft.Colors.BLUE_900)
        
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        # Status messages for scrolling text
        self.status_messages = [
            "Ready to scan...",
            "Initializing diagnostics...",
            "Checking system health...",
            "Analyzing network status...",
            "Scanning disk usage...",
            "Measuring RAM performance...",
            "Testing network speed...",
            "Complete!"
        ]
        self.current_status_index = 0
        self.is_scanning = False
        
        # Initialize UI components
        self.output_field = ft.TextField(
            value="Click 'Run diagnostics' to begin system health check...",
            multiline=True,
            min_lines=10,
            max_lines=10,
            read_only=True,
            border_color=ft.Colors.TRANSPARENT,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_GREY_800),
            color=ft.Colors.WHITE,
            width=530,
            text_size=12
        )
        
        self.status_text = ft.Text(
            self.status_messages[0],
            size=14,
            color=ft.Colors.WHITE70,
            text_align=ft.TextAlign.CENTER
        )
        
        self.btn_diagnostics = ft.Button(
            "Run diagnostics",
            width=200,
            height=50,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=10
            ),
            on_click=self.start_scan,
            disabled=False
        )
        
        self.setup_ui()
    
    def setup_ui(self):
        """
        Create UI components directly on the page (Full Window).
        """
        # Create main column directly on page (no container wrapper)
        main_content = ft.Column(
            [
                # Title
                ft.Text(
                    "Health Check",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER
                ),
                
                ft.Container(height=20),  # Spacing
                
                # Scrolling status text with glass effect
                ft.Container(
                    content=self.status_text,
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                    width=500
                ),
                
                ft.Container(height=30),  # Spacing
                
                # Run Diagnostics Button
                self.btn_diagnostics,
                
                ft.Container(height=30),  # Spacing
                
                # Output text area
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Diagnostics Output:",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE
                            ),
                            ft.Container(height=10),
                            self.output_field
                        ]
                    ),
                    padding=15,
                    border_radius=15,
                    bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                    width=560,
                    height=250
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            scroll=ft.ScrollMode.AUTO  # Add scroll for small windows
        )
        
        # Add directly to page with minimal padding
        self.page.padding = 20
        self.page.add(main_content)
    
    def update_status(self, message: str):
        """
        Update the status text with animation effect.
        """
        self.status_text.value = message
        self.page.update()
    
    def animate_status(self):
        """
        Animate status messages during scanning.
        """
        while self.is_scanning:
            self.current_status_index = (self.current_status_index + 1) % len(self.status_messages)
            self.update_status(self.status_messages[self.current_status_index])
            time.sleep(1.5)
    
    def start_scan(self, e):
        """
        Start the diagnostic scan in a separate thread.
        """
        self.is_scanning = True
        self.btn_diagnostics.disabled = True
        self.btn_diagnostics.bgcolor = ft.Colors.GREY_400
        self.output_field.value = "⏳ Collecting data and analyzing... Please wait..."
        self.page.update()
        
        # Start status animation
        animation_thread = threading.Thread(target=self.animate_status, daemon=True)
        animation_thread.start()
        
        # Run diagnostics in separate thread
        threading.Thread(target=self.run_diagnostics).start()
    
    def run_diagnostics(self):
        """
        Execute the diagnostic process and update UI.
        """
        try:
            # Run the main process from network_sender
            result = network_sender.run_process()
            
            # Update output field with results
            self.output_field.value = result
        except Exception as e:
            self.output_field.value = f"❌ Error during diagnostics:\n{str(e)}"
        
        # Stop animation and re-enable button
        self.is_scanning = False
        self.btn_diagnostics.disabled = False
        self.btn_diagnostics.bgcolor = ft.Colors.BLUE_600
        self.update_status("Ready to scan...")
        self.page.update()


def main(page: ft.Page):
    """
    Main entry point for the Flet application.
    """
    app = HealthCheckApp(page)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
