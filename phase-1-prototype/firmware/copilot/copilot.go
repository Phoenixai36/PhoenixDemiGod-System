package main

// Lógica de Copilotaje en TinyGo (compilado a WASM3)
// Este código define la lógica de negocio principal de la célula.
// Se compila a un módulo WebAssembly (WASM) que es ejecutado por el runtime del SoC.

// La directiva 'export' hace que la función sea visible desde fuera del módulo WASM,
// permitiendo que el firmware principal la invoque.

// process_sensor_data es la función principal que reacciona a las lecturas de los sensores.
//export process_sensor_data
func process_sensor_data(sensor_id uint32, value float32) uint32 {
    switch sensor_id {
    case 0: // Sensor de CO2
        if value > 1200.0 {
            // Si el CO2 supera 1200 ppm, activar el ventilador al 80%
            return actuate_fan(80)
        }
    case 1: // Sensor de Temperatura
        if value > 35.0 {
            // Si la temperatura supera los 35°C, activar la refrigeración al 100%
            return actuate_cooling(100)
        }
    }
    return 0 // No se requiere ninguna acción
}

// actuate_fan es una función exportada que interactúa con el hardware (simulado).
// En un caso real, esta función sería importada desde el host del firmware.
//export actuate_fan
func actuate_fan(power uint32) uint32 {
    // Aquí iría la lógica para controlar un pin PWM que maneja un ventilador.
    // Por ahora, es un placeholder.
    // Devolvemos 1 para indicar éxito.
    return 1
}

// actuate_cooling es otro ejemplo de función de actuación.
//export actuate_cooling
func actuate_cooling(power uint32) uint32 {
    // Lógica para activar un sistema de refrigeración.
    return 1 // Success
}

// La función main es requerida por el compilador de Go, pero en un contexto WASM
// a menudo permanece vacía, ya que la ejecución es controlada por las funciones exportadas.
func main() {}