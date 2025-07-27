#!/usr/bin/env python3
"""
Configuration Management Tool for FastAPI Clean Architecture Template

A terminal-friendly configuration tool using Dynaconf for layered settings
management and Textual for the user interface, following hexagonal architecture
principles.

Author: Codegen
Python: 3.12+
Dependencies: textual>=5.0.1,<6, dynaconf==3.2.11
"""

import asyncio
import json
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union
from urllib.parse import urlparse

from dynaconf import Dynaconf
from rich.console import Console
from rich.syntax import Syntax
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TextArea,
)


# ============================================================================
# DOMAIN LAYER - Core Business Logic (Pure Python, No External Dependencies)
# ============================================================================

class ConfigurationFormat(Enum):
    """Supported configuration file formats."""
    TOML = "toml"
    YAML = "yaml"
    JSON = "json"
    INI = "ini"
    PY = "py"


class Environment(Enum):
    """Supported environment types."""
    DEFAULT = "default"
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass(frozen=True)
class ConfigurationKey:
    """Value object representing a configuration key."""
    name: str
    
    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Configuration key cannot be empty")
        if not self.name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Configuration key must be alphanumeric with underscores/hyphens")


@dataclass(frozen=True)
class ConfigurationValue:
    """Value object representing a configuration value with type information."""
    value: Any
    value_type: str = field(init=False)
    
    def __post_init__(self) -> None:
        object.__setattr__(self, 'value_type', type(self.value).__name__)
    
    def validate_url(self) -> bool:
        """Validate if value is a valid URL."""
        if not isinstance(self.value, str):
            return False
        try:
            result = urlparse(self.value)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def validate_path(self) -> bool:
        """Validate if value is a valid file path."""
        if not isinstance(self.value, str):
            return False
        try:
            Path(self.value)
            return True
        except Exception:
            return False


@dataclass
class ConfigurationItem:
    """Domain entity representing a single configuration item."""
    key: ConfigurationKey
    value: ConfigurationValue
    environment: Environment = Environment.DEFAULT
    description: Optional[str] = None
    
    def update_value(self, new_value: Any) -> None:
        """Update the configuration value."""
        self.value = ConfigurationValue(new_value)
    
    def is_sensitive(self) -> bool:
        """Check if this configuration item contains sensitive data."""
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']
        return any(keyword in self.key.name.lower() for keyword in sensitive_keywords)


@dataclass
class ConfigurationSet:
    """Aggregate root for managing a collection of configuration items."""
    project_name: str
    format: ConfigurationFormat
    items: Dict[str, ConfigurationItem] = field(default_factory=dict)
    create_secrets_file: bool = False
    
    def add_item(self, item: ConfigurationItem) -> None:
        """Add a configuration item to the set."""
        if not item.key.name:
            raise ValueError("Configuration key cannot be empty")
        self.items[item.key.name] = item
    
    def remove_item(self, key_name: str) -> bool:
        """Remove a configuration item by key name."""
        if key_name in self.items:
            del self.items[key_name]
            return True
        return False
    
    def get_item(self, key_name: str) -> Optional[ConfigurationItem]:
        """Get a configuration item by key name."""
        return self.items.get(key_name)
    
    def get_items_by_environment(self, env: Environment) -> List[ConfigurationItem]:
        """Get all configuration items for a specific environment."""
        return [item for item in self.items.values() if item.environment == env]
    
    def validate_all_items(self) -> List[str]:
        """Validate all configuration items and return list of errors."""
        errors = []
        for item in self.items.values():
            try:
                # Validate key
                ConfigurationKey(item.key.name)
            except ValueError as e:
                errors.append(f"Invalid key '{item.key.name}': {e}")
        return errors


