# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | **Español**

clap es una aplicación de interfaz de usuario de terminal (TUI) para gestionar los perfiles de configuración y los servidores MCP de Claude Code, Codex, Gemini CLI y OpenCode. Cada configuración de proveedor, modelo y permisos se almacena como un preset, de modo que cambiar de configuración no requiere editar manualmente archivos `.json` y `.env`.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Características

- **Cambio de perfiles:** Se pueden almacenar varios presets de configuración por herramienta y activar cualquiera de ellos desde la TUI o la línea de comandos.
- **Presets de proveedores integrados:** Se incluyen plantillas de preset para el endpoint oficial y los proveedores de API compatibles más comunes de cada herramienta soportada. Al importar una plantilla se crea un preset editable; únicamente es necesario introducir la API key.
- **Gestión de servidores MCP:** Es posible añadir y eliminar servidores Model Context Protocol en la TUI; todos los cambios se guardan mediante escrituras atómicas.
- **Advertencias de activación:** Antes de activar un preset, la configuración activa actual se compara con los presets almacenados, y se muestra una advertencia cuando las credenciales no guardadas no están cubiertas por ningún preset.
- **Soporte de ratón:** La TUI acepta entrada de ratón para cambiar de pestaña, seleccionar elementos y desplazar la lista. La entrada del ratón se desactiva durante búsquedas, entrada de texto y confirmaciones.
- **Interfaz multi-idioma:** English, 简体中文, 繁體中文 y 日本語, con detección automática o cambio mediante el comando `clap lang`.

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
clap backup <nombre>   # guardar configuración actual como preset
clap diff <nombre>     # comparar preset con configuración actual
clap backups           # listar copias de seguridad
clap restore <nombre>  # restaurar copia de seguridad
clap apps              # listar herramientas soportadas
clap app <nombre>      # cambiar herramienta por defecto (claude/codex/gemini/opencode)
clap lang [code]       # mostrar/cambiar idioma (zh-CN, zh-TW, ja, en)
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

- **Sin advertencia** — Las credenciales del live config actual ya están cubiertas por algún preset almacenado (seguro para cambiar).
- **Coincidencia parcial** — Mismo proveedor/URL base pero credenciales diferentes (ej. otra cuenta). Te avisa para que guardes la configuración actual como un nuevo preset antes de cambiar.
- **Sin coincidencia** — Proveedor completamente nuevo sin coincidencia de URL base ni API key. Te advierte que guardes la configuración actual antes de perderla.

Presiona `y` para continuar o cualquier otra tecla para cancelar.

### Presets de Proveedores Integrados

Presiona `p` en la TUI para explorar las plantillas de preset integradas. Las plantillas cubren el endpoint oficial y varios proveedores de API compatibles para cada herramienta soportada. Al seleccionar una plantilla, esta se copia en el directorio de presets y se abre el editor para introducir la API key.

### Gestión de MCP

Presiona `m` en TUI (modo Claude Code) para gestionar servidores MCP:
- `a` — Añadir un nuevo servidor MCP (nombre → comando → argumentos)
- `D` — Eliminar el servidor MCP seleccionado

Los cambios se escriben en `~/.claude/settings.json` con escritura atómica.
