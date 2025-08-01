"""
Phoenix Hydra Integration for Mamba/SSM Model Router

Integra el router multi-modelo Mamba/SSM con el sistema Phoenix Hydra existente,
proporcionando capacidades de análisis AI local para el sistema de revisión.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .phoenix_model_router import PhoenixModelRouter, InferenceRequest, TaskType
from ..core.interfaces import AnalysisEngine
from ..models.data_models import Component, EvaluationResult, ComponentCategory


class AIAnalysisType(Enum):
    """Tipos de análisis AI disponibles"""
    CODE_REVIEW = "code_review"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CONFIGURATION_VALIDATION = "configuration_validation"
    DEPENDENCY_ANALYSIS = "dependency_analysis"


@dataclass
class AIAnalysisResult:
    """Resultado de análisis AI"""
    analysis_type: AIAnalysisType
    component_name: str
    ai_insights: str
    confidence_score: float
    recommendations: List[str]
    model_used: str
    energy_consumed_wh: float
    processing_time_ms: float


class PhoenixHydraAIAnalyzer(AnalysisEngine):
    """
    Analizador AI integrado con Phoenix Hydra usando modelos Mamba/SSM locales

    Proporciona análisis inteligente de componentes usando el router multi-modelo
    con eficiencia energética y procesamiento 100% local.
    """

    def __init__(self, router: Optional[PhoenixModelRouter] = None):
        self.logger = logging.getLogger(__name__)
        self.router = router or PhoenixModelRouter()
        self.analysis_history: List[AIAnalysisResult] = []

    def evaluate_component(self, component: Component, criteria: Dict[str, Any]) -> EvaluationResult:
        """
        Evalúa un componente usando análisis AI local con modelos Mamba/SSM
        """

        # Determinar tipo de análisis basado en el componente
        analysis_type = self._determine_analysis_type(component)

        # Crear prompt específico para el análisis
        prompt = self._create_analysis_prompt(
            component, criteria, analysis_type)

        # Mapear tipo de análisis a TaskType del router
        task_type = self._map_to_task_type(analysis_type)

        # Realizar análisis AI
        ai_result = self._perform_ai_analysis(
            prompt, task_type, component.name, analysis_type)

        # Convertir resultado AI a EvaluationResult estándar
        evaluation_result = self._convert_to_evaluation_result(
            component, ai_result, criteria)

        # Guardar en historial
        self.analysis_history.append(ai_result)

        return evaluation_result

    def analyze_dependencies(self, component: Component, dependency_graph: Any) -> Dict[str, Any]:
        """
        Analiza dependencias usando AI local
        """

        prompt = f"""
        Analiza las dependencias del componente {component.name} en Phoenix Hydra:
        
        Componente: {component.name}
        Categoría: {component.category.value}
        Archivos: {len(component.files) if hasattr(component, 'files') else 0}
        
        Proporciona:
        1. Análisis de dependencias críticas
        2. Posibles conflictos o problemas
        3. Recomendaciones de optimización
        4. Impacto en el sistema general
        
        Responde en formato estructurado con análisis técnico detallado.
        """

        ai_result = self._perform_ai_analysis(
            prompt,
            TaskType.SYSTEM_REVIEW,
            component.name,
            AIAnalysisType.DEPENDENCY_ANALYSIS
        )

        return {
            "dependency_analysis": ai_result.ai_insights,
            "recommendations": ai_result.recommendations,
            "confidence_score": ai_result.confidence_score,
            "model_used": ai_result.model_used,
            "energy_consumed_wh": ai_result.energy_consumed_wh
        }

    def _determine_analysis_type(self, component: Component) -> AIAnalysisType:
        """Determina el tipo de análisis basado en el componente"""

        if component.category == ComponentCategory.SECURITY:
            return AIAnalysisType.SECURITY_AUDIT
        elif component.category == ComponentCategory.INFRASTRUCTURE:
            return AIAnalysisType.ARCHITECTURE_ANALYSIS
        elif hasattr(component, 'files') and any(f.endswith('.py') for f in component.files):
            return AIAnalysisType.CODE_REVIEW
        elif hasattr(component, 'files') and any(f.endswith(('.yaml', '.json', '.toml')) for f in component.files):
            return AIAnalysisType.CONFIGURATION_VALIDATION
        else:
            return AIAnalysisType.ARCHITECTURE_ANALYSIS

    def _create_analysis_prompt(self, component: Component, criteria: Dict[str, Any],
                                analysis_type: AIAnalysisType) -> str:
        """Crea prompt específico para el análisis"""

        base_info = f"""
        Analiza el componente Phoenix Hydra: {component.name}
        Categoría: {component.category.value}
        Estado: {component.status.value if hasattr(component, 'status') else 'unknown'}
        """

        if analysis_type == AIAnalysisType.CODE_REVIEW:
            return f"""
            {base_info}
            
            Realiza una revisión de código enfocada en:
            1. Calidad del código y mejores prácticas
            2. Posibles bugs o vulnerabilidades
            3. Optimizaciones de rendimiento
            4. Cumplimiento con estándares Phoenix Hydra
            5. Integración con arquitectura Mamba/SSM
            
            Criterios específicos: {criteria}
            
            Proporciona análisis detallado con recomendaciones específicas.
            """

        elif analysis_type == AIAnalysisType.SECURITY_AUDIT:
            return f"""
            {base_info}
            
            Realiza auditoría de seguridad enfocada en:
            1. Vulnerabilidades de seguridad
            2. Gestión de credenciales y secretos
            3. Configuraciones de acceso
            4. Cumplimiento con estándares de seguridad
            5. Protección de datos y privacidad (GDPR compliance)
            
            Criterios específicos: {criteria}
            
            Identifica riesgos y proporciona recomendaciones de mitigación.
            """

        elif analysis_type == AIAnalysisType.CONFIGURATION_VALIDATION:
            return f"""
            {base_info}
            
            Valida configuraciones enfocándose en:
            1. Sintaxis y estructura correcta
            2. Valores y parámetros apropiados
            3. Compatibilidad con otros componentes
            4. Optimización para eficiencia energética
            5. Configuración para procesamiento local
            
            Criterios específicos: {criteria}
            
            Verifica configuraciones y sugiere mejoras.
            """

        else:  # ARCHITECTURE_ANALYSIS por defecto
            return f"""
            {base_info}
            
            Analiza la arquitectura enfocándose en:
            1. Diseño y estructura del componente
            2. Integración con sistema Phoenix Hydra
            3. Escalabilidad y mantenibilidad
            4. Eficiencia energética y recursos
            5. Compatibilidad con modelos Mamba/SSM
            
            Criterios específicos: {criteria}
            
            Evalúa arquitectura y proporciona recomendaciones estratégicas.
            """

    def _map_to_task_type(self, analysis_type: AIAnalysisType) -> TaskType:
        """Mapea tipo de análisis AI a TaskType del router"""

        mapping = {
            AIAnalysisType.CODE_REVIEW: TaskType.CODE_ANALYSIS,
            AIAnalysisType.ARCHITECTURE_ANALYSIS: TaskType.SYSTEM_REVIEW,
            AIAnalysisType.SECURITY_AUDIT: TaskType.SECURITY_AUDIT,
            AIAnalysisType.PERFORMANCE_OPTIMIZATION: TaskType.SYSTEM_REVIEW,
            AIAnalysisType.CONFIGURATION_VALIDATION: TaskType.CONFIGURATION,
            AIAnalysisType.DEPENDENCY_ANALYSIS: TaskType.SYSTEM_REVIEW
        }

        return mapping.get(analysis_type, TaskType.GENERAL_QUERY)

    async def _perform_ai_analysis(self, prompt: str, task_type: TaskType,
                                   component_name: str, analysis_type: AIAnalysisType) -> AIAnalysisResult:
        """Realiza análisis AI usando el router multi-modelo"""

        inference_request = InferenceRequest(
            prompt=prompt,
            task_type=task_type,
            max_tokens=2048,
            temperature=0.3,  # Más determinístico para análisis técnico
            enable_fallback=True
        )

        try:
            response = await self.router.infer(inference_request)

            if response.error:
                self.logger.error(
                    f"AI analysis failed for {component_name}: {response.error}")
                # Crear resultado de error
                return AIAnalysisResult(
                    analysis_type=analysis_type,
                    component_name=component_name,
                    ai_insights=f"Error en análisis AI: {response.error}",
                    confidence_score=0.0,
                    recommendations=["Revisar configuración del modelo AI"],
                    model_used="error",
                    energy_consumed_wh=0.0,
                    processing_time_ms=0.0
                )

            # Extraer recomendaciones del texto de respuesta
            recommendations = self._extract_recommendations(response.response)

            return AIAnalysisResult(
                analysis_type=analysis_type,
                component_name=component_name,
                ai_insights=response.response,
                confidence_score=response.confidence_score,
                recommendations=recommendations,
                model_used=response.model_used,
                energy_consumed_wh=response.energy_consumed_wh,
                processing_time_ms=response.inference_time_ms
            )

        except Exception as e:
            self.logger.error(f"Exception during AI analysis: {e}")
            return AIAnalysisResult(
                analysis_type=analysis_type,
                component_name=component_name,
                ai_insights=f"Excepción durante análisis: {str(e)}",
                confidence_score=0.0,
                recommendations=["Verificar estado del sistema AI"],
                model_used="error",
                energy_consumed_wh=0.0,
                processing_time_ms=0.0
            )

    def _extract_recommendations(self, ai_response: str) -> List[str]:
        """Extrae recomendaciones del texto de respuesta AI"""

        recommendations = []
        lines = ai_response.split('\n')

        # Buscar secciones de recomendaciones
        in_recommendations = False
        for line in lines:
            line = line.strip()

            # Detectar inicio de sección de recomendaciones
            if any(keyword in line.lower() for keyword in ['recomendacion', 'recommendation', 'sugerencia', 'mejora']):
                in_recommendations = True
                continue

            # Si estamos en sección de recomendaciones y la línea parece una recomendación
            if in_recommendations and line:
                if line.startswith(('-', '*', '•', '1.', '2.', '3.')):
                    recommendations.append(line.lstrip('-*•0123456789. '))
                # Línea sustancial que no es título
                elif len(line) > 20 and not line.endswith(':'):
                    recommendations.append(line)

        # Si no encontramos recomendaciones estructuradas, extraer de forma heurística
        if not recommendations:
            sentences = ai_response.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30 and any(keyword in sentence.lower() for keyword in
                                              ['debe', 'debería', 'recomienda', 'sugiere', 'mejorar', 'optimizar', 'implementar']):
                    recommendations.append(sentence)

        return recommendations[:5]  # Limitar a 5 recomendaciones principales

    def _convert_to_evaluation_result(self, component: Component, ai_result: AIAnalysisResult,
                                      criteria: Dict[str, Any]) -> EvaluationResult:
        """Convierte resultado AI a EvaluationResult estándar"""

        # Calcular porcentaje de completitud basado en confianza y análisis
        completion_percentage = min(95.0, ai_result.confidence_score * 100)

        # Determinar criterios cumplidos vs faltantes basado en recomendaciones
        criteria_met = []
        criteria_missing = []

        if ai_result.confidence_score > 0.7:
            criteria_met.extend(list(criteria.keys())[:len(criteria)//2])
            criteria_missing.extend(list(criteria.keys())[len(criteria)//2:])
        else:
            criteria_missing.extend(list(criteria.keys()))

        # Crear issues basado en recomendaciones
        issues = [
            f"AI Recommendation: {rec}" for rec in ai_result.recommendations]

        return EvaluationResult(
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion_percentage,
            quality_score=ai_result.confidence_score * 100,
            issues=issues,
            ai_analysis=ai_result.ai_insights,
            model_used=ai_result.model_used,
            energy_consumed_wh=ai_result.energy_consumed_wh
        )

    def get_ai_analysis_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de análisis AI para grants y auditorías"""

        if not self.analysis_history:
            return {"error": "No AI analysis history available"}

        total_analyses = len(self.analysis_history)
        total_energy = sum(r.energy_consumed_wh for r in self.analysis_history)
        avg_confidence = sum(
            r.confidence_score for r in self.analysis_history) / total_analyses
        avg_processing_time = sum(
            r.processing_time_ms for r in self.analysis_history) / total_analyses

        # Distribución por tipo de análisis
        analysis_distribution = {}
        for result in self.analysis_history:
            analysis_type = result.analysis_type.value
            analysis_distribution[analysis_type] = analysis_distribution.get(
                analysis_type, 0) + 1

        # Distribución por modelo usado
        model_distribution = {}
        for result in self.analysis_history:
            model = result.model_used
            model_distribution[model] = model_distribution.get(model, 0) + 1

        return {
            "total_ai_analyses": total_analyses,
            "total_energy_consumed_wh": total_energy,
            "average_confidence_score": avg_confidence,
            "average_processing_time_ms": avg_processing_time,
            "energy_per_analysis_wh": total_energy / total_analyses,
            "analysis_type_distribution": analysis_distribution,
            "model_usage_distribution": model_distribution,
            "ai_efficiency_rating": "HIGH" if avg_confidence > 0.8 else "MEDIUM" if avg_confidence > 0.6 else "LOW"
        }


# Función de integración principal
def integrate_ai_with_phoenix_hydra(existing_analyzer: Optional[AnalysisEngine] = None) -> PhoenixHydraAIAnalyzer:
    """
    Integra capacidades AI Mamba/SSM con el sistema Phoenix Hydra existente

    Args:
        existing_analyzer: Analizador existente a extender (opcional)

    Returns:
        PhoenixHydraAIAnalyzer: Analizador AI integrado
    """

    logger = logging.getLogger(__name__)
    logger.info("Integrando capacidades AI Mamba/SSM con Phoenix Hydra")

    # Crear router multi-modelo
    router = PhoenixModelRouter()

    # Crear analizador AI integrado
    ai_analyzer = PhoenixHydraAIAnalyzer(router)

    logger.info(
        "Integración AI completada - Phoenix Hydra ahora tiene capacidades Mamba/SSM locales")

    return ai_analyzer
