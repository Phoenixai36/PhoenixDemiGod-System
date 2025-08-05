// =================================================================
// Tipos Generales de la API
// =================================================================

/**
 * Respuesta genérica de la API para datos paginados.
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

// =================================================================
// Tipos para la Configuración de la UI
// =================================================================

/**
 * Define un elemento en el menú de navegación.
 */
export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon?: string; // Opcional: nombre de un icono a mostrar
  children?: NavigationItem[]; // Para submenús
}

/**
 * Configuración completa de la UI para la aplicación.
 * El backend enviará esto al iniciar la aplicación.
 */
export interface AppConfig {
  navigation: NavigationItem[];
  userPermissions: string[]; // Lista de permisos del usuario
}

// =================================================================
// Tipos para el Componente DataTable Dinámico
// =================================================================

/**
 * Define el tipo de dato de una columna.
 * Afecta al formato y a las opciones de filtro.
 */
export type ColumnDataType = 'string' | 'number' | 'date' | 'boolean' | 'custom';

/**
 * Define una columna para el DataTable.
 */
export interface ColumnDefinition {
  key: string; // La clave del objeto de datos
  header: string; // El texto a mostrar en la cabecera
  dataType: ColumnDataType;
  sortable?: boolean;
  filterable?: boolean;
  // Opcional: para renderizado personalizado de celdas
  customRender?: string; // Nombre de un componente de renderizado personalizado
}

/**
 * Configuración completa para un DataTable.
 */
export interface DataTableConfig {
  columns: ColumnDefinition[];
  // Opciones de paginación
  pagination?: {
    defaultPageSize: number;
    pageSizeOptions: number[];
  };
}

// =================================================================
// Tipos para el Componente FormGenerator Dinámico
// =================================================================

/**
 * Tipos de campos de formulario soportados.
 */
export type FormFieldType = 'text' | 'password' | 'number' | 'select' | 'checkbox' | 'date' | 'textarea';

/**
 * Regla de validación para un campo de formulario.
 */
export interface ValidationRule {
  type: 'required' | 'minLength' | 'maxLength' | 'regex' | 'min' | 'max';
  value?: any; // El valor para la regla (e.g., 8 para minLength)
  message: string; // Mensaje de error
}

/**
 * Define una opción para campos 'select'.
 */
export interface SelectOption {
  value: string | number;
  label: string;
}

/**
 * Define un campo individual en un formulario.
 */
export interface FormField {
  name: string; // Corresponde a la clave en el objeto de datos del formulario
  label: string;
  type: FormFieldType;
  placeholder?: string;
  defaultValue?: any;
  options?: SelectOption[]; // Para tipo 'select'
  validation?: ValidationRule[];
}

/**

 * Configuración completa para un Formulario.
 */
export interface FormConfig {
  fields: FormField[];
  submitUrl: string; // Endpoint de la API para enviar el formulario
  submitMethod: 'POST' | 'PUT';
}

// =================================================================
// Tipos para el Layout/Dashboard Dinámico
// =================================================================

/**
 * Define un widget que se puede renderizar en un layout.
 */
export interface Widget {
  id: string;
  /**
   * El nombre del componente React a renderizar.
   * El frontend debe tener un mapeo de estos nombres a los componentes reales.
   * E.g., 'DataTableWidget', 'SummaryChartWidget', 'RecentActivityWidget'
   */
  component: string;
  /**
   * Configuración específica para este widget.
   * La estructura de este objeto dependerá del tipo de componente.
   * Por ejemplo, para un 'DataTableWidget', esto podría ser un DataTableConfig.
   */
  config: Record<string, any>;
}

/**
 * Define la estructura de un layout de página.
 */
export interface PageLayout {
  /**
   * Define el tipo de contenedor del layout.
   * E.g., 'grid', 'flex', 'tabs'
   */
  type: 'grid' | 'flex' | 'tabs';
  /**
   * Configuración específica para el layout.
   * E.g., para 'grid', podría ser { columns: 3, gap: 4 }
   */
  layoutConfig: Record<string, any>;
  widgets: Widget[];
}