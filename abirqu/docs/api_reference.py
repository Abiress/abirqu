"""
Task 19.2 — API Reference Generator.

Automatically generate API reference documentation from code.
Support multiple output formats (Markdown, RST, HTML, Jupyter).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import inspect
import re


class APIFormat(Enum):
    """Output formats for API reference."""
    MARKDOWN = "markdown"
    RESTRUCTURED_TEXT = "rst"
    HTML = "html"
    JUPYTER = "jupyter"


@dataclass
class APIParameter:
    """API parameter documentation."""
    name: str
    type: str
    description: str = ""
    default: Optional[Any] = None
    required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'default': str(self.default) if self.default is not None else None,
            'required': self.required
        }


@dataclass
class APIEndpoint:
    """Documentation for an API endpoint or function."""
    endpoint_id: str
    name: str
    module: str
    signature: str
    description: str = ""
    parameters: List[APIParameter] = field(default_factory=list)
    returns: str = ""
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint_id': self.endpoint_id,
            'name': self.name,
            'module': self.module,
            'signature': self.signature,
            'description': self.description,
            'parameters': [p.to_dict() for p in self.parameters],
            'returns': self.returns,
            'examples': self.examples,
            'tags': self.tags,
            'deprecated': self.deprecated,
            'version': self.version
        }


@dataclass
class APISchema:
    """Schema for API documentation."""
    schema_id: str
    title: str
    version: str
    endpoints: List[APIEndpoint]
    modules: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'schema_id': self.schema_id,
            'title': self.title,
            'version': self.version,
            'endpoints': [e.to_dict() for e in self.endpoints],
            'modules': self.modules,
            'endpoint_count': len(self.endpoints),
            'metadata': self.metadata
        }


@dataclass
class APIReferenceResult:
    """Result of API reference generation."""
    success: bool
    schema: Optional[APISchema] = None
    output: Optional[str] = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'schema_id': self.schema.schema_id if self.schema else None,
            'message': self.message,
            'output_length': len(self.output) if self.output else 0
        }


class CodeParser:
    """Parse Python code to extract API information."""
    
    def __init__(self):
        self.parsed_modules: Dict[str, Any] = {}
    
    def parse_module(self, module: Any) -> Dict[str, Any]:
        """Parse a module and extract API info."""
        module_name = module.__name__ if hasattr(module, '__name__') else str(module)
        
        info = {
            'name': module_name,
            'functions': [],
            'classes': [],
            'constants': []
        }
        
        # Get all members.
        members = inspect.getmembers(module)
        
        for name, obj in members:
            # Skip private members.
            if name.startswith('_'):
                continue
            
            if inspect.isfunction(obj):
                info['functions'].append(self._parse_function(name, obj))
            elif inspect.isclass(obj):
                info['classes'].append(self._parse_class(name, obj))
            elif not callable(obj) and not name.startswith('__'):
                info['constants'].append({
                    'name': name,
                    'value': str(obj),
                    'type': type(obj).__name__
                })
        
        self.parsed_modules[module_name] = info
        return info
    
    def _parse_function(self, name: str, func: Any) -> Dict[str, Any]:
        """Parse a function."""
        try:
            sig = inspect.signature(func)
            doc = inspect.getdoc(func) or ""
            
            params = []
            for param_name, param in sig.parameters.items():
                param_info = {
                    'name': param_name,
                    'type': str(param.annotation) if param.annotation != param.empty else 'Any',
                    'default': str(param.default) if param.default != param.empty else None,
                    'required': param.default == param.empty
                }
                params.append(param_info)
            
            return {
                'name': name,
                'signature': f"{name}{sig}",
                'docstring': doc,
                'parameters': params,
                'returns': str(sig.return_annotation) if sig.return_annotation != sig.empty else 'None'
            }
        except Exception:
            return {
                'name': name,
                'signature': f"{name}(...)",
                'docstring': '',
                'parameters': [],
                'returns': 'None'
            }
    
    def _parse_class(self, name: str, cls: Any) -> Dict[str, Any]:
        """Parse a class."""
        methods = []
        for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not method_name.startswith('_') or method_name in ('__init__', '__call__'):
                methods.append(self._parse_function(method_name, method))
        
        return {
            'name': name,
            'docstring': inspect.getdoc(cls) or "",
            'methods': methods
        }


class APIReferenceGenerator:
    """Main API reference generator."""
    
    def __init__(self):
        self.parser = CodeParser()
        self.endpoints: List[APIEndpoint] = []
        self.schemas: Dict[str, APISchema] = {}
        self.formatters: Dict[APIFormat, Callable] = {}
        self._register_formatters()
    
    def _register_formatters(self):
        """Register output formatters."""
        self.formatters[APIFormat.MARKDOWN] = self._format_markdown
        self.formatters[APIFormat.HTML] = self._format_html
        self.formatters[APIFormat.RESTRUCTURED_TEXT] = self._format_rst
        self.formatters[APIFormat.JUPYTER] = self._format_jupyter
    
    def generate_from_module(self, module: Any,
                            version: str = "1.0") -> APIReferenceResult:
        """Generate API reference from a module."""
        try:
            module_info = self.parser.parse_module(module)
            
            endpoints = []
            endpoint_counter = 0
            
            # Create endpoints for functions.
            for func_info in module_info['functions']:
                endpoint_counter += 1
                params = [
                    APIParameter(
                        name=p['name'],
                        type=p['type'],
                        description=self._extract_param_desc(func_info['docstring'], p['name']),
                        default=p['default'],
                        required=p['required']
                    )
                    for p in func_info['parameters']
                ]
                
                endpoint = APIEndpoint(
                    endpoint_id=f"ep_{endpoint_counter}",
                    name=func_info['name'],
                    module=module_info['name'],
                    signature=func_info['signature'],
                    description=func_info['docstring'],
                    parameters=params,
                    returns=func_info['returns'],
                    examples=self._extract_examples(func_info['docstring'])
                )
                endpoints.append(endpoint)
            
            # Create endpoints for class methods.
            for class_info in module_info['classes']:
                for method_info in class_info.get('methods', []):
                    endpoint_counter += 1
                    params = [
                        APIParameter(
                            name=p['name'],
                            type=p['type'],
                            description=self._extract_param_desc(method_info['docstring'], p['name']),
                            default=p['default'],
                            required=p['required']
                        )
                        for p in method_info['parameters'] if p['name'] != 'self'
                    ]
                    
                    endpoint = APIEndpoint(
                        endpoint_id=f"ep_{endpoint_counter}",
                        name=f"{class_info['name']}.{method_info['name']}",
                        module=module_info['name'],
                        signature=method_info['signature'],
                        description=method_info['docstring'],
                        parameters=params,
                        returns=method_info['returns'],
                        examples=self._extract_examples(method_info['docstring'])
                    )
                    endpoints.append(endpoint)
            
            # Create schema.
            schema = APISchema(
                schema_id=f"schema_{len(self.schemas) + 1}",
                title=f"{module_info['name']} API Reference",
                version=version,
                endpoints=endpoints,
                modules=[module_info['name']]
            )
            
            self.schemas[schema.schema_id] = schema
            
            return APIReferenceResult(
                success=True,
                schema=schema,
                message=f"Generated API reference with {len(endpoints)} endpoints"
            )
            
        except Exception as e:
            return APIReferenceResult(
                success=False,
                message=f"Failed to generate API reference: {e}"
            )
    
    def _extract_param_desc(self, docstring: str, param_name: str) -> str:
        """Extract parameter description from docstring."""
        if not docstring:
            return ""
        
        # Simple extraction: look for param_name in docstring.
        lines = docstring.split('\n')
        for line in lines:
            if param_name in line and (':' in line or '-' in line):
                return line.strip()
        return ""
    
    def _extract_examples(self, docstring: str) -> List[str]:
        """Extract examples from docstring."""
        if not docstring:
            return []
        
        examples = []
        in_example = False
        current_example = []
        
        for line in docstring.split('\n'):
            if 'example' in line.lower() or '>>>' in line:
                in_example = True
                if '>>>' in line:
                    current_example.append(line)
            elif in_example:
                if line.strip() == '' or (current_example and not line.startswith('>>>')):
                    if current_example:
                        examples.append('\n'.join(current_example))
                    current_example = []
                    in_example = False
                else:
                    current_example.append(line)
        
        if current_example:
            examples.append('\n'.join(current_example))
        
        return examples
    
    def format_output(self, schema: APISchema,
                      format: APIFormat = APIFormat.MARKDOWN) -> str:
        """Format schema to specified output format."""
        if format in self.formatters:
            return self.formatters[format](schema)
        return self._format_markdown(schema)
    
    def _format_markdown(self, schema: APISchema) -> str:
        """Format as Markdown."""
        md = f"# {schema.title}\n\n"
        md += f"Version: {schema.version}\n\n"
        md += f"## Endpoints ({len(schema.endpoints)})\n\n"
        
        for ep in schema.endpoints:
            md += f"### {ep.name}\n\n"
            md += f"**Signature:** `{ep.signature}`\n\n"
            if ep.description:
                md += f"{ep.description}\n\n"
            if ep.parameters:
                md += "**Parameters:**\n\n"
                for p in ep.parameters:
                    req = "required" if p.required else "optional"
                    md += f"- `{p.name}` ({p.type}, {req}): {p.description}\n"
                md += "\n"
            if ep.returns:
                md += f"**Returns:** {ep.returns}\n\n"
            if ep.examples:
                md += "**Examples:**\n\n"
                for ex in ep.examples:
                    md += f"```\n{ex}\n```\n\n"
        
        return md
    
    def _format_html(self, schema: APISchema) -> str:
        """Format as HTML."""
        html = f"<html><head><title>{schema.title}</title></head><body>"
        html += f"<h1>{schema.title}</h1>"
        html += f"<p>Version: {schema.version}</p>"
        html += f"<h2>Endpoints ({len(schema.endpoints)})</h2>"
        
        for ep in schema.endpoints:
            html += f"<h3>{ep.name}</h3>"
            html += f"<p><strong>Signature:</strong> <code>{ep.signature}</code></p>"
            if ep.description:
                html += f"<p>{ep.description}</p>"
        
        html += "</body></html>"
        return html
    
    def _format_rst(self, schema: APISchema) -> str:
        """Format as reStructuredText."""
        rst = f"{schema.title}\n{'=' * len(schema.title)}\n\n"
        rst += f"Version: {schema.version}\n\n"
        rst += f"Endpoints ({len(schema.endpoints)})\n{'-' * 20}\n\n"
        
        for ep in schema.endpoints:
            rst += f"{ep.name}\n{'-' * len(ep.name)}\n\n"
            rst += f"**Signature:** ``{ep.signature}``\n\n"
            if ep.description:
                rst += f"{ep.description}\n\n"
        
        return rst
    
    def _format_jupyter(self, schema: APISchema) -> str:
        """Format as Jupyter notebook JSON."""
        cells = []
        
        # Title cell.
        cells.append({
            'cell_type': 'markdown',
            'metadata': {},
            'source': [f"# {schema.title}\n\nVersion: {schema.version}"]
        })
        
        # Endpoint cells.
        for ep in schema.endpoints:
            cells.append({
                'cell_type': 'markdown',
                'metadata': {},
                'source': [f"## {ep.name}\n\n`{ep.signature}`\n\n{ep.description}"]
            })
        
        notebook = {
            'metadata': {
                'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
            },
            'nbformat': 4,
            'nbformat_minor': 4,
            'cells': cells
        }
        
        import json
        return json.dumps(notebook, indent=2)
    
    def export(self, schema_id: str,
               format: APIFormat = APIFormat.MARKDOWN) -> APIReferenceResult:
        """Export a schema to specified format."""
        if schema_id not in self.schemas:
            return APIReferenceResult(
                success=False,
                message=f"Schema {schema_id} not found"
            )
        
        schema = self.schemas[schema_id]
        output = self.format_output(schema, format)
        
        return APIReferenceResult(
            success=True,
            schema=schema,
            output=output,
            message=f"Exported to {format.value}"
        )
