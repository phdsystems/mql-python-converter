"""
Pine Script Parser Module
Parses Pine Script code and creates an Abstract Syntax Tree (AST)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PineType(Enum):
    """Pine Script data types"""
    SERIES = "series"
    SIMPLE = "simple"
    CONST = "const"
    INPUT = "input"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    COLOR = "color"
    PLOT = "plot"
    HLINE = "hline"


@dataclass
class PineVariable:
    """Represents a Pine Script variable"""
    name: str
    type: Optional[PineType]
    value: Any
    is_series: bool = False
    is_input: bool = False


@dataclass
class PineFunction:
    """Represents a Pine Script function"""
    name: str
    params: List[str]
    body: List[str]
    return_type: Optional[PineType] = None


@dataclass
class PineIndicator:
    """Represents a Pine Script indicator"""
    version: int
    title: str
    shorttitle: Optional[str]
    overlay: bool
    precision: Optional[int]
    scale: Optional[str]
    variables: Dict[str, PineVariable]
    functions: Dict[str, PineFunction]
    plots: List[Dict]
    alerts: List[Dict]


class PineScriptParser:
    """Parser for Pine Script code"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset parser state"""
        self.version = 5
        self.indicator_info = {}
        self.variables = {}
        self.functions = {}
        self.plots = []
        self.alerts = []
        self.imports = []
        
    def parse(self, code: str) -> PineIndicator:
        """
        Parse Pine Script code and return indicator object
        
        Args:
            code: Pine Script source code
            
        Returns:
            PineIndicator object
        """
        self.reset()
        
        # Clean and split code into lines
        lines = self._preprocess_code(code)
        
        # Parse each component
        self._parse_version(lines)
        self._parse_indicator_declaration(lines)
        self._parse_inputs(lines)
        self._parse_variables(lines)
        self._parse_functions(lines)
        self._parse_plots(lines)
        self._parse_alerts(lines)
        
        # Build and return indicator object
        return PineIndicator(
            version=self.version,
            title=self.indicator_info.get('title', 'Untitled'),
            shorttitle=self.indicator_info.get('shorttitle'),
            overlay=self.indicator_info.get('overlay', True),
            precision=self.indicator_info.get('precision'),
            scale=self.indicator_info.get('scale'),
            variables=self.variables,
            functions=self.functions,
            plots=self.plots,
            alerts=self.alerts
        )
    
    def _preprocess_code(self, code: str) -> List[str]:
        """Clean and prepare code for parsing"""
        # Remove comments
        lines = []
        for line in code.split('\n'):
            # Remove single-line comments
            if '//' in line:
                line = line[:line.index('//')]
            lines.append(line.strip())
        
        # Remove empty lines
        lines = [l for l in lines if l]
        
        return lines
    
    def _parse_version(self, lines: List[str]):
        """Parse Pine Script version"""
        for line in lines:
            if line.startswith('//@version='):
                self.version = int(line.split('=')[1])
                break
    
    def _parse_indicator_declaration(self, lines: List[str]):
        """Parse indicator() declaration"""
        for line in lines:
            if line.startswith('indicator('):
                # Extract parameters
                params_str = line[10:-1]  # Remove 'indicator(' and ')'
                params = self._parse_function_params(params_str)
                
                for param in params:
                    if '=' in param:
                        key, value = param.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if key == 'overlay':
                            self.indicator_info[key] = value.lower() == 'true'
                        elif key == 'precision':
                            self.indicator_info[key] = int(value)
                        else:
                            self.indicator_info[key] = value
                    else:
                        # First parameter is usually title
                        self.indicator_info['title'] = param.strip('"\'')
    
    def _parse_inputs(self, lines: List[str]):
        """Parse input declarations"""
        input_patterns = [
            r'(\w+)\s*=\s*input\.int\((.*?)\)',
            r'(\w+)\s*=\s*input\.float\((.*?)\)',
            r'(\w+)\s*=\s*input\.bool\((.*?)\)',
            r'(\w+)\s*=\s*input\.string\((.*?)\)',
            r'(\w+)\s*=\s*input\.color\((.*?)\)',
            r'(\w+)\s*=\s*input\.source\((.*?)\)',
            r'(\w+)\s*=\s*input\((.*?)\)',
        ]
        
        for line in lines:
            for pattern in input_patterns:
                match = re.search(pattern, line)
                if match:
                    var_name = match.group(1)
                    params = match.group(2)
                    
                    # Parse input parameters
                    param_list = self._parse_function_params(params)
                    default_value = None
                    title = var_name
                    
                    if param_list:
                        # First param is usually default value
                        default_value = self._parse_value(param_list[0])
                        
                        # Look for title parameter
                        for param in param_list[1:]:
                            if 'title=' in param or '"' in param:
                                title = param.split('=', 1)[-1].strip('"\'')
                                break
                    
                    self.variables[var_name] = PineVariable(
                        name=var_name,
                        type=PineType.INPUT,
                        value=default_value,
                        is_input=True
                    )
    
    def _parse_variables(self, lines: List[str]):
        """Parse variable declarations"""
        for line in lines:
            # Skip if it's an input or function declaration
            if 'input.' in line or 'input(' in line:
                continue
            if line.startswith('indicator(') or line.startswith('strategy('):
                continue
            if line.startswith('plot(') or line.startswith('hline('):
                continue
            
            # Match variable assignment
            match = re.match(r'^(\w+)\s*=\s*(.+)$', line)
            if match:
                var_name = match.group(1)
                expression = match.group(2)
                
                # Skip if already parsed as input
                if var_name in self.variables:
                    continue
                
                # Determine if it's a series
                is_series = any(func in expression for func in [
                    'close', 'open', 'high', 'low', 'volume',
                    'sma(', 'ema(', 'rsi(', 'macd(', 'bb(',
                    'ta.', 'math.', 'array.'
                ])
                
                self.variables[var_name] = PineVariable(
                    name=var_name,
                    type=PineType.SERIES if is_series else PineType.SIMPLE,
                    value=expression,
                    is_series=is_series
                )
    
    def _parse_functions(self, lines: List[str]):
        """Parse function declarations"""
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for function declaration (Pine v5 syntax)
            func_match = re.match(r'^(\w+)\((.*?)\)\s*=>', line)
            if func_match:
                func_name = func_match.group(1)
                params = func_match.group(2)
                
                # Parse function body
                body = []
                i += 1
                indent_level = None
                
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.startswith('    '):  # Indented line
                        body.append(next_line.strip())
                    else:
                        break
                    i += 1
                
                self.functions[func_name] = PineFunction(
                    name=func_name,
                    params=self._parse_function_params(params),
                    body=body
                )
            
            i += 1
    
    def _parse_plots(self, lines: List[str]):
        """Parse plot declarations"""
        plot_patterns = [
            r'plot\((.*?)\)',
            r'plotshape\((.*?)\)',
            r'plotchar\((.*?)\)',
            r'plotcandle\((.*?)\)',
            r'plotbar\((.*?)\)',
            r'hline\((.*?)\)',
            r'fill\((.*?)\)'
        ]
        
        for line in lines:
            for pattern in plot_patterns:
                match = re.search(pattern, line)
                if match:
                    plot_type = pattern.split('\\')[0]
                    params = self._parse_function_params(match.group(1))
                    
                    plot_info = {
                        'type': plot_type,
                        'params': params
                    }
                    
                    # Parse specific parameters
                    for param in params:
                        if '=' in param:
                            key, value = param.split('=', 1)
                            plot_info[key.strip()] = value.strip()
                    
                    self.plots.append(plot_info)
    
    def _parse_alerts(self, lines: List[str]):
        """Parse alert conditions"""
        for line in lines:
            if 'alertcondition(' in line:
                match = re.search(r'alertcondition\((.*?)\)', line)
                if match:
                    params = self._parse_function_params(match.group(1))
                    
                    alert_info = {'params': params}
                    for param in params:
                        if '=' in param:
                            key, value = param.split('=', 1)
                            alert_info[key.strip()] = value.strip()
                    
                    self.alerts.append(alert_info)
    
    def _parse_function_params(self, params_str: str) -> List[str]:
        """Parse function parameters, handling nested parentheses"""
        params = []
        current_param = ''
        paren_depth = 0
        
        for char in params_str:
            if char == '(' :
                paren_depth += 1
                current_param += char
            elif char == ')':
                paren_depth -= 1
                current_param += char
            elif char == ',' and paren_depth == 0:
                params.append(current_param.strip())
                current_param = ''
            else:
                current_param += char
        
        if current_param.strip():
            params.append(current_param.strip())
        
        return params
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a value string into appropriate Python type"""
        value_str = value_str.strip()
        
        # Boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        
        # String
        if value_str.startswith('"') or value_str.startswith("'"):
            return value_str.strip('"\'')
        
        # Number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Default to string representation
        return value_str


def parse_pinescript(code: str) -> PineIndicator:
    """
    Convenience function to parse Pine Script code
    
    Args:
        code: Pine Script source code
        
    Returns:
        PineIndicator object
    """
    parser = PineScriptParser()
    return parser.parse(code)