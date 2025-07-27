"""Main TUI application for Loguru configuration."""

from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Label
from textual.screen import Screen

from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort
from src.domain.entities.logger_config import LoggerConfig


class LoguruConfigApp(App):
    """Main TUI application for Loguru configuration."""
    
    CSS = """
    .title {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
    }
    
    .sidebar {
        dock: left;
        width: 30;
        background: $surface;
    }
    
    .main-content {
        background: $background;
    }
    
    .status-bar {
        dock: bottom;
        height: 3;
        background: $surface;
    }
    
    Button {
        margin: 1;
        min-width: 20;
    }
    
    .config-info {
        margin: 1;
        padding: 1;
        border: solid $primary;
    }
    """
    
    TITLE = "Loguru Configuration Tool"
    SUB_TITLE = "Comprehensive logging setup with real-time preview"
    
    def __init__(
        self,
        config_port: LoggerConfigurationPort,
        logger_port: LoggerApplicationPort
    ):
        """
        Initialize the TUI application.
        
        Args:
            config_port: Logger configuration port.
            logger_port: Logger application port.
        """
        super().__init__()
        self._config_port = config_port
        self._logger_port = logger_port
        self._current_config: Optional[LoggerConfig] = None
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        
        with Container():
            # Title bar
            yield Static("🎯 Loguru Configuration Tool", classes="title")
            
            with Horizontal():
                # Sidebar with navigation
                with Vertical(classes="sidebar"):
                    yield Label("Configuration Sections", id="sidebar-title")
                    yield Button("📊 Basic Settings", id="basic-settings")
                    yield Button("📁 File Configuration", id="file-config")
                    yield Button("🎨 Formatting & Colors", id="formatting")
                    yield Button("🔄 Rotation & Retention", id="rotation")
                    yield Button("📤 Handlers & Output", id="handlers")
                    yield Button("⚙️ Advanced Options", id="advanced")
                    yield Button("🧪 Test Configuration", id="test-config")
                    yield Button("💾 Save/Load", id="save-load")
                
                # Main content area
                with Vertical(classes="main-content"):
                    yield Static("Welcome to Loguru Configuration Tool!", id="main-content")
                    yield Static(self._get_welcome_message(), id="welcome-message")
                    
                    # Configuration info panel
                    with Container(classes="config-info"):
                        yield Label("Current Configuration: None", id="config-status")
                        yield Label("Handlers: 0", id="handlers-count")
                        yield Label("Status: Not configured", id="status")
            
            # Status bar
            with Container(classes="status-bar"):
                yield Label("Ready - Select a configuration section to begin", id="status-message")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "Loguru Configuration Tool"
        self.sub_title = "Press Ctrl+C to exit"
        
        # Load default configuration
        self.call_later(self._load_default_config)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "basic-settings":
            self._show_basic_settings()
        elif button_id == "file-config":
            self._show_file_config()
        elif button_id == "formatting":
            self._show_formatting()
        elif button_id == "rotation":
            self._show_rotation()
        elif button_id == "handlers":
            self._show_handlers()
        elif button_id == "advanced":
            self._show_advanced()
        elif button_id == "test-config":
            self._show_test_config()
        elif button_id == "save-load":
            self._show_save_load()
    
    async def _load_default_config(self) -> None:
        """Load the default configuration."""
        try:
            config = await self._config_port.load_configuration("default")
            if config:
                self._current_config = config
                self._update_config_display()
            else:
                # Create default configuration
                self._current_config = LoggerConfig(name="default")
                self._update_config_display()
        except Exception as e:
            self._update_status(f"Error loading configuration: {e}")
    
    async def load_configuration(self, name: str) -> None:
        """Load a specific configuration by name."""
        try:
            config = await self._config_port.load_configuration(name)
            if config:
                self._current_config = config
                self._update_config_display()
                self._update_status(f"Loaded configuration: {name}")
            else:
                self._update_status(f"Configuration not found: {name}")
        except Exception as e:
            self._update_status(f"Error loading configuration: {e}")
    
    def _update_config_display(self) -> None:
        """Update the configuration display."""
        if self._current_config:
            config_status = self.query_one("#config-status", Label)
            handlers_count = self.query_one("#handlers-count", Label)
            status = self.query_one("#status", Label)
            
            config_status.update(f"Current Configuration: {self._current_config.name}")
            handlers_count.update(f"Handlers: {len(self._current_config.handlers)}")
            status_text = "Enabled" if self._current_config.enabled else "Disabled"
            status.update(f"Status: {status_text}")
    
    def _update_status(self, message: str) -> None:
        """Update the status message."""
        status_message = self.query_one("#status-message", Label)
        status_message.update(message)
    
    def _show_basic_settings(self) -> None:
        """Show basic settings screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("📊 Basic Settings\n\nConfigure fundamental logging options:\n\n• Enable/Disable logging\n• Set global log level\n• Configure async logging\n\n[Coming soon in full TUI implementation]")
        self._update_status("Basic Settings - Configure fundamental logging options")
    
    def _show_file_config(self) -> None:
        """Show file configuration screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("📁 File Configuration\n\nConfigure file output settings:\n\n• Log file paths and naming\n• File encoding and modes\n• Directory structure\n\n[Coming soon in full TUI implementation]")
        self._update_status("File Configuration - Set up log file output")
    
    def _show_formatting(self) -> None:
        """Show formatting screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("🎨 Formatting & Colors\n\nCustomize log appearance:\n\n• Format presets (simple, detailed, JSON)\n• Custom format strings\n• Color schemes and styling\n• Backtrace and diagnostic options\n\n[Coming soon in full TUI implementation]")
        self._update_status("Formatting - Customize log appearance and colors")
    
    def _show_rotation(self) -> None:
        """Show rotation screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("🔄 Rotation & Retention\n\nManage log file lifecycle:\n\n• Size-based rotation\n• Time-based rotation\n• Retention policies\n• Compression options\n\n[Coming soon in full TUI implementation]")
        self._update_status("Rotation - Configure log file rotation and retention")
    
    def _show_handlers(self) -> None:
        """Show handlers screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("📤 Handlers & Output\n\nConfigure output destinations:\n\n• Console output\n• File handlers\n• Syslog integration\n• Systemd journal\n\n[Coming soon in full TUI implementation]")
        self._update_status("Handlers - Configure output destinations")
    
    def _show_advanced(self) -> None:
        """Show advanced options screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("⚙️ Advanced Options\n\nAdvanced configuration:\n\n• Custom filters\n• Exception handling\n• Performance tuning\n• Integration options\n\n[Coming soon in full TUI implementation]")
        self._update_status("Advanced - Configure advanced logging options")
    
    def _show_test_config(self) -> None:
        """Show test configuration screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("🧪 Test Configuration\n\nTest your logging setup:\n\n• Preview log output\n• Generate test messages\n• Validate configuration\n• Performance testing\n\n[Coming soon in full TUI implementation]")
        self._update_status("Test Configuration - Preview and validate your setup")
    
    def _show_save_load(self) -> None:
        """Show save/load screen."""
        main_content = self.query_one("#main-content", Static)
        main_content.update("💾 Save/Load Configuration\n\nManage configurations:\n\n• Save current settings\n• Load saved configurations\n• Import/Export (JSON, YAML, TOML)\n• Configuration templates\n\n[Coming soon in full TUI implementation]")
        self._update_status("Save/Load - Manage your configurations")
    
    def _get_welcome_message(self) -> str:
        """Get the welcome message."""
        return """
Welcome to the Loguru Configuration Tool!

This comprehensive TUI provides an intuitive interface for configuring
Loguru logging with real-time preview and testing capabilities.

🎯 Features:
• Interactive configuration of all Loguru options
• Real-time preview of log output
• Configuration testing and validation
• Save/load configuration profiles
• Import/export in multiple formats

📋 Getting Started:
1. Select a configuration section from the sidebar
2. Adjust settings using the interactive controls
3. Preview your changes in real-time
4. Test the configuration with sample messages
5. Save your configuration for future use

💡 Tip: Use the CLI interface for quick configuration changes:
   python loguru_config_tui.py --enable --log-level DEBUG --file logs/app.log

Press any button in the sidebar to begin configuration!
        """