class ConfigurationDomainService:
    """Domain service for configuration business logic."""
    
    @staticmethod
    def generate_default_config(project_name: str, format: ConfigurationFormat) -> ConfigurationSet:
        """Generate a default configuration set for a new project."""
        config_set = ConfigurationSet(project_name=project_name, format=format)
        
        # Add common configuration items
        default_items = [
            ConfigurationItem(
                key=ConfigurationKey("PROJECT_NAME"),
                value=ConfigurationValue(project_name),
                description="Name of the project"
            ),
            ConfigurationItem(
                key=ConfigurationKey("DEBUG"),
                value=ConfigurationValue(True),
                environment=Environment.DEVELOPMENT,
                description="Enable debug mode"
            ),
            ConfigurationItem(
                key=ConfigurationKey("DATABASE_URL"),
                value=ConfigurationValue("postgresql://localhost:5432/mydb"),
                description="Database connection URL"
            ),
            ConfigurationItem(
                key=ConfigurationKey("SECRET_KEY"),
                value=ConfigurationValue("your-secret-key-here"),
                description="Secret key for encryption"
            ),
        ]
        
        for item in default_items:
            config_set.add_item(item)
        
        return config_set
    
    @staticmethod
    def validate_configuration_format(format: ConfigurationFormat, content: str) -> bool:
        """Validate configuration content against its format."""
        try:
            if format == ConfigurationFormat.JSON:
                json.loads(content)
            # Add other format validations as needed
            return True
        except Exception:
            return False


# ============================================================================
# APPLICATION LAYER - Use Cases and Services
# ============================================================================

class ConfigurationRepositoryPort(Protocol):
    """Port for configuration persistence operations."""
    
    async def load_configuration(self, project_root: Path) -> Optional[ConfigurationSet]:
        """Load configuration from storage."""
        ...
    
    async def save_configuration(self, config_set: ConfigurationSet, project_root: Path) -> bool:
        """Save configuration to storage."""
        ...
    
    async def backup_configuration(self, project_root: Path) -> bool:
        """Create a backup of the current configuration."""
        ...
    
    async def get_available_environments(self, project_root: Path) -> List[Environment]:
        """Get list of available environments."""
        ...


class ValidationServicePort(Protocol):
    """Port for validation operations."""
    
    def validate_key(self, key: str) -> List[str]:
        """Validate a configuration key."""
        ...
    
    def validate_value(self, value: Any, value_type: str) -> List[str]:
        """Validate a configuration value."""
        ...


@dataclass
class CreateConfigurationCommand:
    """Command for creating a new configuration."""
    project_name: str
    format: ConfigurationFormat
    create_secrets_file: bool = False


@dataclass
class UpdateConfigurationCommand:
    """Command for updating a configuration item."""
    key_name: str
    new_value: Any
    environment: Environment = Environment.DEFAULT
    description: Optional[str] = None


@dataclass
class DeleteConfigurationCommand:
    """Command for deleting a configuration item."""
    key_name: str


class CreateConfigurationUseCase:
    """Use case for creating a new configuration."""
    
    def __init__(self, repository: ConfigurationRepositoryPort):
        self.repository = repository
    
    async def execute(self, command: CreateConfigurationCommand, project_root: Path) -> ConfigurationSet:
        """Execute the create configuration use case."""
        config_set = ConfigurationDomainService.generate_default_config(
            command.project_name, command.format
        )
        config_set.create_secrets_file = command.create_secrets_file
        
        await self.repository.save_configuration(config_set, project_root)
        return config_set


class UpdateConfigurationUseCase:
    """Use case for updating a configuration item."""
    
    def __init__(self, repository: ConfigurationRepositoryPort, validator: ValidationServicePort):
        self.repository = repository
        self.validator = validator
    
    async def execute(self, command: UpdateConfigurationCommand, config_set: ConfigurationSet) -> bool:
        """Execute the update configuration use case."""
        # Validate the new value
        errors = self.validator.validate_value(command.new_value, type(command.new_value).__name__)
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
        
        # Update or create the configuration item
        if command.key_name in config_set.items:
            item = config_set.items[command.key_name]
            item.update_value(command.new_value)
            if command.description:
                item.description = command.description
        else:
            item = ConfigurationItem(
                key=ConfigurationKey(command.key_name),
                value=ConfigurationValue(command.new_value),
                environment=command.environment,
                description=command.description
            )
            config_set.add_item(item)
        
        return True


