import React from "react";
import { DataTableConfig } from "../types/api.types";

interface DataTableProps {
  config: DataTableConfig;
  data: any[];
}

const DataTable: React.FC<DataTableProps> = ({ config, data }) => {
  if (!config || !data) {
    return <div>Cargando datos de la tabla...</div>;
  }

  const { columns } = config;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((col) => (
                <td
                  key={col.key}
                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-700"
                >
                  {/* Aquí se podría añadir lógica para el customRender */}
                  {row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {/* Aquí se podría añadir la lógica de paginación */}
    </div>
  );
};

export default DataTable;
