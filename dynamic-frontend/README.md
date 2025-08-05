# Dynamic Frontend - API Contract Documentation

## 1. Introducción

Este documento detalla el contrato de la API que el equipo de backend debe implementar para que el frontend dinámico funcione correctamente. El frontend es una capa de presentación "tonta" que se renderiza completamente basada en las respuestas de la API.

## 2. Endpoints Principales

### `GET /api/config`

Este es el endpoint más importante. Se llama una vez al iniciar la aplicación para obtener la configuración global de la UI.

-   **Respuesta Exitosa (200 OK)**

```json
{
  "navigation": [
    {
      "id": "dashboard",
      "label": "Dashboard",
      "path": "/page/dashboard",
      "icon": "home"
    },
    {
      "id": "users",
      "label": "Usuarios",
      "path": "/page/users",
      "icon": "users"
    }
  ],
  "userPermissions": ["read:users", "write:users", "read:dashboard"]
}
```

-   **Estructura `AppConfig`**:
    -   `navigation` (`NavigationItem[]`): Un array de objetos que definen los elementos del menú de navegación principal.
        -   `id` (`string`): Identificador único.
        -   `label` (`string`): Texto a mostrar.
        -   `path` (`string`): La ruta a la que enlaza (generalmente `/page/:pageName`).
        -   `icon` (`string`, opcional): Nombre de un icono.
        -   `children` (`NavigationItem[]`, opcional): Para submenús anidados.
    -   `userPermissions` (`string[]`): Un array de strings que representan los permisos del usuario actual.

---

### `GET /api/layouts/:pageName`

Este endpoint proporciona la configuración de layout para una página específica.

-   **Parámetros de URL**:
    -   `pageName` (`string`): El identificador de la página (e.g., `dashboard`, `users`).

-   **Respuesta Exitosa (200 OK)**

```json
{
  "type": "grid",
  "layoutConfig": {
    "columns": 2,
    "gap": 16
  },
  "widgets": [
    {
      "id": "users-table",
      "component": "DataTable",
      "config": {
        "api": {
          "url": "/api/users",
          "method": "GET"
        },
        "columns": [
          { "key": "name", "header": "Nombre", "dataType": "string", "sortable": true },
          { "key": "email", "header": "Email", "dataType": "string" },
          { "key": "role", "header": "Rol", "dataType": "string", "filterable": true }
        ],
        "pagination": {
          "defaultPageSize": 10,
          "pageSizeOptions": [5, 10, 20]
        }
      }
    },
    {
      "id": "add-user-form",
      "component": "FormGenerator",
      "config": {
        "fields": [
          {
            "name": "name",
            "label": "Nombre de Usuario",
            "type": "text",
            "validation": [{ "type": "required", "message": "El nombre es obligatorio." }]
          },
          {
            "name": "email",
            "label": "Email",
            "type": "text",
            "validation": [{ "type": "required", "message": "El email es obligatorio." }]
          }
        ],
        "submitUrl": "/api/users",
        "submitMethod": "POST"
      }
    }
  ]
}
```

-   **Estructura `PageLayout`**:
    -   `type` (`'grid' | 'flex' | 'tabs'`): El tipo de contenedor principal.
    -   `layoutConfig` (`Record<string, any>`): Configuración para el contenedor (e.g., `{ "columns": 3 }`).
    -   `widgets` (`Widget[]`): Array de widgets a renderizar.
        -   `id` (`string`): ID único del widget.
        -   `component` (`string`): Nombre del componente React a usar (`DataTable`, `FormGenerator`, etc.).
        -   `config` (`Record<string, any>`): La configuración específica para ese widget.

## 3. Configuración de Widgets

### 3.1. `DataTable`

-   **`config` para un widget `DataTable`**:
    -   `api.url` (`string`): Endpoint para obtener los datos de la tabla.
    -   `columns` (`ColumnDefinition[]`): Definición de las columnas.
        -   `key` (`string`): Clave en el objeto de datos.
        -   `header` (`string`): Título de la columna.
        -   `dataType` (`'string' | 'number' | 'date' | ...`): Tipo de dato.
        -   `sortable`, `filterable` (`boolean`, opcional).
    -   `pagination` (opcional): Configuración de la paginación.

### 3.2. `FormGenerator`

-   **`config` para un widget `FormGenerator`**:
    -   `fields` (`FormField[]`): Array de campos del formulario.
        -   `name`, `label`, `type` (`string`).
        -   `validation` (`ValidationRule[]`, opcional): Reglas de validación.
            -   `type`: `'required'`, `'minLength'`, etc.
            -   `value`: Valor para la regla.
            -   `message`: Mensaje de error.
    -   `submitUrl` (`string`): Endpoint para enviar los datos.
    -   `submitMethod` (`'POST' | 'PUT'`).

## 4. Flujo de Renderizado

1.  El frontend se carga y llama a `GET /api/config`.
2.  Con la respuesta, renderiza la barra de navegación principal.
3.  El usuario navega a una ruta, por ejemplo `/page/dashboard`.
4.  El frontend extrae `dashboard` de la URL y llama a `GET /api/layouts/dashboard`.
5.  Con la configuración del layout, el componente `DynamicLayout` renderiza los widgets especificados (`DataTable`, `FormGenerator`, etc.), pasando a cada uno su `config` correspondiente.
6.  Cada widget es responsable de obtener sus propios datos si es necesario (e.g., el `DataTable` llama a la URL especificada en su `config.api.url`).