import React from "react";
import { PageLayout, Widget } from "../types/api.types";
import DataTable from "./DataTable";
import FormGenerator from "./FormGenerator";

// Registro de widgets disponibles. En una aplicación real, esto podría ser más dinámico.
const widgetRegistry: Record<string, React.ComponentType<any>> = {
  DataTable: DataTable,
  FormGenerator: FormGenerator,
  // Añadir aquí otros componentes de widget
};

interface DynamicLayoutProps {
  layoutConfig: PageLayout;
}

const DynamicLayout: React.FC<DynamicLayoutProps> = ({ layoutConfig }) => {
  if (!layoutConfig) {
    return <div>Cargando layout...</div>;
  }

  const { type, layoutConfig: gridConfig, widgets } = layoutConfig;

  const renderWidget = (widget: Widget) => {
    const WidgetComponent = widgetRegistry[widget.component];
    if (!WidgetComponent) {
      console.error(`Widget no encontrado en el registro: ${widget.component}`);
      return (
        <div key={widget.id}>Widget no encontrado: {widget.component}</div>
      );
    }
    // Pasamos la configuración específica del widget como props al componente
    return <WidgetComponent key={widget.id} {...widget.config} />;
  };

  // Renderiza el layout basado en el tipo
  switch (type) {
    case "grid":
      const gridStyles = {
        display: "grid",
        gridTemplateColumns: `repeat(${gridConfig.columns || 1}, 1fr)`,
        gap: `${gridConfig.gap || 4}px`,
      };
      return <div style={gridStyles}>{widgets.map(renderWidget)}</div>;
    // Añadir más casos para otros tipos de layout (flex, tabs, etc.)
    default:
      return <div>{widgets.map(renderWidget)}</div>;
  }
};

export default DynamicLayout;
