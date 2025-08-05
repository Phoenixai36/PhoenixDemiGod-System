import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import DynamicLayout from "../components/DynamicLayout";
import apiService from "../services/apiService";
import { PageLayout } from "../types/api.types";

const GenericPage: React.FC = () => {
  const { pageName } = useParams<{ pageName: string }>();
  const [layoutConfig, setLayoutConfig] = useState<PageLayout | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLayout = async () => {
      try {
        setLoading(true);
        // En una aplicación real, el endpoint sería dinámico basado en la página
        const response = await apiService.get(`/layouts/${pageName}`);
        setLayoutConfig(response.data);
      } catch (err) {
        setError(`No se pudo cargar el layout para la página: ${pageName}`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (pageName) {
      fetchLayout();
    }
  }, [pageName]);

  if (loading) {
    return <div>Cargando página...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  if (!layoutConfig) {
    return <div>No se encontró la configuración del layout.</div>;
  }

  return <DynamicLayout layoutConfig={layoutConfig} />;
};

export default GenericPage;
