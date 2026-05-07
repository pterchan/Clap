# clap

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | **Español**

Gestor de Perfiles de Claude Code — Una herramienta TUI para gestionar múltiples perfiles de `settings.json` desde la terminal.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Instalación

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
clap ls                # listar perfiles
clap use <nombre>      # activar perfil
clap current           # mostrar perfil activo
clap diff <nombre>     # comparar perfil con la configuración actual
clap backups           # listar copias de seguridad
clap restore <nombre>  # restaurar copia de seguridad
```

### Atajos de TUI

| Tecla | Función | Tecla | Función |
|-------|---------|-------|---------|
| `↑` / `↓` / `j` / `k` | Moverse | `Enter` | Activar |
| `e` | Editar | `n` | Nuevo |
| `d` | Duplicar | `R` | Renombrar |
| `D` | Eliminar | `/` | Filtrar |
| `=` | Comparar | `b` | Ver copias de seguridad |
| `r` | Recargar | `o` | Abrir en Finder |
| `q` | Salir | | |
