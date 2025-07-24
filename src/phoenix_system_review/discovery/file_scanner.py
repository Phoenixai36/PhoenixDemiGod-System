"""
File System Scanner for Phoenix Hydra System Review Tool

Provides recursive directory scanning functionality with file type detection,
categorization, and configuration file identification.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..models.data_models import Component, ComponentCategory, ComponentStatus, ProjectInventory


@dataclass
class FileInfo:
    """Information about a discovered file"""
    path: str
    name: str
    extension: str
    size: int
    modified_time: datetime
    file_type: str
    category: ComponentCategory
    is_configuration: bool = False
    is_executable: bool = False
    content_hash: Optional[str] = None


class FileSystemScanner:
    """
    Recursive directory scanner with file type detection and categorization.
    
    Scans the Phoenix Hydra project structure to identify all relevant files,
    categorize them by type and purpose, and create a comprehensive inventory.
    """
    
    # File extension mappings to categories
    EXTENSION_CATEGORIES = {
        # Python files
        '.py': ComponentCategory.INFRASTRUCTURE,
        '.pyx': ComponentCategory.INFRASTRUCTURE,
        '.pyi': ComponentCategory.INFRASTRUCTURE,
        
        # Configuration files
        '.yaml': ComponentCategory.INFRASTRUCTURE,
        '.yml': ComponentCategory.INFRASTRUCTURE,
        '.json': ComponentCategory.INFRASTRUCTURE,
        '.toml': ComponentCategory.INFRASTRUCTURE,
        '.ini': ComponentCategory.INFRASTRUCTURE,
        '.cfg': ComponentCategory.INFRASTRUCTURE,
        '.conf': ComponentCategory.INFRASTRUCTURE,
        '.env': ComponentCategory.INFRASTRUCTURE,
        
        # Infrastructure as Code
        '.tf': ComponentCategory.INFRASTRUCTURE,
        '.tfvars': ComponentCategory.INFRASTRUCTURE,
        '.hcl': ComponentCategory.INFRASTRUCTURE,
        
        # Container files
        'dockerfile': ComponentCategory.INFRASTRUCTURE,
        'compose.yaml': ComponentCategory.INFRASTRUCTURE,
        'compose.yml': ComponentCategory.INFRASTRUCTURE,
        
        # JavaScript/TypeScript (for automation)
        '.js': ComponentCategory.AUTOMATION,
        '.ts': ComponentCategory.AUTOMATION,
        '.mjs': ComponentCategory.AUTOMATION,
        
        # Shell scripts
        '.sh': ComponentCategory.AUTOMATION,
        '.ps1': ComponentCategory.AUTOMATION,
        '.bat': ComponentCategory.AUTOMATION,
        '.cmd': ComponentCategory.AUTOMATION,
        
        # Documentation
        '.md': ComponentCategory.DOCUMENTATION,
        '.rst': ComponentCategory.DOCUMENTATION,
        '.txt': ComponentCategory.DOCUMENTATION,
        '.adoc': ComponentCategory.DOCUMENTATION,
        
        # Test files
        'test_*.py': ComponentCategory.TESTING,
        '*_test.py': ComponentCategory.TESTING,
        '*.test.js': ComponentCategory.TESTING,
        '*.spec.js': ComponentCategory.TESTING,
        
        # Web files
        '.html': ComponentCategory.INFRASTRUCTURE,
        '.css': ComponentCategory.INFRASTRUCTURE,
        '.scss': ComponentCategory.INFRASTRUCTURE,
        '.sass': ComponentCategory.INFRASTRUCTURE,
    }
    
    # Configuration file patterns
    CONFIG_PATTERNS = {
        'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt',
        'package.json', 'package-lock.json', 'yarn.lock',
        'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        'compose.yml', 'compose.yaml',
        '.env', '.env.example', '.env.local',
        'config.yaml', 'config.yml', 'config.json',
        'settings.py', 'settings.yaml', 'settings.json',
        'terraform.tfvars', 'variables.tf', 'main.tf',
        '.gitignore', '.gitattributes', '.github',
        'pytest.ini', 'tox.ini', '.flake8', '.pylintrc',
        'tsconfig.json', 'webpack.config.js', 'vite.config.js'
    }
    
    # Directories to exclude from scanning
    EXCLUDE_DIRS = {
        '__pycache__', '.pytest_cache', '.git', '.svn', '.hg',
        'node_modules', '.venv', 'venv', 'venv2', 'venv3',
        '.terraform', '.terraform.lock.hcl',
        'build', 'dist', '.egg-info', '.eggs',
        '.coverage', '.nyc_output', 'coverage',
        '.DS_Store', 'Thumbs.db',
        '.idea', '.vscode/settings.json'  # Keep .vscode but exclude settings
    }
    
    # File extensions to exclude
    EXCLUDE_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.log', '.tmp', '.temp', '.cache',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.wav',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.exe', '.msi', '.deb', '.rpm'
    }

    def __init__(self, root_path: str, include_hidden: bool = False):
        """
        Initialize the file system scanner.
        
        Args:
            root_path: Root directory to scan
            include_hidden: Whether to include hidden files and directories
        """
        self.root_path = Path(root_path).resolve()
        self.include_hidden = include_hidden
        self.scanned_files: List[FileInfo] = []
        self.components: List[Component] = []
        
    def scan_project_structure(self) -> ProjectInventory:
        """
        Scan the entire project structure and return a comprehensive inventory.
        
        Returns:
            ProjectInventory with all discovered components and files
        """
        print(f"Scanning project structure at: {self.root_path}")
        
        # Reset state
        self.scanned_files.clear()
        self.components.clear()
        
        # Perform recursive scan
        total_files, total_dirs = self._scan_directory(self.root_path)
        
        # Categorize files
        config_files = [f.path for f in self.scanned_files if f.is_configuration]
        source_files = [f.path for f in self.scanned_files if f.extension in ['.py', '.js', '.ts']]
        doc_files = [f.path for f in self.scanned_files if f.category == ComponentCategory.DOCUMENTATION]
        
        # Create components from discovered files
        self._create_components_from_files()
        
        return ProjectInventory(
            components=self.components,
            total_files=total_files,
            total_directories=total_dirs,
            configuration_files=config_files,
            source_files=source_files,
            documentation_files=doc_files,
            scan_timestamp=datetime.now()
        )
    
    def _scan_directory(self, directory: Path) -> Tuple[int, int]:
        """
        Recursively scan a directory and collect file information.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            Tuple of (total_files, total_directories)
        """
        total_files = 0
        total_dirs = 0
        
        try:
            for item in directory.iterdir():
                # Skip hidden files/dirs if not included
                if not self.include_hidden and item.name.startswith('.'):
                    # Allow some important hidden files
                    if item.name not in {'.env', '.gitignore', '.github'}:
                        continue
                
                if item.is_dir():
                    # Skip excluded directories
                    if item.name in self.EXCLUDE_DIRS:
                        continue
                    
                    total_dirs += 1
                    # Recursively scan subdirectory
                    sub_files, sub_dirs = self._scan_directory(item)
                    total_files += sub_files
                    total_dirs += sub_dirs
                    
                elif item.is_file():
                    # Skip excluded file extensions
                    if item.suffix.lower() in self.EXCLUDE_EXTENSIONS:
                        continue
                    
                    # Process the file
                    file_info = self._analyze_file(item)
                    if file_info:
                        self.scanned_files.append(file_info)
                        total_files += 1
                        
        except PermissionError:
            print(f"Permission denied accessing: {directory}")
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")
            
        return total_files, total_dirs
    
    def _analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        """
        Analyze a file and extract relevant information.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            FileInfo object with file details, or None if file should be skipped
        """
        try:
            stat = file_path.stat()
            extension = file_path.suffix.lower()
            
            # Determine file type and category
            file_type = self._determine_file_type(file_path)
            category = self._determine_category(file_path, file_type)
            
            # Check if it's a configuration file
            is_config = self._is_configuration_file(file_path)
            
            # Check if it's executable
            is_executable = os.access(file_path, os.X_OK)
            
            return FileInfo(
                path=str(file_path.relative_to(self.root_path)),
                name=file_path.name,
                extension=extension,
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                file_type=file_type,
                category=category,
                is_configuration=is_config,
                is_executable=is_executable,
                content_hash=self._calculate_file_hash(file_path) if stat.st_size < 1024*1024 else None  # Only hash files < 1MB
            )
            
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _determine_file_type(self, file_path: Path) -> str:
        """
        Determine the type of file based on name and extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String describing the file type
        """
        name = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # Special cases based on filename
        if name in ['dockerfile', 'dockerfile.dev', 'dockerfile.prod']:
            return 'dockerfile'
        elif name in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']:
            return 'docker-compose'
        elif name.startswith('test_') or name.endswith('_test.py'):
            return 'python-test'
        elif name.endswith('.test.js') or name.endswith('.spec.js'):
            return 'javascript-test'
        elif name in ['pyproject.toml', 'setup.py', 'requirements.txt']:
            return 'python-config'
        elif name in ['package.json', 'package-lock.json']:
            return 'node-config'
        elif extension == '.tf':
            return 'terraform'
        elif extension == '.py':
            return 'python'
        elif extension in ['.js', '.ts']:
            return 'javascript'
        elif extension in ['.yaml', '.yml']:
            return 'yaml-config'
        elif extension == '.json':
            return 'json-config'
        elif extension == '.toml':
            return 'toml-config'
        elif extension == '.md':
            return 'markdown'
        elif extension in ['.sh', '.ps1', '.bat']:
            return 'script'
        else:
            return 'unknown'
    
    def _determine_category(self, file_path: Path, file_type: str) -> ComponentCategory:
        """
        Determine the component category for a file.
        
        Args:
            file_path: Path to the file
            file_type: Type of the file
            
        Returns:
            ComponentCategory enum value
        """
        # Check path-based categorization first
        path_str = str(file_path).lower()
        file_name = file_path.name.lower()
        
        if 'test' in path_str or file_type.endswith('-test'):
            return ComponentCategory.TESTING
        elif any(doc_dir in path_str for doc_dir in ['docs/', 'documentation/', 'readme']):
            return ComponentCategory.DOCUMENTATION
        elif any(script_dir in path_str for script_dir in ['scripts/', 'automation/', 'deploy']):
            return ComponentCategory.AUTOMATION
        elif any(infra_dir in path_str for infra_dir in ['infra/', 'infrastructure/', 'terraform/', 'docker/']):
            return ComponentCategory.INFRASTRUCTURE
        elif (any(money_dir in path_str for money_dir in ['monetization/', 'revenue/', 'affiliate/', 'grant']) or
              any(money_file in file_name for money_file in ['monetization', 'revenue', 'affiliate', 'grant', 'pricing', 'billing'])):
            return ComponentCategory.MONETIZATION
        elif any(sec_dir in path_str for sec_dir in ['security/', 'auth/', 'ssl/', 'cert']):
            return ComponentCategory.SECURITY
        
        # Fallback to extension-based categorization
        extension = file_path.suffix.lower()
        return self.EXTENSION_CATEGORIES.get(extension, ComponentCategory.INFRASTRUCTURE)
    
    def _is_configuration_file(self, file_path: Path) -> bool:
        """
        Check if a file is a configuration file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a configuration file
        """
        name = file_path.name.lower()
        path_str = str(file_path).lower()
        
        # Check exact matches
        if name in self.CONFIG_PATTERNS:
            return True
        
        # Check patterns
        if (name.startswith('config') or name.startswith('settings') or 
            name.endswith('.config.js') or name.endswith('.config.ts') or
            name.endswith('.env') or name.startswith('.env.')):
            return True
        
        # Check for files in config directories (handle both / and \ path separators)
        config_dirs = ['config/', 'configs/', 'configuration/', 'config\\', 'configs\\', 'configuration\\']
        if any(config_dir in path_str for config_dir in config_dirs):
            if name.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg')):
                return True
        
        # Check for Phoenix-specific configuration files
        if ('config' in name or 'settings' in name or 'monetization' in name or
            'deployment' in name or 'environment' in name) and name.endswith(('.json', '.yaml', '.yml', '.toml')):
            return True
            
        return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""
    
    def _create_components_from_files(self) -> None:
        """
        Create Component objects from discovered files by grouping related files.
        """
        # Group files by directory and category
        component_groups: Dict[str, List[FileInfo]] = {}
        
        for file_info in self.scanned_files:
            # Create component key based on directory and category
            dir_path = str(Path(file_info.path).parent)
            if dir_path == '.':
                dir_path = 'root'
            
            key = f"{dir_path}:{file_info.category.value}"
            if key not in component_groups:
                component_groups[key] = []
            component_groups[key].append(file_info)
        
        # Create components from groups
        for group_key, files in component_groups.items():
            dir_path, category_str = group_key.split(':', 1)
            category = ComponentCategory(category_str)
            
            # Determine component name
            if dir_path == 'root':
                component_name = f"root-{category.value}"
            else:
                component_name = f"{dir_path.replace('/', '-')}-{category.value}"
            
            # Find main configuration file for this component
            config_files = [f for f in files if f.is_configuration]
            main_config = config_files[0].path if config_files else None
            
            # Determine component status based on file analysis
            status = self._determine_component_status(files)
            
            # Create component
            component = Component(
                name=component_name,
                category=category,
                path=dir_path,
                dependencies=[],  # Will be populated by dependency analyzer
                configuration={'main_config': main_config, 'file_count': len(files)},
                status=status,
                description=f"{category.value.title()} component in {dir_path}",
                last_updated=max(f.modified_time for f in files) if files else datetime.now()
            )
            
            self.components.append(component)
    
    def _determine_component_status(self, files: List[FileInfo]) -> ComponentStatus:
        """
        Determine component status based on its files.
        
        Args:
            files: List of files in the component
            
        Returns:
            ComponentStatus enum value
        """
        if not files:
            return ComponentStatus.FAILED
        
        # Check for configuration files
        has_config = any(f.is_configuration for f in files)
        
        # Check for recent modifications (within last 30 days)
        recent_files = [f for f in files if (datetime.now() - f.modified_time).days < 30]
        
        if has_config and recent_files:
            return ComponentStatus.OPERATIONAL
        elif has_config or recent_files:
            return ComponentStatus.DEGRADED
        else:
            return ComponentStatus.UNKNOWN
    
    def get_files_by_category(self, category: ComponentCategory) -> List[FileInfo]:
        """
        Get all files belonging to a specific category.
        
        Args:
            category: Component category to filter by
            
        Returns:
            List of FileInfo objects in the specified category
        """
        return [f for f in self.scanned_files if f.category == category]
    
    def get_configuration_files(self) -> List[FileInfo]:
        """
        Get all configuration files discovered during scanning.
        
        Returns:
            List of FileInfo objects for configuration files
        """
        return [f for f in self.scanned_files if f.is_configuration]
    
    def find_files_by_pattern(self, pattern: str) -> List[FileInfo]:
        """
        Find files matching a specific pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            List of matching FileInfo objects
        """
        import fnmatch
        return [f for f in self.scanned_files if fnmatch.fnmatch(f.name, pattern)]