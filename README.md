# 🏠 Projeto Smarko Home - IoT & Automação Residencial

![Status](https://img.shields.io/badge/Status-Concluído-success)
![MicroPython](https://img.shields.io/badge/MicroPython-1.28.0-blue)
![ESP32](https://img.shields.io/badge/Hardware-ESP32-black)
![MQTT](https://img.shields.io/badge/Protocolo-MQTT-orange)

O **Projeto Smarko** é um sistema completo de automação residencial inteligente (IoT) desenvolvido em MicroPython para o microcontrolador ESP32. O ecossistema integra a leitura de sensores em tempo real, controle bidirecional de atuadores, dashboard web auto-hospedado (via WebSockets) e telemetria na nuvem.

## 🚀 Arquitetura e Tecnologias

O sistema foi desenhado com foco em processamento assíncrono não-bloqueante na borda (Edge Computing) e integração de serviços em nuvem:

* **Hardware Base:** ESP32 (Simulado via Wokwi).
* **Firmware:** MicroPython (Gerenciamento de rede, I2C, PWM, ADC e WebSockets).
* **Comunicação:** Protocolo MQTT (HiveMQ) e HTTP/WebSockets.
* **Interface Local:** Dashboard responsivo (HTML5/CSS3/JS) consumindo dados em tempo real.
* **Orquestração na Nuvem:** Node-RED para recepção de tópicos MQTT.
* **Persistência e Alertas:** Integração com Google Sheets (via Google Apps Script) para registro de histórico e notificação por e-mail.

## 📡 Sensores e Atuadores

O ambiente monitora e controla independentemente os seguintes componentes físicos:

**Sensores (Entradas):**
* `DHT22`: Temperatura (°C) e Umidade (%).
* `LDR`: Fotorresistor para medição de intensidade luminosa (LUX).
* `PIR`: Sensor infravermelho de detecção de movimento.
* `HC-SR04`: Sensor ultrassônico para medição de distância.

**Atuadores (Saídas):**
* `LEDs`: Indicadores de iluminação (Sala e Quarto).
* `Servomotor`: Controle de tranca da porta principal via sinal PWM.
* `Buzzer`: Sirene do sistema de alarme.
* `Display OLED (SSD1306)`: Interface física I2C exibindo IP, status da rede e telemetria local.

## ⚙️ Como Executar o Projeto

1. Clone este repositório:
   ```bash
   git clone [https://github.com/fozato/Projeto-Smarko-IOT.git](https://github.com/fozato/Projeto-Smarko-IOT.git)
