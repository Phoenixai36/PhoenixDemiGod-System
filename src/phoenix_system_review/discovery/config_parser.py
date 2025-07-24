"""
Configuration Parser for Phoenix Hydra System Review Tool

Provides parsing capabilities for YAML, JSON, TOML, and other configuration formats
with validation and schema checking.
"""

import json
import yaml
import configparser

# Try to import TOML parser
toml = None
try:
    import tomli as toml
    import tomli_w
    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from ..models.data_models import Issue, Priority


@dataclass
class ConfigurationData:
    """Represents parsed configuration data with metadata"""
    file_path: str
    format_type: str
    data: Dict[str, Any]
    schema_valid: bool = True
    validation_errors: List[str] = None
    parsing_errors: List[str] = None
    last_modified: Optional[datetime] = None
    file_size: int = 0
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
        if self.parsing_errors is None:
            self.parsing_errors = []


class ConfigurationParser:
    """
    Multi-format configuration parser with validation and schema checking.
    
    Supports YAML, JSON, TOML, INI, and environment file parsing with
    error handling for malformed files and basic schema validation.
    """
    
    # Supported file extensions and their parsers
    SUPPORTED_FORMATS = {
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        '.env': 'env',
        '.properties': 'properties'
    }
    
    # Phoenix Hydra specific configuration schemas
    PHOENIX_SCHEMAS = {
        'pyproject.toml': {
            'required_sections': ['tool.pytest', 'project'],
            'optional_sections': ['build-system', 'tool.black', 'tool.ruff']
        },
        'docker-compose.yml': {
            'required_sections': ['services'],
            'optional_sections': ['networks', 'volumes', 'secrets']
        },
        'package.json': {
            'required_fields': ['name', 'version'],
            'optional_fields': ['scripts', 'dependencies', 'devDependencies']
        },
        'terraform': {
            'required_blocks': ['resource', 'provider'],
            'optional_blocks': ['variable', 'output', 'data', 'locals']
        }
    }
    
    def __init__(self):
        """Initialize the configuration parser"""
        self.parsed_configs: Dict[str, ConfigurationData] = {}
        self.parsing_errors: List[Issue] = []
    
    def parse_configurations(self, config_files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Parse multiple configuration files and return structured data.
        
        Args:
            config_files: List of configuration file paths to parse
            
        Returns:
            Dictionary mapping file paths to parsed configuration data
        """
        results = {}
        
        for file_path in config_files:
            try:
                config_data = self.parse_single_file(file_path)
                if config_data:
                    results[file_path] = config_data.data
                    self.parsed_configs[file_path] = config_data
                else:
                    # File doesn't exist or couldn't be parsed
                    results[file_path] = {}
            except Exception as e:
                self._add_parsing_error(file_path, f"Failed to parse file: {str(e)}")
                results[file_path] = {}
        
        return results
    
    def parse_single_file(self, file_path: str) -> Optional[ConfigurationData]:
        """
        Parse a single configuration file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            ConfigurationData object with parsed content and metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            self._add_parsing_error(file_path, "File does not exist")
            return None
        
        if not path.is_file():
            self._add_parsing_error(file_path, "Path is not a file")
            return None
        
        # Determine file format
        format_type = self._determine_format(path)
        if not format_type:
            self._add_parsing_error(file_path, f"Unsupported file format: {path.suffix}")
            return None
        
        # Get file metadata
        stat = path.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        file_size = stat.st_size
        
        # Parse the file
        try:
            data = self._parse_by_format(path, format_type)
            
            # Create configuration data object
            config_data = ConfigurationData(
                file_path=file_path,
                format_type=format_type,
                data=data,
                last_modified=last_modified,
                file_size=file_size
            )
            
            # Validate configuration
            self._validate_configuration(config_data)
            
            # Store the parsed configuration
            self.parsed_configs[file_path] = config_data
            
            return config_data
            
        except Exception as e:
            self._add_parsing_error(file_path, f"Parsing error: {str(e)}")
            return ConfigurationData(
                file_path=file_path,
                format_type=format_type,
                data={},
                schema_valid=False,
                parsing_errors=[str(e)],
                last_modified=last_modified,
                file_size=file_size
            )
    
    def _determine_format(self, file_path: Path) -> Optional[str]:
        """
        Determine the configuration format based on file extension and content.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Format type string or None if unsupported
        """
        # Check by extension first
        extension = file_path.suffix.lower()
        if extension in self.SUPPORTED_FORMATS:
            return self.SUPPORTED_FORMATS[extension]
        
        # Special cases based on filename
        name = file_path.name.lower()
        if name in ['dockerfile', 'dockerfile.dev', 'dockerfile.prod']:
            return 'dockerfile'
        elif name.startswith('.env'):
            return 'env'
        elif 'compose' in name and (name.endswith('.yml') or name.endswith('.yaml')):
            return 'yaml'
        
        return None
    
    def _parse_by_format(self, file_path: Path, format_type: str) -> Dict[str, Any]:
        """
        Parse file content based on its format type.
        
        Args:
            file_path: Path to the file
            format_type: Type of format to parse
            
        Returns:
            Parsed data as dictionary
        """
        content = file_path.read_text(encoding='utf-8')
        
        if format_type == 'yaml':
            return self._parse_yaml(content)
        elif format_type == 'json':
            return self._parse_json(content)
        elif format_type == 'toml':
            return self._parse_toml(content)
        elif format_type == 'ini':
            return self._parse_ini(content)
        elif format_type == 'env':
            return self._parse_env(content)
        elif format_type == 'properties':
            return self._parse_properties(content)
        elif format_type == 'dockerfile':
            return self._parse_dockerfile(content)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML content"""
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {str(e)}")
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON content"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
    
    def _parse_toml(self, content: str) -> Dict[str, Any]:
        """Parse TOML content"""
        if not TOML_AVAILABLE or toml is None:
            # For testing purposes, provide a basic TOML parser
            return self._basic_toml_parse(content)
        try:
            if hasattr(toml, 'loads'):
                return toml.loads(content)
            else:
                # Fallback for older toml versions
                import io
                return toml.load(io.StringIO(content))
        except Exception as e:
            raise ValueError(f"Invalid TOML: {str(e)}")
    
    def _basic_toml_parse(self, content: str) -> Dict[str, Any]:
        """Basic TOML parser for testing when tomli is not available"""
        result = {}
        current_section = result
        section_stack = []
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Handle sections
            if line.startswith('[') and line.endswith(']'):
                section_name = line[1:-1]
                if '.' in section_name:
                    # Nested section
                    parts = section_name.split('.')
                    current_section = result
                    for part in parts:
                        if part not in current_section:
                            current_section[part] = {}
                        current_section = current_section[part]
                else:
                    # Top-level section
                    if section_name not in result:
                        result[section_name] = {}
                    current_section = result[section_name]
                continue
            
            # Handle key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Basic value parsing
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                elif value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.startswith('[') and value.endswith(']'):
                    # Basic array parsing
                    array_content = value[1:-1].strip()
                    if array_content:
                        value = [item.strip().strip('"\'') for item in array_content.split(',')]
                    else:
                        value = []
                else:
                    # Try to parse as number
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Keep as string
                
                current_section[key] = value
        
        return result
    
    def _parse_ini(self, content: str) -> Dict[str, Any]:
        """Parse INI/CFG content"""
        try:
            parser = configparser.ConfigParser()
            parser.read_string(content)
            
            # Convert to nested dictionary
            result = {}
            for section_name in parser.sections():
                result[section_name] = dict(parser[section_name])
            
            return result
        except configparser.Error as e:
            raise ValueError(f"Invalid INI/CFG: {str(e)}")
    
    def _parse_env(self, content: str) -> Dict[str, Any]:
        """Parse environment file content"""
        result = {}
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                result[key] = value
            else:
                # Invalid line format
                result[f'_invalid_line_{line_num}'] = line
        
        return result
    
    def _parse_properties(self, content: str) -> Dict[str, Any]:
        """Parse Java properties file content"""
        result = {}
        
        for line in content.splitlines():
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            
            # Parse key=value or key:value format
            if '=' in line:
                key, value = line.split('=', 1)
            elif ':' in line:
                key, value = line.split(':', 1)
            else:
                continue
            
            result[key.strip()] = value.strip()
        
        return result
    
    def _parse_dockerfile(self, content: str) -> Dict[str, Any]:
        """Parse Dockerfile content into structured data"""
        result = {
            'instructions': [],
            'from_image': None,
            'exposed_ports': [],
            'volumes': [],
            'environment': {},
            'labels': {}
        }
        
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse instruction
            parts = line.split(None, 1)
            if len(parts) < 1:
                continue
            
            instruction = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""
            
            result['instructions'].append({
                'line': line_num,
                'instruction': instruction,
                'args': args
            })
            
            # Extract specific information
            if instruction == 'FROM':
                result['from_image'] = args
            elif instruction == 'EXPOSE':
                result['exposed_ports'].extend(args.split())
            elif instruction == 'VOLUME':
                result['volumes'].append(args.strip('[]"\''))
            elif instruction == 'ENV':
                if '=' in args:
                    key, value = args.split('=', 1)
                    result['environment'][key.strip()] = value.strip()
            elif instruction == 'LABEL':
                if '=' in args:
                    key, value = args.split('=', 1)
                    result['labels'][key.strip()] = value.strip()
        
        return result
    
    def _validate_configuration(self, config_data: ConfigurationData) -> None:
        """
        Validate configuration against Phoenix Hydra specific schemas.
        
        Args:
            config_data: Configuration data to validate
        """
        file_name = Path(config_data.file_path).name.lower()
        
        # Check for Phoenix-specific validation rules
        if file_name == 'pyproject.toml' or (config_data.format_type == 'toml' and ('pyproject' in file_name or 'project' in config_data.data)):
            self._validate_pyproject(config_data)
        elif 'compose' in file_name:
            self._validate_docker_compose(config_data)
        elif file_name == 'package.json' or (config_data.format_type == 'json' and 'package' in file_name):
            self._validate_package_json(config_data)
        elif config_data.format_type == 'dockerfile':
            self._validate_dockerfile(config_data)
        elif file_name.endswith('.tf'):
            self._validate_terraform(config_data)
        
        # General validation
        self._validate_general_structure(config_data)
    
    def _validate_pyproject(self, config_data: ConfigurationData) -> None:
        """Validate pyproject.toml structure"""
        data = config_data.data
        
        # Check for required sections
        if 'project' not in data and 'tool' not in data:
            config_data.validation_errors.append("Missing required 'project' or 'tool' section")
            config_data.schema_valid = False
        
        # For Phoenix Hydra, we expect certain tools to be configured
        if 'tool' not in data:
            config_data.validation_errors.append("Missing 'tool' section with Phoenix development tools")
        else:
            tools = data['tool']
            if 'pytest' not in tools:
                config_data.validation_errors.append("Missing pytest configuration")
            
            # Check for code quality tools
            quality_tools = ['black', 'ruff', 'mypy']
            missing_tools = [tool for tool in quality_tools if tool not in tools]
            if missing_tools:
                config_data.validation_errors.append(f"Missing code quality tools: {', '.join(missing_tools)}")
    
    def _validate_docker_compose(self, config_data: ConfigurationData) -> None:
        """Validate docker-compose.yml structure"""
        data = config_data.data
        
        if 'services' not in data:
            config_data.validation_errors.append("Missing required 'services' section")
            config_data.schema_valid = False
            return
        
        services = data['services']
        
        # Check for Phoenix Hydra services
        expected_services = ['phoenix-core', 'n8n-phoenix', 'windmill', 'postgres', 'minio']
        missing_services = []
        
        for service in expected_services:
            if not any(service in svc_name for svc_name in services.keys()):
                missing_services.append(service)
        
        if missing_services:
            config_data.validation_errors.append(f"Missing expected services: {', '.join(missing_services)}")
        
        # Validate service configurations
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                config_data.validation_errors.append(f"Invalid service configuration for {service_name}")
                continue
            
            # Check for health checks
            if 'healthcheck' not in service_config:
                config_data.validation_errors.append(f"Missing health check for service {service_name}")
    
    def _validate_package_json(self, config_data: ConfigurationData) -> None:
        """Validate package.json structure"""
        data = config_data.data
        
        required_fields = ['name', 'version']
        for field in required_fields:
            if field not in data:
                config_data.validation_errors.append(f"Missing required field: {field}")
                config_data.schema_valid = False
        
        # Check for scripts section
        if 'scripts' not in data:
            config_data.validation_errors.append("Missing 'scripts' section")
        else:
            scripts = data['scripts']
            expected_scripts = ['test', 'build', 'start']
            missing_scripts = [script for script in expected_scripts if script not in scripts]
            if missing_scripts:
                config_data.validation_errors.append(f"Missing recommended scripts: {', '.join(missing_scripts)}")
    
    def _validate_dockerfile(self, config_data: ConfigurationData) -> None:
        """Validate Dockerfile structure"""
        data = config_data.data
        
        if not data.get('from_image'):
            config_data.validation_errors.append("Missing FROM instruction")
            config_data.schema_valid = False
        
        # Check for security best practices
        instructions = [inst['instruction'] for inst in data.get('instructions', [])]
        
        if 'USER' not in instructions:
            config_data.validation_errors.append("Missing USER instruction (security best practice)")
        
        if 'HEALTHCHECK' not in instructions:
            config_data.validation_errors.append("Missing HEALTHCHECK instruction")
        
        # Check for exposed ports
        if not data.get('exposed_ports'):
            config_data.validation_errors.append("No ports exposed")
    
    def _validate_terraform(self, config_data: ConfigurationData) -> None:
        """Validate Terraform configuration structure"""
        data = config_data.data
        
        # Check for required blocks (this is a simplified validation)
        if not any(key.startswith('resource') for key in data.keys()):
            config_data.validation_errors.append("No resource blocks found")
        
        if not any(key.startswith('provider') for key in data.keys()):
            config_data.validation_errors.append("No provider blocks found")
    
    def _validate_general_structure(self, config_data: ConfigurationData) -> None:
        """Perform general validation checks"""
        data = config_data.data
        
        # Check for empty configuration
        if not data:
            config_data.validation_errors.append("Configuration file is empty")
            config_data.schema_valid = False
        
        # Check for very large configurations (potential issue)
        if config_data.file_size > 1024 * 1024:  # 1MB
            config_data.validation_errors.append("Configuration file is very large (>1MB)")
        
        # Check for sensitive data patterns
        sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'["\']?.*key["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'["\']?.*password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'["\']?.*secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            r'["\']?.*token["\']?\s*[:=]\s*["\']?[^"\'\s]+'
        ]
        
        content_str = str(data).lower()
        for pattern in sensitive_patterns:
            if re.search(pattern, content_str):
                config_data.validation_errors.append("Potential sensitive data found in configuration")
                break
    
    def _add_parsing_error(self, file_path: str, message: str) -> None:
        """Add a parsing error to the error list"""
        error = Issue(
            severity=Priority.HIGH,
            description=message,
            component="configuration_parser",
            file_path=file_path
        )
        self.parsing_errors.append(error)
    
    def get_parsed_config(self, file_path: str) -> Optional[ConfigurationData]:
        """
        Get parsed configuration data for a specific file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            ConfigurationData object or None if not found
        """
        return self.parsed_configs.get(file_path)
    
    def get_all_parsed_configs(self) -> Dict[str, ConfigurationData]:
        """
        Get all parsed configuration data.
        
        Returns:
            Dictionary mapping file paths to ConfigurationData objects
        """
        return self.parsed_configs.copy()
    
    def get_parsing_errors(self) -> List[Issue]:
        """
        Get all parsing errors encountered.
        
        Returns:
            List of Issue objects representing parsing errors
        """
        return self.parsing_errors.copy()
    
    def validate_configuration_files(self, config_files: List[str]) -> List[str]:
        """
        Validate multiple configuration files and return list of issues.
        
        Args:
            config_files: List of configuration file paths
            
        Returns:
            List of validation issue descriptions
        """
        issues = []
        
        for file_path in config_files:
            config_data = self.parse_single_file(file_path)
            if config_data:
                if not config_data.schema_valid:
                    issues.extend([f"{file_path}: {error}" for error in config_data.validation_errors])
                if config_data.parsing_errors:
                    issues.extend([f"{file_path}: {error}" for error in config_data.parsing_errors])
        
        # Add general parsing errors
        for error in self.parsing_errors:
            issues.append(f"{error.file_path}: {error.description}")
        
        return issues
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all parsed configurations.
        
        Returns:
            Dictionary with configuration summary statistics
        """
        total_configs = len(self.parsed_configs)
        valid_configs = sum(1 for config in self.parsed_configs.values() if config.schema_valid)
        total_errors = len(self.parsing_errors)
        
        format_counts = {}
        for config in self.parsed_configs.values():
            format_type = config.format_type
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        return {
            'total_configurations': total_configs,
            'valid_configurations': valid_configs,
            'invalid_configurations': total_configs - valid_configs,
            'total_parsing_errors': total_errors,
            'format_distribution': format_counts,
            'validation_success_rate': (valid_configs / total_configs * 100) if total_configs > 0 else 0
        }