class DeleteConfigurationUseCase:
    """Use case for deleting a configuration item."""
    
    def __init__(self, repository: ConfigurationRepositoryPort):
        self.repository = repository
    
    async def execute(self, command: DeleteConfigurationCommand, config_set: ConfigurationSet) -> bool:
        """Execute the delete configuration use case."""
        return config_set.remove_item(command.key_name)


class ConfigurationApplicationService:
    """Application service coordinating configuration operations."""
    
    def __init__(
        self,
        repository: ConfigurationRepositoryPort,
        validator: ValidationServicePort
    ):
        self.repository = repository
        self.validator = validator
        self.create_use_case = CreateConfigurationUseCase(repository)
        self.update_use_case = UpdateConfigurationUseCase(repository, validator)
        self.delete_use_case = DeleteConfigurationUseCase(repository)
    
    async def initialize_project(self, command: CreateConfigurationCommand, project_root: Path) -> ConfigurationSet:
        """Initialize a new project configuration."""
        return await self.create_use_case.execute(command, project_root)
    
    async def load_existing_configuration(self, project_root: Path) -> Optional[ConfigurationSet]:
        """Load existing configuration from storage."""
        return await self.repository.load_configuration(project_root)
    
    async def update_configuration_item(
        self, command: UpdateConfigurationCommand, config_set: ConfigurationSet
    ) -> bool:
        """Update a configuration item."""
        return await self.update_use_case.execute(command, config_set)
    
    async def delete_configuration_item(
        self, command: DeleteConfigurationCommand, config_set: ConfigurationSet
    ) -> bool:
        """Delete a configuration item."""
        return await self.delete_use_case.execute(command, config_set)
    
    async def save_configuration(self, config_set: ConfigurationSet, project_root: Path) -> bool:
        """Save configuration to storage."""
        await self.repository.backup_configuration(project_root)
        return await self.repository.save_configuration(config_set, project_root)


# ============================================================================
# INFRASTRUCTURE LAYER - Adapters for External Concerns
# ============================================================================

class DynaconfConfigurationRepository:
    """Concrete implementation of ConfigurationRepositoryPort using Dynaconf."""
    
    def __init__(self):
        self.console = Console()
    
    async def load_configuration(self, project_root: Path) -> Optional[ConfigurationSet]:
        """Load configuration using Dynaconf."""
        try:
            # Look for existing settings files
            settings_files = [
                project_root / "settings.toml",
                project_root / "settings.yaml",
                project_root / "settings.json",
                project_root / "settings.ini",
                project_root / "settings.py",
            ]
            
            existing_file = None
            config_format = ConfigurationFormat.TOML
            
            for settings_file in settings_files:
                if settings_file.exists():
                    existing_file = settings_file
                    config_format = ConfigurationFormat(settings_file.suffix[1:])
                    break
            
            if not existing_file:
                return None
            
            # Load with Dynaconf
            settings = Dynaconf(
                settings_files=[str(existing_file)],
                environments=True,
                load_dotenv=True,
            )
            
            # Convert to domain objects
            config_set = ConfigurationSet(
                project_name=getattr(settings, 'PROJECT_NAME', 'Unknown'),
                format=config_format
            )
            
            # Load all settings
            for key in settings.keys():
                value = settings.get(key)
                item = ConfigurationItem(
                    key=ConfigurationKey(key),
                    value=ConfigurationValue(value),
                    environment=Environment.DEFAULT
                )
                config_set.add_item(item)
            
            return config_set
            
        except Exception as e:
            self.console.print(f"[red]Error loading configuration: {e}[/red]")
            return None
    
    async def save_configuration(self, config_set: ConfigurationSet, project_root: Path) -> bool:
        """Save configuration using Dynaconf format."""
        try:
            settings_file = project_root / f"settings.{config_set.format.value}"
            
            # Prepare data for saving
            data = {}
            for item in config_set.items.values():
                data[item.key.name] = item.value.value
            
            # Write based on format
            if config_set.format == ConfigurationFormat.TOML:
                import tomli_w
                with open(settings_file, 'wb') as f:
                    tomli_w.dump(data, f)
            elif config_set.format == ConfigurationFormat.JSON:
                with open(settings_file, 'w') as f:
                    json.dump(data, f, indent=2)
            # Add other formats as needed
            
            # Create secrets file if requested
            if config_set.create_secrets_file:
                secrets_file = project_root / ".secrets"
                sensitive_data = {
                    item.key.name: item.value.value
                    for item in config_set.items.values()
                    if item.is_sensitive()
                }
                if sensitive_data:
                    with open(secrets_file, 'w') as f:
                        for key, value in sensitive_data.items():
                            f.write(f"{key}={value}\n")
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error saving configuration: {e}[/red]")
            return False
    
    async def backup_configuration(self, project_root: Path) -> bool:
        """Create backup of existing configuration files."""
        try:
            settings_files = [
                project_root / "settings.toml",
                project_root / "settings.yaml", 
                project_root / "settings.json",
                project_root / "settings.ini",
                project_root / "settings.py",
            ]
            
            for settings_file in settings_files:
                if settings_file.exists():
                    backup_file = settings_file.with_suffix(f"{settings_file.suffix}.bak")
                    shutil.copy2(settings_file, backup_file)
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error creating backup: {e}[/red]")
            return False
    
    async def get_available_environments(self, project_root: Path) -> List[Environment]:
        """Get available environments from configuration."""
        return list(Environment)


