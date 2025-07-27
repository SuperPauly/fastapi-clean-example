# FastAPI Configuration Management Tool

A terminal-friendly configuration management tool built with **Dynaconf 3.2.11** and **Textual 5.0.1**, following hexagonal architecture principles. This tool provides both initial project setup (wizard mode) and ongoing configuration maintenance capabilities.

## 🏗️ Architecture

The tool follows **hexagonal architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                 Presentation Layer (UI)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Textual   │  │   Wizard    │  │   Maintenance       │ │
│  │   Widgets   │  │   Screen    │  │   Screen            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Use Cases  │  │  Commands   │  │   App Services      │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Config Set  │  │ Config Item │  │   Value Objects     │ │
│  │ (Aggregate) │  │  (Entity)   │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Dynaconf   │  │ File System │  │    Validation       │ │
│  │  Repository │  │   Adapter   │  │    Service          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Installation

### Option 1: Using pipx (Recommended)

```bash
# Install dependencies first
pip install textual==5.0.1 dynaconf==3.2.11 tomli-w

# Run directly with pipx
pipx run manage_config.py
```

### Option 2: Manual Installation

```bash
# Clone or download the script
wget https://raw.githubusercontent.com/your-repo/manage_config.py

# Install dependencies
pip install textual==5.0.1 dynaconf==3.2.11 tomli-w

# Make executable and run
chmod +x manage_config.py
python manage_config.py
```

### Option 3: Development Setup

```bash
# For development with the FastAPI template
git clone <your-fastapi-template-repo>
cd <your-fastapi-template-repo>

# Install dependencies
hatch add textual==5.0.1 dynaconf==3.2.11 tomli-w

# Run the configuration tool
python manage_config.py
```

## 📋 Features

### 🧙‍♂️ **Configuration Wizard (First Run)**
- **Project Setup**: Enter project name and basic settings
- **Format Selection**: Choose from TOML, YAML, JSON, INI, or Python formats
- **Secrets Management**: Option to create `.secrets` file for sensitive data
- **Default Configuration**: Automatically generates common settings

### 🔧 **Maintenance Mode (Ongoing Management)**
- **Two-Pane Layout**: Configuration table on left, live preview on right
- **Environment Switching**: Toggle between default, development, testing, production
- **CRUD Operations**: Full create, read, update, delete functionality
- **Live Preview**: Real-time preview of configuration file changes
- **Backup System**: Automatic backup creation before saving

## ⌨️ Keyboard Shortcuts

### Global Shortcuts
- `Ctrl+Q` - Quit application
- `Escape` - Cancel current operation
- `Ctrl+C` - Cancel/Interrupt

### Maintenance Mode
- `Ctrl+N` - Create new configuration variable
- `Enter` - Edit selected variable
- `Delete` - Delete selected variable
- `Ctrl+S` - Save configuration to disk
- `F1` - Switch environment focus

### Modal Dialogs
- `Ctrl+S` - Save changes
- `Escape` - Cancel without saving

## 🎯 Usage Examples

### Initial Project Setup

1. **Run the tool** in your project directory:
   ```bash
   python manage_config.py
   ```

2. **Complete the wizard**:
   - Enter your project name (e.g., "MyFastAPIProject")
   - Select configuration format (TOML recommended)
   - Choose whether to create `.secrets` file
   - Click "Create Configuration"

3. **Generated files**:
   ```
   settings.toml          # Main configuration
   .secrets              # Sensitive data (if enabled)
   settings.toml.bak     # Backup (when saving)
   ```

### Managing Configuration

1. **Navigate environments** using the dropdown or `F1`
2. **Add variables** with `Ctrl+N`:
   - Key: `DATABASE_URL`
   - Value: `postgresql://localhost:5432/mydb`
   - Description: `Database connection string`

3. **Edit existing variables** by selecting and pressing `Enter`
4. **Save changes** with `Ctrl+S` (creates backup automatically)

### Supported Configuration Formats

#### TOML (Recommended)
```toml
PROJECT_NAME = "MyFastAPIProject"
DEBUG = true
DATABASE_URL = "postgresql://localhost:5432/mydb"
SECRET_KEY = "your-secret-key-here"
```

#### JSON
```json
{
  "PROJECT_NAME": "MyFastAPIProject",
  "DEBUG": true,
  "DATABASE_URL": "postgresql://localhost:5432/mydb",
  "SECRET_KEY": "your-secret-key-here"
}
```

