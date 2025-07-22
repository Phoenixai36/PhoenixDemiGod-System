# cyberglitch_bridge.py
# Ubicación: src/integration/cyberglitch_bridge.py

import os
import time
import json
import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Importaciones simuladas para interfaces externas
# En producción, reemplazar con las bibliotecas reales
class OSCClient:
    """Cliente OSC para comunicación con MPC One."""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        print(f"OSC Client initialized: {host}:{port}")
        
    def send_message(self, address: str, *args):
        """Envía mensaje OSC."""
        print(f"OSC message sent to {address}: {args}")
        
    def get_activity(self) -> Dict[str, float]:
        """Obtiene actividad MIDI actual."""
        return {
            "note_density": np.random.uniform(0.2, 0.8),
            "velocity_avg": np.random.uniform(60, 110),
            "cc_activity": np.random.uniform(0.0, 1.0)
        }


class AbletonLinkClient:
    """Cliente para Ableton Link."""
    def __init__(self, port: int):
        self.port = port
        print(f"Ableton Link Client initialized on port {port}")
        
    def get_tempo(self) -> float:
        """Obtiene tempo actual."""
        return np.random.uniform(120.0, 160.0)
    
    def get_audio_buffer(self) -> np.ndarray:
        """Obtiene buffer de audio actual."""
        # Simulación de buffer de audio (1 segundo a 44.1kHz)
        return np.random.uniform(-0.8, 0.8, 44100)
    
    def trigger_scene(self, scene_index: int):
        """Dispara escena en Ableton Live."""
        print(f"Triggered scene {scene_index} in Ableton Live")


class PhaseAnalyzer:
    """Analizador de fases musicales."""
    def __init__(self):
        self.phases = ["intro", "build-up", "drop", "breakdown", "outro"]
        self.current_phase = "intro"
        self.phase_history = []
        
    def analyze(self, audio_features: Dict[str, float], midi_activity: Dict[str, float]) -> str:
        """Analiza fase actual basada en características de audio y MIDI."""
        # Algoritmo simplificado para demostración
        energy = audio_features.get("rms", 0.5)
        note_density = midi_activity.get("note_density", 0.5)
        
        if energy < 0.3 and note_density < 0.3:
            self.current_phase = "intro" if len(self.phase_history) < 2 else "outro"
        elif energy < 0.5 and note_density > 0.6:
            self.current_phase = "build-up"
        elif energy > 0.7:
            self.current_phase = "drop"
        else:
            self.current_phase = "breakdown"
            
        self.phase_history.append(self.current_phase)
        if len(self.phase_history) > 20:
            self.phase_history.pop(0)
            
        return self.current_phase


class ChaosfrenesiDetector:
    """Detector de eventos Chaosfrenesi."""
    def __init__(self, probability: float = 0.05):
        self.probability = probability
        self.last_triggered = 0
        self.cooldown = 60  # segundos mínimos entre eventos
        
    def is_active(self) -> bool:
        """Determina si Chaosfrenesi está activo."""
        current_time = time.time()
        if current_time - self.last_triggered < self.cooldown:
            return False
            
        if np.random.random() < self.probability:
            self.last_triggered = current_time
            return True
            
        return False


@dataclass
class PerformanceData:
    """Estructura de datos para información de performance."""
    bpm: float
    phase: str
    midi_activity: Dict[str, float]
    audio_features: Dict[str, float]
    chaos_active: bool
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "bpm": self.bpm,
            "phase": self.phase,
            "midi_activity": self.midi_activity,
            "audio_features": self.audio_features,
            "chaos_active": self.chaos_active,
            "timestamp": self.timestamp
        }


