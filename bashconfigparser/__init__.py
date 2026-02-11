#!/usr/bin/env python3
"""
Bash-Konfigurationsdatei Parser
Unterstützt verschiedene Syntax-Stile und behält Kommentare und Formatierung bei.
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum


class VariableStyle(Enum):
    """Unterstützte Variablendefinitions-Stile"""
    BASH = "bash"          # VAR=value
    EXPORT = "export"      # export VAR=value
    DECLARE = "declare"    # declare -x VAR=value
    SETENV = "setenv"      # setenv VAR value (csh/tcsh)


@dataclass
class ConfigVariable:
    """Repräsentiert eine Variable in der Konfigurationsdatei"""
    name: str
    value: str
    style: VariableStyle
    line_number: int
    raw_line: str
    leading_whitespace: str = ""
    inline_comment: Optional[str] = None
    quote_char: str = ""  # ', ", oder leer
    
    def __str__(self) -> str:
        """Gibt die Variable in der ursprünglichen Form zurück"""
        if self.inline_comment:
            comment_part = f"  # {self.inline_comment}"
        else:
            comment_part = ""
        
        value = self.value
        if self.quote_char:
            value = f"{self.quote_char}{value}{self.quote_char}"
        
        if self.style == VariableStyle.BASH:
            return f"{self.leading_whitespace}{self.name}={value}{comment_part}"
        elif self.style == VariableStyle.EXPORT:
            return f"{self.leading_whitespace}export {self.name}={value}{comment_part}"
        elif self.style == VariableStyle.DECLARE:
            return f"{self.leading_whitespace}declare -x {self.name}={value}{comment_part}"
        elif self.style == VariableStyle.SETENV:
            return f"{self.leading_whitespace}setenv {self.name} {value}{comment_part}"
    
    def get_unquoted_value(self) -> str:
        """Gibt den Wert ohne Anführungszeichen zurück"""
        if self.quote_char and self.value.startswith(self.quote_char) and self.value.endswith(self.quote_char):
            return self.value[1:-1]
        return self.value
    
    def set_value(self, new_value: str, quote_char: str = "") -> None:
        """Setzt einen neuen Wert für die Variable"""
        self.value = new_value
        if quote_char:
            self.quote_char = quote_char


@dataclass
class ConfigComment:
    """Repräsentiert einen Kommentar in der Konfigurationsdatei"""
    content: str
    line_number: int
    raw_line: str
    is_inline: bool = False
    
    def __str__(self) -> str:
        return self.raw_line.rstrip()


@dataclass
class ConfigEmptyLine:
    """Repräsentiert eine leere Zeile in der Konfigurationsdatei"""
    line_number: int
    raw_line: str = ""
    
    def __str__(self) -> str:
        return ""


class BashConfigParser:
    """
    Parser für Bash-Konfigurationsdateien (.bashrc, .bash_profile, .profile, etc.)
    Behält Kommentare, Leerzeilen und Formatierung bei.
    """
    
    # Regex-Patterns für verschiedene Variablendefinitionen
    PATTERNS = {
        VariableStyle.BASH: re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_\.]*)\s*=\s*(.*?)\s*(#.*)?$'),
        VariableStyle.EXPORT: re.compile(r'^(\s*)export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*(#.*)?$'),
        VariableStyle.DECLARE: re.compile(r'^(\s*)declare\s+-x\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*(#.*)?$'),
        VariableStyle.SETENV: re.compile(r'^(\s*)setenv\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.*?)\s*(#.*)?$'),
    }
    
    # Kommentar-Pattern
    COMMENT_PATTERN = re.compile(r'^(\s*)#(.*)$')
    
    def __init__(self, preserve_formatting: bool = True, config_file: str = None):
        self.preserve_formatting = preserve_formatting
        self.variables: Dict[str, ConfigVariable] = {}
        self.comments: List[ConfigComment] = []
        self.empty_lines: List[ConfigEmptyLine] = []
        self.lines: List[Union[ConfigVariable, ConfigComment, ConfigEmptyLine]] = []
        self.file_path: Optional[str] = None
        if config_file != None:
            self.parse_file(config_file)
        
    def parse_file(self, file_path: str) -> None:
        """Parst eine Konfigurationsdatei"""
        self.file_path = file_path
        self._reset()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.parse_string(content)
        except FileNotFoundError:
            # Datei existiert nicht, leere Konfiguration
            pass
        except UnicodeDecodeError:
            # Versuche mit anderer Kodierung
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            self.parse_string(content)
    
    def parse_string(self, content: str) -> None:
        """Parst einen String mit Konfigurationsdaten"""
        self._reset()
        
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            self._parse_line(line.rstrip('\n'), line_num)
    
    def _parse_line(self, line: str, line_num: int) -> None:
        """Parst eine einzelne Zeile"""
        # Leerzeile
        if not line.strip():
            empty_line = ConfigEmptyLine(line_number=line_num, raw_line=line)
            self.empty_lines.append(empty_line)
            self.lines.append(empty_line)
            return
        
        # Kommentarzeile
        comment_match = self.COMMENT_PATTERN.match(line)
        if comment_match:
            comment = ConfigComment(
                content=comment_match.group(2).strip(),
                line_number=line_num,
                raw_line=line,
                is_inline=False
            )
            self.comments.append(comment)
            self.lines.append(comment)
            return
        
        # Versuche verschiedene Variablendefinitionen
        var = self._parse_variable_line(line, line_num)
        if var:
            self.variables[var.name] = var
            self.lines.append(var)
        else:
            # Keine erkannte Syntax, als Kommentar behandeln (oder Originalzeile behalten)
            comment = ConfigComment(
                content=f"UNPARSED: {line}",
                line_number=line_num,
                raw_line=line,
                is_inline=False
            )
            self.comments.append(comment)
            self.lines.append(comment)
    
    def _parse_variable_line(self, line: str, line_num: int) -> Optional[ConfigVariable]:
        """Parst eine Zeile als Variablendefinition"""
        for style, pattern in self.PATTERNS.items():
            match = pattern.match(line)
            if match:
                leading_whitespace = match.group(1)
                var_name = match.group(2)
                var_value = match.group(3).rstrip()
                inline_comment = match.group(4) if match.group(4) else None
                
                # Extrahiere Inline-Kommentar
                comment_content = None
                if inline_comment:
                    comment_content = inline_comment[1:].strip()  # Remove #
                    # Wenn der Wert selbst ein Kommentarzeichen enthält, müssen wir aufpassen
                    if '#' in var_value:
                        # Überprüfe ob # Teil des Wertes ist (in Anführungszeichen)
                        var_value, comment_content = self._split_value_and_comment(var_value, inline_comment)
                
                # Erkenne Anführungszeichen
                quote_char, unquoted_value = self._extract_quotes(var_value)
                
                return ConfigVariable(
                    name=var_name,
                    value=unquoted_value,
                    style=style,
                    line_number=line_num,
                    raw_line=line,
                    leading_whitespace=leading_whitespace,
                    inline_comment=comment_content,
                    quote_char=quote_char
                )
        
        return None
    
    def _split_value_and_comment(self, value: str, full_comment: str) -> Tuple[str, Optional[str]]:
        """Trennt Wert und Inline-Kommentar, wenn # in Anführungszeichen erscheint"""
        # Einfache Implementierung: Nehme alles vor dem ersten ungequoteten # als Wert
        in_single_quote = False
        in_double_quote = False
        escaped = False
        
        for i, char in enumerate(value):
            if escaped:
                escaped = False
                continue
                
            if char == '\\':
                escaped = True
                continue
                
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == '#' and not in_single_quote and not in_double_quote:
                # Ungequotetes # gefunden -> hier beginnt Kommentar
                return value[:i].rstrip(), value[i+1:].strip()
        
        return value, full_comment[1:].strip() if full_comment else None
    
    def _extract_quotes(self, value: str) -> Tuple[str, str]:
        """Extrahiert Anführungszeichen aus einem Wert"""
        if not value:
            return "", value
        
        # Prüfe auf einfache Anführungszeichen
        if value.startswith("'") and value.endswith("'"):
            return "'", value[1:-1]
        
        # Prüfe auf doppelte Anführungszeichen
        if value.startswith('"') and value.endswith('"'):
            return '"', value[1:-1]
        
        # Prüfe auf kombinierte Anführungszeichen (selten, aber möglich)
        # Beispiel: '"value"' oder "'value'"
        if len(value) >= 4:
            if (value.startswith("'\"") and value.endswith("\"'")) or \
               (value.startswith('"\'') and value.endswith('\'"')):
                return value[0:2], value[2:-2]
        
        return "", value
    
    def get(self, name: str, default: Any = None) -> Optional[str]:
        """Gibt den Wert einer Variable zurück"""
        if name in self.variables:
            return self.variables[name].get_unquoted_value()
        return default
    
    def set(self, name: str, value: str, style: VariableStyle = VariableStyle.BASH, 
            quote_char: str = "", inline_comment: Optional[str] = None) -> None:
        """Setzt eine Variable"""
        # Prüfe ob Variable bereits existiert
        if name in self.variables:
            # Aktualisiere bestehende Variable
            var = self.variables[name]
            var.set_value(value, quote_char or var.quote_char)
            var.style = style
            if inline_comment is not None:
                var.inline_comment = inline_comment
        else:
            # Erstelle neue Variable
            var = ConfigVariable(
                name=name,
                value=value,
                style=style,
                line_number=0,  # Wird beim Speichern angepasst
                raw_line="",
                leading_whitespace="",
                inline_comment=inline_comment,
                quote_char=quote_char
            )
            self.variables[name] = var
            # Füge am Ende der Datei hinzu
            self.lines.append(var)
    
    def remove(self, name: str) -> bool:
        """Entfernt eine Variable"""
        if name in self.variables:
            var = self.variables[name]
            # Entferne aus der lines-Liste
            self.lines = [line for line in self.lines if not (isinstance(line, ConfigVariable) and line.name == name)]
            # Entferne aus dem Dictionary
            del self.variables[name]
            return True
        return False
    
    def save(self, file_path: Optional[str] = None) -> None:
        """Speichert die Konfiguration in eine Datei"""
        if file_path is None:
            if self.file_path is None:
                raise ValueError("Keine Datei angegeben")
            file_path = self.file_path
        
        lines = []
        for item in self.lines:
            lines.append(str(item))
        
        content = '\n'.join(lines)
        
        # Backup der originalen Datei erstellen
        if os.path.exists(file_path):
            backup_path = f"{file_path}.bak"
            try:
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            except:
                pass
        
        # Neue Datei schreiben
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def to_string(self) -> str:
        """Gibt die Konfiguration als String zurück"""
        lines = []
        for item in self.lines:
            lines.append(str(item))
        return '\n'.join(lines)
    
    def get_all_variables(self) -> Dict[str, str]:
        """Gibt alle Variablen als Dictionary zurück"""
        return {name: var.get_unquoted_value() for name, var in self.variables.items()}
    
    def add_comment(self, comment: str, position: Optional[int] = None) -> None:
        """Fügt einen Kommentar hinzu"""
        comment_line = f"# {comment}"
        comment_obj = ConfigComment(
            content=comment,
            line_number=0,
            raw_line=comment_line,
            is_inline=False
        )
        
        if position is None:
            self.lines.append(comment_obj)
        else:
            self.lines.insert(position, comment_obj)
        
        self.comments.append(comment_obj)
    
    def add_empty_line(self, position: Optional[int] = None) -> None:
        """Fügt eine leere Zeile hinzu"""
        empty_line = ConfigEmptyLine(line_number=0)
        
        if position is None:
            self.lines.append(empty_line)
        else:
            self.lines.insert(position, empty_line)
        
        self.empty_lines.append(empty_line)
    
    def _reset(self) -> None:
        """Setzt den Parser zurück"""
        self.variables.clear()
        self.comments.clear()
        self.empty_lines.clear()
        self.lines.clear()
    
    def validate_variable_name(self, name: str) -> bool:
        """Validiert einen Variablennamen"""
        pattern = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
        return bool(pattern.match(name))


# Hilfsfunktionen für häufige Aufgaben
def load_config(file_path: str) -> BashConfigParser:
    """Lädt eine Konfigurationsdatei"""
    parser = BashConfigParser()
    parser.parse_file(file_path)
    return parser


def create_config() -> BashConfigParser:
    """Erstellt einen neuen, leeren Konfigurationsparser"""
    return BashConfigParser()


# Beispiel-Nutzung
if __name__ == "__main__":
    parser = BashConfigParser()
    parser.parse_file("/etc/sysconfig/cranix")
    
    print("Gefundene Variablen:")
    for name, var in parser.variables.items():
        print(f"  {name}: {var.get_unquoted_value()} (Style: {var.style.value})")
    
    print("\nKommentare:")
    for comment in parser.comments:
        if not comment.is_inline:
            print(f"  Line {comment.line_number}: {comment.content}")
    
