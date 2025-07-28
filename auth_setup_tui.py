#!/usr/bin/env python3
"""
Authentication Setup TUI - Interactive Configuration Tool

This script provides a Text User Interface (TUI) for configuring authentication
settings in the FastAPI Clean Architecture Template. It allows users to:

- Configure OAuth providers (Google, GitHub, Facebook, etc.)
- Set up email verification settings
- Configure password policies
- Set up RBAC roles and permissions
- Configure rate limiting for authentication
- Generate secure secrets and keys

Usage:
    python auth_setup_tui.py
    python auth_setup_tui.py --config-file custom_settings.toml
    python auth_setup_tui.py --provider google --interactive
"""

import sys
import argparse
import secrets
import string
from pathlib import Path
from typing import Dict, Any, List, Optional
import toml

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Button, Input, Checkbox, Select, TextArea,
        Static, Label, Switch, ProgressBar, Tabs, TabPane, DataTable
    )
    from textual.screen import Screen
    from textual.binding import Binding
    from textual import events
    from textual.reactive import reactive
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    print("⚠️  Textual not available. Install with: pip install textual")


class AuthSetupConfig:
    """Configuration manager for authentication setup."""
    
    def __init__(self, config_file: str = "settings.toml"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default."""
        if self.config_file.exists():
            try:
                return toml.load(self.config_file)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default authentication configuration."""
        return {
            "authentication": {
                "enable_registration": True,
                "enable_email_verification": True,
                "enable_password_reset": True,
                "enable_social_login": True,
                "enable_rbac": True,
                "default_user_role": "user",
                "email_verification_expire_hours": 24,
                "email_verification_required": True,
                "resend_verification_cooldown_minutes": 5,
                "password_reset_expire_hours": 2,
                "password_reset_cooldown_minutes": 15,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 30,
                "enable_account_lockout": True,
                "available_roles": ["user", "moderator", "admin", "superuser"],
                "role_hierarchy": {
                    "user": 1,
                    "moderator": 2,
                    "admin": 3,
                    "superuser": 4
                }
            },
            "security": {
                "jwt_secret_key": self.generate_secret_key(),
                "session_secret_key": self.generate_secret_key(),
                "jwt_algorithm": "HS256",
                "jwt_expire_minutes": 30,
                "jwt_refresh_expire_days": 7,
                "session_expire_minutes": 60,
                "session_cookie_secure": True,
                "session_cookie_httponly": True,
                "password_min_length": 8,
                "password_require_uppercase": True,
                "password_require_lowercase": True,
                "password_require_numbers": True,
                "password_require_special": True
            },
            "oauth": {
                "redirect_url": "http://localhost:8000/auth/callback",
                "state_secret": self.generate_secret_key(),
                **{f"{provider}_enabled": False for provider in self.get_oauth_providers()},
                **{f"{provider}_client_id": f"your-{provider}-client-id" for provider in self.get_oauth_providers()},
                **{f"{provider}_client_secret": f"your-{provider}-client-secret" for provider in self.get_oauth_providers()}
            }
        }
    
    @staticmethod
    def get_oauth_providers() -> List[str]:
        """Get list of supported OAuth providers."""
        return [
            "google", "github", "facebook", "twitter", "linkedin",
            "microsoft", "steam", "twilio", "twitch", "spotify",
            "stackoverflow", "instagram", "dropbox"
        ]
    
    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """Generate cryptographically secure secret key."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                toml.dump(self.config, f)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


class OAuthProviderScreen(Screen):
    """Screen for configuring OAuth providers."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("ctrl+s", "save", "Save"),
    ]
    
    def __init__(self, config: AuthSetupConfig, provider: str):
        super().__init__()
        self.config = config
        self.provider = provider
        self.provider_config = self.get_provider_config()
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration."""
        providers_info = {
            "google": {
                "name": "Google",
                "scopes": ["openid", "email", "profile"],
                "docs_url": "https://developers.google.com/identity/protocols/oauth2",
                "fields": ["client_id", "client_secret"]
            },
            "github": {
                "name": "GitHub",
                "scopes": ["user:email"],
                "docs_url": "https://docs.github.com/en/developers/apps/building-oauth-apps",
                "fields": ["client_id", "client_secret"]
            },
            "facebook": {
                "name": "Facebook",
                "scopes": ["email", "public_profile"],
                "docs_url": "https://developers.facebook.com/docs/facebook-login",
                "fields": ["client_id", "client_secret"]
            },
            "twitter": {
                "name": "X (Twitter)",
                "scopes": ["tweet.read", "users.read"],
                "docs_url": "https://developer.twitter.com/en/docs/authentication/oauth-2-0",
                "fields": ["client_id", "client_secret"]
            },
            "linkedin": {
                "name": "LinkedIn",
                "scopes": ["r_liteprofile", "r_emailaddress"],
                "docs_url": "https://docs.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow",
                "fields": ["client_id", "client_secret"]
            },
            "microsoft": {
                "name": "Microsoft Live",
                "scopes": ["openid", "profile", "email"],
                "docs_url": "https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow",
                "fields": ["client_id", "client_secret"]
            },
            "steam": {
                "name": "Steam",
                "scopes": [],
                "docs_url": "https://steamcommunity.com/dev/apikey",
                "fields": ["api_key"]
            },
            "twitch": {
                "name": "Twitch",
                "scopes": ["user:read:email"],
                "docs_url": "https://dev.twitch.tv/docs/authentication",
                "fields": ["client_id", "client_secret"]
            },
            "spotify": {
                "name": "Spotify",
                "scopes": ["user-read-email", "user-read-private"],
                "docs_url": "https://developer.spotify.com/documentation/general/guides/authorization/",
                "fields": ["client_id", "client_secret"]
            },
            "stackoverflow": {
                "name": "StackOverflow",
                "scopes": [],
                "docs_url": "https://api.stackexchange.com/docs/authentication",
                "fields": ["client_id", "client_secret", "key"]
            },
            "instagram": {
                "name": "Instagram",
                "scopes": ["user_profile", "user_media"],
                "docs_url": "https://developers.facebook.com/docs/instagram-basic-display-api",
                "fields": ["client_id", "client_secret"]
            },
            "dropbox": {
                "name": "Dropbox",
                "scopes": ["account_info.read"],
                "docs_url": "https://developers.dropbox.com/oauth-guide",
                "fields": ["client_id", "client_secret"]
            }
        }
        return providers_info.get(self.provider, {})
    
    def compose(self) -> ComposeResult:
        """Compose the OAuth provider configuration screen."""
        provider_name = self.provider_config.get("name", self.provider.title())
        
        yield Header(show_clock=True)
        
        with ScrollableContainer():
            yield Static(f"🔐 Configure {provider_name} OAuth", classes="title")
            
            # Provider information
            yield Static(f"📚 Documentation: {self.provider_config.get('docs_url', 'N/A')}", classes="info")
            yield Static(f"🔑 Required Scopes: {', '.join(self.provider_config.get('scopes', []))}", classes="info")
            
            # Enable/disable provider
            enabled_key = f"{self.provider}_enabled"
            current_enabled = self.config.config.get("oauth", {}).get(enabled_key, False)
            yield Horizontal(
                Label("Enable Provider:", classes="label"),
                Switch(value=current_enabled, id=f"enable_{self.provider}"),
                classes="field"
            )
            
            # Configuration fields
            for field in self.provider_config.get("fields", []):
                field_key = f"{self.provider}_{field}"
                current_value = self.config.config.get("oauth", {}).get(field_key, "")
                
                yield Horizontal(
                    Label(f"{field.replace('_', ' ').title()}:", classes="label"),
                    Input(value=current_value, placeholder=f"Enter {field}", id=field_key),
                    classes="field"
                )
            
            # Action buttons
            yield Horizontal(
                Button("Save Configuration", variant="primary", id="save"),
                Button("Test Connection", variant="default", id="test"),
                Button("Back", variant="default", id="back"),
                classes="buttons"
            )
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "test":
            self.test_connection()
        elif event.button.id == "back":
            self.action_back()
    
    def action_save(self) -> None:
        """Save OAuth provider configuration."""
        # Update configuration with form values
        oauth_config = self.config.config.setdefault("oauth", {})
        
        # Update enabled status
        enable_switch = self.query_one(f"#enable_{self.provider}", Switch)
        oauth_config[f"{self.provider}_enabled"] = enable_switch.value
        
        # Update configuration fields
        for field in self.provider_config.get("fields", []):
            field_key = f"{self.provider}_{field}"
            input_widget = self.query_one(f"#{field_key}", Input)
            oauth_config[field_key] = input_widget.value
        
        # Save to file
        if self.config.save_config():
            self.notify("✅ Configuration saved successfully!")
        else:
            self.notify("❌ Failed to save configuration", severity="error")
    
    def test_connection(self) -> None:
        """Test OAuth provider connection."""
        # This would implement actual OAuth testing
        self.notify("🧪 Testing OAuth connection... (Not implemented in demo)")
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.app.pop_screen()


class AuthSetupTUI(App):
    """Main TUI application for authentication setup."""
    
    CSS = """
    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin: 1;
    }
    
    .info {
        color: $text-muted;
        margin: 1 0;
    }
    
    .field {
        height: 3;
        margin: 1 0;
    }
    
    .label {
        width: 20;
        text-align: right;
        margin-right: 2;
    }
    
    .buttons {
        height: 3;
        margin: 2 0;
        align: center;
    }
    
    .provider-grid {
        height: auto;
        margin: 1 0;
    }
    
    .provider-card {
        height: 5;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    .enabled {
        background: $success 20%;
    }
    
    .disabled {
        background: $error 20%;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+s", "save_all", "Save All"),
        Binding("ctrl+r", "reload", "Reload"),
    ]
    
    def __init__(self, config_file: str = "settings.toml"):
        super().__init__()
        self.config = AuthSetupConfig(config_file)
        self.title = "FastAPI Authentication Setup"
        self.sub_title = "Configure OAuth, RBAC, and Security Settings"
    
    def compose(self) -> ComposeResult:
        """Compose the main application."""
        yield Header(show_clock=True)
        
        with Tabs("overview", "oauth", "security", "rbac", "advanced"):
            with TabPane("Overview", id="overview"):
                yield self.create_overview_tab()
            
            with TabPane("OAuth Providers", id="oauth"):
                yield self.create_oauth_tab()
            
            with TabPane("Security", id="security"):
                yield self.create_security_tab()
            
            with TabPane("RBAC", id="rbac"):
                yield self.create_rbac_tab()
            
            with TabPane("Advanced", id="advanced"):
                yield self.create_advanced_tab()
        
        yield Footer()
    
    def create_overview_tab(self) -> ComposeResult:
        """Create overview tab content."""
        with ScrollableContainer():
            yield Static("🚀 FastAPI Authentication Setup", classes="title")
            yield Static("Configure comprehensive authentication for your FastAPI application", classes="info")
            
            # Current configuration status
            auth_config = self.config.config.get("authentication", {})
            oauth_config = self.config.config.get("oauth", {})
            
            enabled_providers = [
                provider for provider in self.config.get_oauth_providers()
                if oauth_config.get(f"{provider}_enabled", False)
            ]
            
            yield Static(f"📊 Configuration Status:", classes="info")
            yield Static(f"   • Email Verification: {'✅' if auth_config.get('enable_email_verification') else '❌'}")
            yield Static(f"   • Social Login: {'✅' if auth_config.get('enable_social_login') else '❌'}")
            yield Static(f"   • RBAC: {'✅' if auth_config.get('enable_rbac') else '❌'}")
            yield Static(f"   • Enabled OAuth Providers: {len(enabled_providers)} ({', '.join(enabled_providers)})")
            
            # Quick actions
            yield Horizontal(
                Button("Generate New Secrets", variant="primary", id="generate_secrets"),
                Button("Validate Configuration", variant="default", id="validate"),
                Button("Export Configuration", variant="default", id="export"),
                classes="buttons"
            )
    
    def create_oauth_tab(self) -> ComposeResult:
        """Create OAuth providers tab content."""
        with ScrollableContainer():
            yield Static("🔐 OAuth Provider Configuration", classes="title")
            
            # OAuth providers grid
            oauth_config = self.config.config.get("oauth", {})
            
            for provider in self.config.get_oauth_providers():
                enabled = oauth_config.get(f"{provider}_enabled", False)
                status_class = "enabled" if enabled else "disabled"
                status_text = "✅ Enabled" if enabled else "❌ Disabled"
                
                with Container(classes=f"provider-card {status_class}"):
                    yield Horizontal(
                        Static(f"🔑 {provider.title()}", classes="provider-name"),
                        Static(status_text, classes="provider-status"),
                        Button("Configure", id=f"config_{provider}", variant="primary" if not enabled else "default"),
                    )
    
    def create_security_tab(self) -> ComposeResult:
        """Create security settings tab content."""
        with ScrollableContainer():
            yield Static("🔒 Security Configuration", classes="title")
            
            security_config = self.config.config.get("security", {})
            
            # JWT Settings
            yield Static("JWT Token Settings:", classes="info")
            yield Horizontal(
                Label("JWT Secret Key:", classes="label"),
                Input(value=security_config.get("jwt_secret_key", ""), password=True, id="jwt_secret"),
                Button("Generate", id="gen_jwt_secret"),
                classes="field"
            )
            
            yield Horizontal(
                Label("JWT Expire (minutes):", classes="label"),
                Input(value=str(security_config.get("jwt_expire_minutes", 30)), id="jwt_expire"),
                classes="field"
            )
            
            # Password Policy
            yield Static("Password Policy:", classes="info")
            yield Horizontal(
                Label("Minimum Length:", classes="label"),
                Input(value=str(security_config.get("password_min_length", 8)), id="password_min_length"),
                classes="field"
            )
            
            yield Horizontal(
                Label("Require Uppercase:", classes="label"),
                Switch(value=security_config.get("password_require_uppercase", True), id="require_uppercase"),
                classes="field"
            )
            
            yield Horizontal(
                Label("Require Numbers:", classes="label"),
                Switch(value=security_config.get("password_require_numbers", True), id="require_numbers"),
                classes="field"
            )
    
    def create_rbac_tab(self) -> ComposeResult:
        """Create RBAC settings tab content."""
        with ScrollableContainer():
            yield Static("👥 Role-Based Access Control", classes="title")
            
            auth_config = self.config.config.get("authentication", {})
            
            # RBAC Enable/Disable
            yield Horizontal(
                Label("Enable RBAC:", classes="label"),
                Switch(value=auth_config.get("enable_rbac", True), id="enable_rbac"),
                classes="field"
            )
            
            # Default Role
            yield Horizontal(
                Label("Default User Role:", classes="label"),
                Select(
                    options=[(role, role) for role in auth_config.get("available_roles", ["user"])],
                    value=auth_config.get("default_user_role", "user"),
                    id="default_role"
                ),
                classes="field"
            )
            
            # Role Hierarchy Table
            yield Static("Role Hierarchy:", classes="info")
            role_table = DataTable()
            role_table.add_columns("Role", "Level", "Description")
            
            role_hierarchy = auth_config.get("role_hierarchy", {})
            for role, level in role_hierarchy.items():
                role_table.add_row(role, str(level), f"Level {level} access")
            
            yield role_table
    
    def create_advanced_tab(self) -> ComposeResult:
        """Create advanced settings tab content."""
        with ScrollableContainer():
            yield Static("⚙️ Advanced Configuration", classes="title")
            
            auth_config = self.config.config.get("authentication", {})
            
            # Account Lockout Settings
            yield Static("Account Lockout:", classes="info")
            yield Horizontal(
                Label("Max Login Attempts:", classes="label"),
                Input(value=str(auth_config.get("max_login_attempts", 5)), id="max_attempts"),
                classes="field"
            )
            
            yield Horizontal(
                Label("Lockout Duration (min):", classes="label"),
                Input(value=str(auth_config.get("lockout_duration_minutes", 30)), id="lockout_duration"),
                classes="field"
            )
            
            # Email Verification Settings
            yield Static("Email Verification:", classes="info")
            yield Horizontal(
                Label("Verification Required:", classes="label"),
                Switch(value=auth_config.get("email_verification_required", True), id="verification_required"),
                classes="field"
            )
            
            yield Horizontal(
                Label("Verification Expire (hours):", classes="label"),
                Input(value=str(auth_config.get("email_verification_expire_hours", 24)), id="verification_expire"),
                classes="field"
            )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "generate_secrets":
            self.generate_new_secrets()
        elif button_id == "validate":
            self.validate_configuration()
        elif button_id == "export":
            self.export_configuration()
        elif button_id.startswith("config_"):
            provider = button_id.replace("config_", "")
            self.push_screen(OAuthProviderScreen(self.config, provider))
        elif button_id.startswith("gen_"):
            self.generate_secret_for_field(button_id)
    
    def generate_new_secrets(self) -> None:
        """Generate new secret keys."""
        security_config = self.config.config.setdefault("security", {})
        oauth_config = self.config.config.setdefault("oauth", {})
        
        security_config["jwt_secret_key"] = self.config.generate_secret_key()
        security_config["session_secret_key"] = self.config.generate_secret_key()
        oauth_config["state_secret"] = self.config.generate_secret_key()
        
        if self.config.save_config():
            self.notify("✅ New secrets generated and saved!")
        else:
            self.notify("❌ Failed to save new secrets", severity="error")
    
    def generate_secret_for_field(self, button_id: str) -> None:
        """Generate secret for specific field."""
        field_map = {
            "gen_jwt_secret": "jwt_secret"
        }
        
        field_id = field_map.get(button_id)
        if field_id:
            new_secret = self.config.generate_secret_key()
            input_widget = self.query_one(f"#{field_id}", Input)
            input_widget.value = new_secret
            self.notify(f"✅ New secret generated for {field_id}")
    
    def validate_configuration(self) -> None:
        """Validate current configuration."""
        # This would implement configuration validation
        self.notify("🔍 Configuration validation... (Not implemented in demo)")
    
    def export_configuration(self) -> None:
        """Export configuration to file."""
        if self.config.save_config():
            self.notify(f"✅ Configuration exported to {self.config.config_file}")
        else:
            self.notify("❌ Failed to export configuration", severity="error")
    
    def action_save_all(self) -> None:
        """Save all configuration changes."""
        if self.config.save_config():
            self.notify("✅ All changes saved successfully!")
        else:
            self.notify("❌ Failed to save changes", severity="error")
    
    def action_reload(self) -> None:
        """Reload configuration from file."""
        self.config = AuthSetupConfig(str(self.config.config_file))
        self.notify("🔄 Configuration reloaded")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="FastAPI Authentication Setup TUI")
    parser.add_argument(
        "--config-file",
        default="settings.toml",
        help="Configuration file path (default: settings.toml)"
    )
    parser.add_argument(
        "--provider",
        choices=AuthSetupConfig.get_oauth_providers(),
        help="Configure specific OAuth provider"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive TUI"
    )
    parser.add_argument(
        "--generate-secrets",
        action="store_true",
        help="Generate new secret keys"
    )
    
    args = parser.parse_args()
    
    if not TEXTUAL_AVAILABLE and (args.interactive or not any([args.generate_secrets, args.provider])):
        print("❌ Textual is required for interactive mode. Install with: pip install textual")
        print("💡 You can still use CLI options like --generate-secrets")
        sys.exit(1)
    
    config = AuthSetupConfig(args.config_file)
    
    if args.generate_secrets:
        # Generate secrets via CLI
        security_config = config.config.setdefault("security", {})
        oauth_config = config.config.setdefault("oauth", {})
        
        security_config["jwt_secret_key"] = config.generate_secret_key()
        security_config["session_secret_key"] = config.generate_secret_key()
        oauth_config["state_secret"] = config.generate_secret_key()
        
        if config.save_config():
            print("✅ New secrets generated and saved!")
        else:
            print("❌ Failed to save new secrets")
        return
    
    if args.provider and not args.interactive:
        # Configure provider via CLI
        print(f"🔐 Configuring {args.provider} OAuth provider...")
        print("Use --interactive flag for TUI configuration")
        return
    
    # Launch TUI
    if TEXTUAL_AVAILABLE:
        app = AuthSetupTUI(args.config_file)
        app.run()
    else:
        print("❌ TUI not available. Use CLI options instead.")


if __name__ == "__main__":
    main()