class CyberglitchBridge:
    """Puente de integración entre Phoenix DemiGod y Cyberglitchcore SetLive."""
    
    def __init__(self, mpc_port: int = 3000, ableton_port: int = 9000):
        """Inicializa el puente de integración."""
        self.mpc_client = OSCClient("127.0.0.1", mpc_port)
        self.ableton_client = AbletonLinkClient(ableton_port)
        self.phase_analyzer = PhaseAnalyzer()
        self.chaosfrenesi_detector = ChaosfrenesiDetector(probability=0.05)
        
        # Configuración de directorios para datos
        self.data_dir = os.path.join(os.path.dirname(__file__), "../../data/performance")
        os.makedirs(self.data_dir, exist_ok=True)
        
        print("CyberglitchBridge initialized successfully")
        
    def capture_performance_data(self) -> PerformanceData:
        """Captura datos en tiempo real de la performance."""
        # Obtener datos de Ableton y MPC
        bpm = self.ableton_client.get_tempo()
        midi_activity = self.mpc_client.get_activity()
        audio_buffer = self.ableton_client.get_audio_buffer()
        
        # Extraer características de audio
        audio_features = self.extract_audio_features(audio_buffer)
        
        # Analizar fase actual
        phase = self.phase_analyzer.analyze(audio_features, midi_activity)
        
        # Verificar si Chaosfrenesi está activo
        chaos_active = self.chaosfrenesi_detector.is_active()
        
        # Crear objeto de datos de performance
        performance_data = PerformanceData(
            bpm=bpm,
            phase=phase,
            midi_activity=midi_activity,
            audio_features=audio_features,
            chaos_active=chaos_active
        )
        
        # Guardar datos para entrenamiento
        self._save_performance_data(performance_data)
        
        return performance_data
        
    def extract_audio_features(self, audio_buffer: np.ndarray) -> Dict[str, float]:
        """Extrae características del audio en tiempo real."""
        # Asegurar que el buffer tenga datos
        if len(audio_buffer) == 0:
            return {
                "rms": 0.0,
                "spectral_centroid": 0.0,
                "spectral_bandwidth": 0.0,
                "spectral_rolloff": 0.0,
                "zero_crossing_rate": 0.0
            }
        
        # Extraer características usando librosa
        try:
            # RMS (Root Mean Square) - energía
            rms = np.sqrt(np.mean(audio_buffer**2))
            
            # Características espectrales simplificadas para demostración
            # En producción, usar librosa.feature.* con ventanas apropiadas
            spectral_centroid = np.mean(np.abs(np.fft.rfft(audio_buffer)))
            spectral_bandwidth = np.std(np.abs(np.fft.rfft(audio_buffer)))
            spectral_rolloff = np.percentile(np.abs(np.fft.rfft(audio_buffer)), 85)
            zero_crossing_rate = np.mean(np.abs(np.diff(np.signbit(audio_buffer))))
            
            return {
                "rms": float(rms),
                "spectral_centroid": float(spectral_centroid),
                "spectral_bandwidth": float(spectral_bandwidth),
                "spectral_rolloff": float(spectral_rolloff),
                "zero_crossing_rate": float(zero_crossing_rate)
            }
        except Exception as e:
            print(f"Error extracting audio features: {e}")
            return {
                "rms": 0.0,
                "spectral_centroid": 0.0,
                "spectral_bandwidth": 0.0,
                "spectral_rolloff": 0.0,
                "zero_crossing_rate": 0.0
            }
    
    def trigger_avatar_mutation(self, mutation_type: str, intensity: float):
        """Dispara mutaciones de avatar basadas en decisiones de IA."""
        self.mpc_client.send_message("avatar/mutate", mutation_type, intensity)
        print(f"Avatar mutation triggered: {mutation_type} (intensity: {intensity})")
        
    def apply_ai_suggestion(self, suggestion_data: Dict[str, Any]):
        """Aplica sugerencias de Phoenix DemiGod a la performance en vivo."""
        suggestion_type = suggestion_data.get("type", "")
        
        if suggestion_type == "glitch":
            # Aplicar efecto glitch
            intensity = suggestion_data.get("intensity", 0.5)
            duration = suggestion_data.get("duration", 4.0)
            self.mpc_client.send_message("effect/glitch", intensity, duration)
            print(f"Applied glitch effect: intensity={intensity}, duration={duration}")
            
        elif suggestion_type == "transition":
            # Aplicar transición
            scene_index = suggestion_data.get("scene_index", 1)
            self.ableton_client.trigger_scene(scene_index)
            print(f"Triggered transition to scene {scene_index}")
            
        elif suggestion_type == "avatar":
            # Modificar avatar
            mutation = suggestion_data.get("mutation", "fractal")
            intensity = suggestion_data.get("intensity", 0.7)
            self.trigger_avatar_mutation(mutation, intensity)
            
        elif suggestion_type == "chaosfrenesi":
            # Forzar evento Chaosfrenesi
            if suggestion_data.get("force", False):
                self.mpc_client.send_message("system/chaosfrenesi", 1.0)
                print("Forced Chaosfrenesi event!")
                
        else:
            print(f"Unknown suggestion type: {suggestion_type}")
    
    def _save_performance_data(self, performance_data: PerformanceData):
        """Guarda datos de performance para entrenamiento futuro."""
        timestamp = int(performance_data.timestamp)
        filename = os.path.join(self.data_dir, f"performance_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(performance_data.to_dict(), f, indent=2)


def test_bridge():
    """Función de prueba para el puente CyberglitchBridge."""
    bridge = CyberglitchBridge()
    
    # Capturar datos de performance
    print("Capturing performance data...")
    performance_data = bridge.capture_performance_data()
    print(f"BPM: {performance_data.bpm}")
    print(f"Phase: {performance_data.phase}")
    print(f"Chaos active: {performance_data.chaos_active}")
    print(f"Audio features: {performance_data.audio_features}")
    
    # Probar mutación de avatar
    bridge.trigger_avatar_mutation("fractal", 0.8)
    
    # Probar aplicación de sugerencia
    suggestion = {
        "type": "transition",
        "scene_index": 2
    }
    bridge.apply_ai_suggestion(suggestion)
    
    print("Test completed successfully!")


if __name__ == "__main__":
    test_bridge()