class ConfigurationValidator:
    """Concrete implementation of ValidationServicePort."""
    
    def validate_key(self, key: str) -> List[str]:
        """Validate a configuration key."""
        errors = []
        
        if not key or not key.strip():
            errors.append("Key cannot be empty")
        elif not key.replace("_", "").replace("-", "").isalnum():
            errors.append("Key must be alphanumeric with underscores/hyphens only")
        elif len(key) > 100:
            errors.append("Key must be less than 100 characters")
        
        return errors
    
    def validate_value(self, value: Any, value_type: str) -> List[str]:
        """Validate a configuration value."""
        errors = []
        
        if value is None:
            errors.append("Value cannot be None")
        elif isinstance(value, str) and not value.strip():
            errors.append("String value cannot be empty")
        
        return errors


# ============================================================================
# PRESENTATION LAYER - Textual UI Components (Infrastructure Adapters)
# ============================================================================

class ConfigurationWizard(ModalScreen[ConfigurationSet]):
    """Initial configuration wizard screen."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
    ]
    
    def __init__(self, app_service: ConfigurationApplicationService):
        super().__init__()
        self.app_service = app_service
        self.project_name = ""
        self.selected_format = ConfigurationFormat.TOML
        self.create_secrets = False
    
    def compose(self) -> ComposeResult:
        """Compose the wizard interface."""
        with Container(id="wizard-container"):
            yield Header()
            yield Label("🚀 FastAPI Configuration Wizard", id="wizard-title")
            yield Label("Set up your project configuration", id="wizard-subtitle")
            
            with Vertical(id="wizard-form"):
                yield Label("Project Name:")
                yield Input(placeholder="Enter project name", id="project-name-input")
                
                yield Label("Configuration Format:")
                yield Select(
                    [(format.value.upper(), format) for format in ConfigurationFormat],
                    value=ConfigurationFormat.TOML,
                    id="format-select"
                )
                
                yield Label("Create .secrets file for sensitive data?")
                yield Select(
                    [("Yes", True), ("No", False)],
                    value=False,
                    id="secrets-select"
                )
                
                with Horizontal(id="wizard-buttons"):
                    yield Button("Create Configuration", variant="primary", id="create-btn")
                    yield Button("Cancel", variant="default", id="cancel-btn")
            
            yield Footer()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "project-name-input":
            self.project_name = event.value
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "format-select":
            self.selected_format = event.value
        elif event.select.id == "secrets-select":
            self.create_secrets = event.value
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-btn":
            await self.create_configuration()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
    
    @work(exclusive=True)
    async def create_configuration(self) -> None:
        """Create the configuration."""
        if not self.project_name.strip():
            self.notify("Please enter a project name", severity="error")
            return
        
        try:
            command = CreateConfigurationCommand(
                project_name=self.project_name,
                format=self.selected_format,
                create_secrets_file=self.create_secrets
            )
            
            project_root = Path.cwd()
            config_set = await self.app_service.initialize_project(command, project_root)
            
            self.dismiss(config_set)
            
        except Exception as e:
            self.notify(f"Error creating configuration: {e}", severity="error")
    
    def action_cancel(self) -> None:
        """Cancel the wizard."""
        self.dismiss(None)


class VariableModal(ModalScreen[bool]):
    """Modal for editing configuration variables."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]
    
    def __init__(self, item: Optional[ConfigurationItem] = None):
        super().__init__()
        self.item = item
        self.is_edit_mode = item is not None
        self.key_name = item.key.name if item else ""
        self.value = str(item.value.value) if item else ""
        self.description = item.description if item else ""
    
    def compose(self) -> ComposeResult:
        """Compose the modal interface."""
        title = "Edit Variable" if self.is_edit_mode else "New Variable"
        
        with Container(id="modal-container"):
            yield Label(title, id="modal-title")
            
            with Vertical(id="modal-form"):
                yield Label("Key:")
                yield Input(
                    value=self.key_name,
                    placeholder="VARIABLE_NAME",
                    id="key-input",
                    disabled=self.is_edit_mode
                )
                
                yield Label("Value:")
                yield Input(
                    value=self.value,
                    placeholder="Enter value",
                    id="value-input"
                )
                
                yield Label("Description (optional):")
                yield Input(
                    value=self.description or "",
                    placeholder="Brief description",
                    id="description-input"
                )
                
                with Horizontal(id="modal-buttons"):
                    yield Button("Save", variant="primary", id="save-btn")
                    yield Button("Cancel", variant="default", id="cancel-btn")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "key-input":
            self.key_name = event.value
        elif event.input.id == "value-input":
            self.value = event.value
        elif event.input.id == "description-input":
            self.description = event.value
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            await self.save_variable()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
    
    async def save_variable(self) -> None:
        """Save the variable."""
        if not self.key_name.strip():
            self.notify("Key cannot be empty", severity="error")
            return
        
        if not self.value.strip():
            self.notify("Value cannot be empty", severity="error")
            return
        
        # Convert value to appropriate type
        converted_value = self.convert_value(self.value)
        
        # Create update command
        command = UpdateConfigurationCommand(
            key_name=self.key_name,
            new_value=converted_value,
            description=self.description if self.description.strip() else None
        )
        
        self.dismiss((command, True))
    
    def convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        # Try to convert to appropriate type
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
    
    def action_cancel(self) -> None:
        """Cancel the modal."""
        self.dismiss((None, False))
    
    def action_save(self) -> None:
        """Save action."""
        asyncio.create_task(self.save_variable())


