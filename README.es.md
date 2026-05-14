# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | **Español**

Gestor de Perfiles Multi-Herramienta — Una herramienta TUI ligera para gestionar perfiles de configuración de Claude Code, Codex, Gemini CLI y OpenCode.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Instalación

### vía npm

```bash
npm install -g @pterchan/clap
```

### vía curl

```bash
curl -fsSL https://raw.githubusercontent.com/pterchan/Clap/main/install.sh | bash
```

O localmente:

```bash
./install.sh
```

## Uso

```bash
clap                   # abrir TUI
clap ls                # listar presets de la herramienta actual
clap use <nombre>      # activar preset
clap current           # mostrar preset activo
clap diff <nombre>     # comparar preset con configuración actual
clap backups           # listar copias de seguridad
clap restore <nombre>  # restaurar copia de seguridad
clap apps              # listar herramientas soportadas
clap app <nombre>      # cambiar herramienta por defecto (claude/codex/gemini/opencode)
```

### Herramientas Soportadas

| Herramienta | Archivo(s) de Configuración | Formato |
|-------------|----------------------------|---------|
| Claude Code | `~/.claude/settings.json` | JSON |
| Codex | `~/.codex/auth.json` + `~/.codex/config.toml` | JSON + TOML |
| Gemini CLI | `~/.gemini/.env` | KEY=VALUE |
| OpenCode | `~/.config/opencode/opencode.json` | JSON |

### Atajos de TUI

| Tecla | Función | Tecla | Función |
|-------|---------|-------|---------|
| `↑` / `↓` / `j` / `k` | Moverse | `Enter` | Activar |
| `e` | Editar | `n` | Nuevo |
| `d` | Duplicar | `R` | Renombrar |
| `D` | Eliminar | `/` | Filtrar |
| `=` | Comparar | `b` | Ver copias de seguridad |
| `r` | Recargar | `o` | Abrir carpeta de presets |
| `Tab` | Cambiar herramienta | `p` | Presets integrados |
| `m` | Gestor MCP | `q` | Salir |

### Soporte para Ratón

La TUI soporta interacción con ratón:
- **Clic** en una pestaña (fila 1) para cambiar de herramienta
- **Clic** en un preset de la lista para activarlo
- **Clic** en un atajo de teclado inferior para ejecutar la acción (`e`, `n`, `d`, `D`, `/`, `=`, `b`, `r`, `o`, `p`, `m`, `q`)
- **Rueda de desplazamiento** para navegar por la lista

El ratón se desactiva durante búsquedas, entrada de texto y confirmaciones para evitar acciones accidentales.

### Advertencias de Activación

Al activar un preset, clap compara sus credenciales (API key, URL base, modelo) con todos los presets almacenados:

- **Coincidencia parcial** — Mismo proveedor/URL base pero credenciales diferentes (ej. otra cuenta). Te avisa para que guardes la configuración actual como un nuevo preset antes de cambiar.
- **Sin coincidencia** — Proveedor completamente nuevo sin coincidencia de URL base ni API key. Te advierte que guardes la configuración actual antes de perderla.

Presiona `y` para continuar o cualquier otra tecla para cancelar.

### Presets de Proveedores Integrados

Presiona `p` en TUI para explorar más de 17 presets de proveedores integrados:

- **Claude Code**: Anthropic oficial, DeepSeek, Kimi, SiliconFlow, OpenRouter, AWS Bedrock, Azure, Groq, Together AI
- **Codex**: OpenAI oficial, OpenRouter, DeepSeek
- **Gemini CLI**: Google oficial, OpenRouter
- **OpenCode**: Anthropic oficial, DeepSeek

Selecciona uno para auto-llenar la plantilla — solo añade tu API key.

### Gestión de MCP

Presiona `m` en TUI (modo Claude Code) para gestionar servidores MCP:
- `a` — Añadir un nuevo servidor MCP (nombre → comando → argumentos)
- `D` — Eliminar el servidor MCP seleccionado

Los cambios se escriben en `~/.claude/settings.json` con escritura atómica.