#### YAML
```yaml
PROJECT_NAME: MyFastAPIProject
DEBUG: true
DATABASE_URL: postgresql://localhost:5432/mydb
SECRET_KEY: your-secret-key-here
```

## 🔒 Security Features

### Sensitive Data Detection
The tool automatically detects sensitive configuration keys containing:
- `password`
- `secret`
- `key`
- `token`
- `credential`

### Secrets File Management
When enabled, sensitive variables are:
- Masked in the UI display (`********`)
- Optionally written to `.secrets` file
- Excluded from main configuration file

### Backup System
- Automatic backup creation before any save operation
- Backup files use `.bak` extension
- Preserves previous configuration state

## 🛠️ Development

### Architecture Principles

The tool follows **hexagonal architecture** (ports and adapters) principles:

1. **Domain Layer**: Pure business logic with no external dependencies
   - `ConfigurationSet` (aggregate root)
   - `ConfigurationItem` (entity)
   - `ConfigurationKey`, `ConfigurationValue` (value objects)

2. **Application Layer**: Use cases and application services
   - `CreateConfigurationUseCase`
   - `UpdateConfigurationUseCase`
   - `DeleteConfigurationUseCase`
   - `ConfigurationApplicationService`

3. **Infrastructure Layer**: External adapters
   - `DynaconfConfigurationRepository` (persistence)
   - `ConfigurationValidator` (validation)
   - Textual UI components (presentation)

### Adding New Features

#### New Configuration Format
```python
# 1. Add to enum
class ConfigurationFormat(Enum):
    XML = "xml"

# 2. Implement in repository
async def save_configuration(self, config_set: ConfigurationSet, project_root: Path) -> bool:
    if config_set.format == ConfigurationFormat.XML:
        # Add XML serialization logic
        pass
```

#### New Validation Rule
```python
# Add to ConfigurationValidator
def validate_value(self, value: Any, value_type: str) -> List[str]:
    errors = []
    
    # Add custom validation
    if value_type == "email" and "@" not in str(value):
        errors.append("Invalid email format")
    
    return errors
```

### Testing

The architecture supports easy testing through dependency injection:

```python
# Unit test example
def test_configuration_creation():
    # Test domain logic
    config_set = ConfigurationSet("TestProject", ConfigurationFormat.TOML)
    item = ConfigurationItem(
        key=ConfigurationKey("TEST_KEY"),
        value=ConfigurationValue("test_value")
    )
    config_set.add_item(item)
    
    assert len(config_set.items) == 1
    assert config_set.get_item("TEST_KEY") is not None

# Integration test with mocks
async def test_create_configuration_use_case():
    mock_repo = Mock(spec=ConfigurationRepositoryPort)
    use_case = CreateConfigurationUseCase(mock_repo)
    
    command = CreateConfigurationCommand("TestProject", ConfigurationFormat.TOML)
    result = await use_case.execute(command, Path.cwd())
    
    mock_repo.save_configuration.assert_called_once()
```

## 🐛 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Install missing dependencies
pip install textual==5.0.1 dynaconf==3.2.11 tomli-w
```

#### Permission errors when saving
```bash
# Check file permissions
ls -la settings.*
chmod 644 settings.toml
```

#### Configuration not loading
- Ensure you're in the correct project directory
- Check for existing `settings.*` files
- Verify file format is valid

### Debug Mode

Run with Python's verbose mode for detailed error information:
```bash
python -v manage_config.py
```

## 📚 Integration with FastAPI Template

This tool is designed to work seamlessly with the FastAPI Clean Architecture template:

1. **Generated Configuration** follows Dynaconf conventions
2. **Environment Support** matches FastAPI deployment patterns
3. **Secrets Management** integrates with `.env` file patterns
4. **Format Compatibility** supports all common configuration formats

### Example Integration

```python
# In your FastAPI app
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["settings.toml"],
    environments=True,
    load_dotenv=True,
)

# Use configuration
DATABASE_URL = settings.DATABASE_URL
DEBUG = settings.get("DEBUG", False)
```

## 🤝 Contributing

The tool is designed for extensibility:

1. **New UI Components**: Add to presentation layer
2. **New Use Cases**: Add to application layer
3. **New Adapters**: Add to infrastructure layer
4. **Domain Extensions**: Add to domain layer

All changes should maintain hexagonal architecture principles and include appropriate tests.

## 📄 License

This configuration tool is part of the FastAPI Clean Architecture template and follows the same license terms.