class ConfigurationTable(DataTable):
    """Custom data table for configuration items."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True
    
    def setup_table(self) -> None:
        """Set up the table columns."""
        self.add_columns("Key", "Value", "Type", "Description")
    
    def populate_table(self, items: List[ConfigurationItem]) -> None:
        """Populate the table with configuration items."""
        self.clear()
        for item in items:
            value_display = str(item.value.value)
            if item.is_sensitive():
                value_display = "*" * min(len(value_display), 8)
            
            self.add_row(
                item.key.name,
                value_display,
                item.value.value_type,
                item.description or "",
                key=item.key.name
            )
    
    def get_selected_key(self) -> Optional[str]:
        """Get the key of the currently selected row."""
        if self.cursor_row >= 0:
            return self.get_row_at(self.cursor_row)[0]
        return None


class MaintenanceScreen(Screen):
    """Main maintenance screen with two-pane layout."""
    
    BINDINGS = [
        Binding("ctrl+n", "new_variable", "New Variable"),
        Binding("enter", "edit_variable", "Edit Variable"),
        Binding("delete", "delete_variable", "Delete Variable"),
        Binding("ctrl+s", "save_config", "Save Configuration"),
        Binding("ctrl+q", "quit_app", "Quit"),
        Binding("f1", "switch_env", "Switch Environment"),
    ]
    
    def __init__(
        self,
        app_service: ConfigurationApplicationService,
        config_set: ConfigurationSet
    ):
        super().__init__()
        self.app_service = app_service
        self.config_set = config_set
        self.current_environment = Environment.DEFAULT
        self.project_root = Path.cwd()
    
    def compose(self) -> ComposeResult:
        """Compose the maintenance interface."""
        with Container(id="main-container"):
            yield Header()
            
            with Horizontal(id="content-container"):
                # Left pane - Configuration table
                with Vertical(id="left-pane"):
                    with Horizontal(id="env-selector-container"):
                        yield Label("Environment:")
                        yield Select(
                            [(env.value.title(), env) for env in Environment],
                            value=self.current_environment,
                            id="env-select"
                        )
                    
                    yield Label("Configuration Variables", id="table-title")
                    yield ConfigurationTable(id="config-table")
                
                # Right pane - Live preview
                with Vertical(id="right-pane"):
                    yield Label("Configuration Preview", id="preview-title")
                    yield TextArea(
                        "",
                        read_only=True,
                        id="config-preview",
                        language="toml"
                    )
            
            yield Static("", id="status-bar")
            yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        self.setup_table()
        self.refresh_display()
    
    def setup_table(self) -> None:
        """Set up the configuration table."""
        table = self.query_one("#config-table", ConfigurationTable)
        table.setup_table()
    
    def refresh_display(self) -> None:
        """Refresh the table and preview display."""
        items = self.config_set.get_items_by_environment(self.current_environment)
        
        # Update table
        table = self.query_one("#config-table", ConfigurationTable)
        table.populate_table(items)
        
        # Update preview
        self.update_preview()
    
    def update_preview(self) -> None:
        """Update the configuration preview."""
        preview_data = {}
        items = self.config_set.get_items_by_environment(self.current_environment)
        
        for item in items:
            preview_data[item.key.name] = item.value.value
        
        # Format based on configuration format
        if self.config_set.format == ConfigurationFormat.JSON:
            preview_text = json.dumps(preview_data, indent=2)
            language = "json"
        else:
            # Default to TOML-like format for preview
            preview_text = "\n".join([
                f"{key} = {repr(value)}" for key, value in preview_data.items()
            ])
            language = "toml"
        
        preview = self.query_one("#config-preview", TextArea)
        preview.text = preview_text
        preview.language = language
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle environment selection changes."""
        if event.select.id == "env-select":
            self.current_environment = event.value
            self.refresh_display()
    
    async def action_new_variable(self) -> None:
        """Create a new configuration variable."""
        result = await self.push_screen_wait(VariableModal())
        if result and result[1]:  # If saved
            command = result[0]
            try:
                await self.app_service.update_configuration_item(command, self.config_set)
                self.refresh_display()
                self.update_status("Variable created successfully", "success")
            except Exception as e:
                self.update_status(f"Error creating variable: {e}", "error")
    
    async def action_edit_variable(self) -> None:
        """Edit the selected configuration variable."""
        table = self.query_one("#config-table", ConfigurationTable)
        selected_key = table.get_selected_key()
        
        if not selected_key:
            self.update_status("No variable selected", "warning")
            return
        
        item = self.config_set.get_item(selected_key)
        if not item:
            self.update_status("Variable not found", "error")
            return
        
        result = await self.push_screen_wait(VariableModal(item))
        if result and result[1]:  # If saved
            command = result[0]
            try:
                await self.app_service.update_configuration_item(command, self.config_set)
                self.refresh_display()
                self.update_status("Variable updated successfully", "success")
            except Exception as e:
                self.update_status(f"Error updating variable: {e}", "error")
    
    async def action_delete_variable(self) -> None:
        """Delete the selected configuration variable."""
        table = self.query_one("#config-table", ConfigurationTable)
        selected_key = table.get_selected_key()
        
        if not selected_key:
            self.update_status("No variable selected", "warning")
            return
        
        # Confirm deletion
        if await self.confirm_deletion(selected_key):
            command = DeleteConfigurationCommand(key_name=selected_key)
            try:
                await self.app_service.delete_configuration_item(command, self.config_set)
                self.refresh_display()
                self.update_status("Variable deleted successfully", "success")
            except Exception as e:
                self.update_status(f"Error deleting variable: {e}", "error")
    
    async def confirm_deletion(self, key_name: str) -> bool:
        """Confirm variable deletion."""
        # Simple confirmation - in a real implementation, you'd use a proper modal
        return True  # For now, always confirm
    
    @work(exclusive=True)
    async def action_save_config(self) -> None:
        """Save the configuration to disk."""
        try:
            success = await self.app_service.save_configuration(self.config_set, self.project_root)
            if success:
                self.update_status("Configuration saved successfully", "success")
            else:
                self.update_status("Failed to save configuration", "error")
        except Exception as e:
            self.update_status(f"Error saving configuration: {e}", "error")
    
    def action_switch_env(self) -> None:
        """Switch environment focus."""
        env_select = self.query_one("#env-select", Select)
        env_select.focus()
    
    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def update_status(self, message: str, status_type: str = "info") -> None:
        """Update the status bar."""
        status_bar = self.query_one("#status-bar", Static)
        
        color_map = {
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "blue"
        }
        
        color = color_map.get(status_type, "white")
        status_bar.update(f"[{color}]{message}[/{color}]")


