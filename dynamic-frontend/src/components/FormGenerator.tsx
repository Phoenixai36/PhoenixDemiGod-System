import React, { useState } from "react";
import apiService from "../services/apiService";
import { FormConfig, FormField } from "../types/api.types";

interface FormGeneratorProps {
  config: FormConfig;
}

const FormGenerator: React.FC<FormGeneratorProps> = ({ config }) => {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initialState: Record<string, any> = {};
    config.fields.forEach((field) => {
      initialState[field.name] = field.defaultValue || "";
    });
    return initialState;
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value, type } = e.target;
    const isCheckbox = type === "checkbox";
    // @ts-ignore
    const finalValue = isCheckbox ? e.target.checked : value;

    setFormData((prev) => ({
      ...prev,
      [name]: finalValue,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Lógica de validación aquí (simplificada por ahora)
    setErrors({});

    try {
      if (config.submitMethod === "POST") {
        await apiService.post(config.submitUrl, formData);
      } else {
        await apiService.put(config.submitUrl, formData);
      }
      alert("Formulario enviado con éxito");
    } catch (error) {
      console.error("Error al enviar el formulario:", error);
      alert("Error al enviar el formulario");
    }
  };

  const renderField = (field: FormField) => {
    const { name, label, type, placeholder, options } = field;

    switch (type) {
      case "select":
        return (
          <div key={name} className="mb-4">
            <label
              htmlFor={name}
              className="block text-sm font-medium text-gray-700"
            >
              {label}
            </label>
            <select
              id={name}
              name={name}
              value={formData[name]}
              onChange={handleChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        );
      case "textarea":
        return (
          <div key={name} className="mb-4">
            <label
              htmlFor={name}
              className="block text-sm font-medium text-gray-700"
            >
              {label}
            </label>
            <textarea
              id={name}
              name={name}
              placeholder={placeholder}
              value={formData[name]}
              onChange={handleChange}
              className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        );
      // Añadir más casos para otros tipos de input (checkbox, date, etc.)
      default:
        return (
          <div key={name} className="mb-4">
            <label
              htmlFor={name}
              className="block text-sm font-medium text-gray-700"
            >
              {label}
            </label>
            <input
              type={type}
              id={name}
              name={name}
              placeholder={placeholder}
              value={formData[name]}
              onChange={handleChange}
              className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-white shadow-md rounded-lg">
      {config.fields.map(renderField)}
      <button
        type="submit"
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        Enviar
      </button>
    </form>
  );
};

export default FormGenerator;