class ConfigApp(App):
    """Main configuration management application."""
    
    CSS = """
    #wizard-container {
        align: center middle;
        width: 60;
        height: 20;
        background: $surface;
        border: thick $primary;
    }
    
    #wizard-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1;
    }
    
    #wizard-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    
    #wizard-form {
        padding: 1;
    }
    
    #wizard-buttons {
        align: center middle;
        margin-top: 1;
    }
    
    #main-container {
        height: 100%;
    }
    
    #content-container {
        height: 1fr;
    }
    
    #left-pane {
        width: 1fr;
        border-right: solid $primary;
        padding: 1;
    }
    
    #right-pane {
        width: 1fr;
        padding: 1;
    }
    
    #env-selector-container {
        margin-bottom: 1;
    }
    
    #table-title, #preview-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #config-table {
        height: 1fr;
    }
    
    #config-preview {
        height: 1fr;
        border: solid $primary;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    
    #modal-container {
        align: center middle;
        width: 50;
        height: 15;
        background: $surface;
        border: thick $primary;
    }
    
    #modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin: 1;
    }
    
    #modal-form {
        padding: 1;
    }
    
    #modal-buttons {
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.title = "FastAPI Configuration Manager"
        self.sub_title = "Hexagonal Architecture"
        
        # Initialize dependencies following hexagonal architecture
        self.repository = DynaconfConfigurationRepository()
        self.validator = ConfigurationValidator()
        self.app_service = ConfigurationApplicationService(self.repository, self.validator)
        
        self.config_set: Optional[ConfigurationSet] = None
        self.project_root = Path.cwd()
    
    async def on_mount(self) -> None:
        """Initialize the application."""
        # Try to load existing configuration
        existing_config = await self.app_service.load_existing_configuration(self.project_root)
        
        if existing_config:
            # Configuration exists, go to maintenance mode
            self.config_set = existing_config
            await self.push_screen(MaintenanceScreen(self.app_service, self.config_set))
        else:
            # No configuration exists, start wizard
            result = await self.push_screen_wait(ConfigurationWizard(self.app_service))
            if result:
                self.config_set = result
                await self.push_screen(MaintenanceScreen(self.app_service, self.config_set))
            else:
                self.exit()


# ============================================================================
# APPLICATION FACTORY AND DEPENDENCY INJECTION
# ============================================================================

class ApplicationFactory:
    """Factory for creating the application with proper dependency injection."""
    
    @staticmethod
    def create_app() -> ConfigApp:
        """Create the application with all dependencies wired."""
        return ConfigApp()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Main entry point for the configuration management tool."""
    try:
        app = ApplicationFactory.create_app()
        app.run()
    except KeyboardInterrupt:
        print("\nConfiguration tool interrupted by user.")
    except Exception as e:
        print(f"Error running configuration tool: {e}")


if __name__ == "__main__":
    main()
