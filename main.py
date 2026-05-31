import network
import socket
import time
import dht
import ssd1306
from machine import Pin, PWM, I2C, ADC
from umqtt.simple import MQTTClient

USUARIO_ID = "victor_smarko_iot"
MQTT_BROKER = "broker.hivemq.com"
MQTT_CLIENT_ID = f"esp32_{USUARIO_ID}"
MQTT_TOPIC_TELEMETRIA = f"iot/casa/{USUARIO_ID}/sensores"
MQTT_TOPIC_CMD_LED1 = f"iot/casa/{USUARIO_ID}/comando/led_sala"
MQTT_TOPIC_CMD_LED2 = f"iot/casa/{USUARIO_ID}/comando/led_quarto"
MQTT_TOPIC_CMD_PORTA = f"iot/casa/{USUARIO_ID}/comando/porta"
MQTT_TOPIC_CMD_ALARM = f"iot/casa/{USUARIO_ID}/comando/alarme"

sensor_dht = dht.DHT22(Pin(27))
ldr_adc = ADC(Pin(34))
ldr_adc.atten(ADC.ATTN_11DB)
sensor_pir = Pin(13, Pin.IN)
ultrassonico_trig = Pin(12, Pin.OUT)
ultrassonico_echo = Pin(14, Pin.IN)

led_sala = Pin(2, Pin.OUT)
led_quarto = Pin(4, Pin.OUT)
buzzer = Pin(5, Pin.OUT)
porta_servo = PWM(Pin(18), freq=50)

try:
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
except:
    oled = None

estado_porta = False
estado_alarme = False

def ler_distancia():
    ultrassonico_trig.value(0)
    time.sleep_us(2)
    ultrassonico_trig.value(1)
    time.sleep_us(10)
    ultrassonico_trig.value(0)
    try:
        duracao = time.pulse_with_timeout(ultrassonico_echo, 1, 30000)
        return int((duracao * 0.0343) / 2)
    except:
        return 0

def controlar_porta(abrir):
    global estado_porta
    estado_porta = abrir
    porta_servo.duty(115 if abrir else 40)

def controlar_alarme(ativar):
    global estado_alarme
    estado_alarme = ativar
    buzzer.value(ativar)

def conecta_wifi():
    print("📡 Conectando WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Wokwi-GUEST')
    while not wlan.isconnected():
        time.sleep(0.5)
    ip = wlan.ifconfig()[0]
    print(f"✅ WiFi: {ip}")
    return ip

def mqtt_callback(topic, msg):
    topico_str = topic.decode('utf-8')
    mensagem_str = msg.decode('utf-8')
    if topico_str == MQTT_TOPIC_CMD_LED1:
        led_sala.value(1 if mensagem_str == "ON" else 0)
        print(f"LED Sala: {mensagem_str}")
    elif topico_str == MQTT_TOPIC_CMD_LED2:
        led_quarto.value(1 if mensagem_str == "ON" else 0)
        print(f"LED Quarto: {mensagem_str}")
    elif topico_str == MQTT_TOPIC_CMD_PORTA:
        controlar_porta(True if mensagem_str == "ABRIR" else False)
        print(f"Porta: {mensagem_str}")
    elif topico_str == MQTT_TOPIC_CMD_ALARM:
        controlar_alarme(True if mensagem_str == "ATIVAR" else False)
        print(f"Alarme: {mensagem_str}")

def conecta_mqtt():
    print("🔌 Conectando MQTT...")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC_CMD_LED1)
    client.subscribe(MQTT_TOPIC_CMD_LED2)
    client.subscribe(MQTT_TOPIC_CMD_PORTA)
    client.subscribe(MQTT_TOPIC_CMD_ALARM)
    print(" MQTT Conectado!")
    return client

print(" Iniciando Sistema IoT Smarko...")

ip_wlan = conecta_wifi()

web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
web_socket.bind(('', 80))
web_socket.listen(5)
web_socket.setblocking(False)

try:
    mqtt_client = conecta_mqtt()
except Exception as e:
    print(f" Erro MQTT: {e}")
    mqtt_client = None

tempo_anterior_publicacao = 0
tempo_anterior_oled = 0
tempo_anterior_dht = 0
controlar_porta(False)

val_temp = 0
val_umid = 0

while True:
    tempo_atual = time.time()
    
    # Ler DHT a cada 5 segundos (para evitar timeout)
    if tempo_atual - tempo_anterior_dht >= 5:
        try:
            sensor_dht.measure()
            time.sleep(1)
            val_temp = sensor_dht.temperature()
            val_umid = sensor_dht.humidity()
            print(f" DHT: {val_temp}°C {val_umid}%")
        except Exception as e:
            print(f" Erro DHT: {e}")
        tempo_anterior_dht = tempo_atual
        
    val_ldr = ldr_adc.read()
    val_pir = sensor_pir.value()
    val_dist = ler_distancia()

    if oled and (tempo_atual - tempo_anterior_oled > 2):
        try:
            oled.fill(0)
            oled.text(f"IP:{ip_wlan}", 0, 0)
            oled.text(f"T:{val_temp}C U:{val_umid}%", 0, 27)
            oled.text(f"L:{val_ldr} P:{val_pir} D:{val_dist}", 0, 30)
            oled.text(f"S1:{led_sala.value()} S2:{led_quarto.value()}", 0, 45)
            oled.text(f"P:{estado_porta} A:{estado_alarme}", 0, 56)
            oled.show()
        except:
            pass
        tempo_anterior_oled = tempo_atual

    if mqtt_client:
        try:
            mqtt_client.check_msg()
        except:
            pass

    if mqtt_client and (tempo_atual - tempo_anterior_publicacao > 10):
        payload = f'{{"temp":{val_temp},"umid":{val_umid},"ldr":{val_ldr},"pir":{val_pir},"dist":{val_dist}}}'
        try:
            mqtt_client.publish(MQTT_TOPIC_TELEMETRIA, payload)
            print(f" Publicado: {payload}")
        except Exception as e:
            print(f" Erro ao publicar: {e}")
        tempo_anterior_publicacao = tempo_atual

    try:
        conn, addr = web_socket.accept()
        conn.settimeout(0.5)
        try:
            request = conn.recv(1024).decode('utf-8')
            if '/?led1=toggle' in request:
                led_sala.value(not led_sala.value())
            elif '/?led2=toggle' in request:
                led_quarto.value(not led_quarto.value())
            elif '/?porta=toggle' in request:
                controlar_porta(not estado_porta)
            elif '/?alarme=toggle' in request:
                controlar_alarme(not estado_alarme)
            
            html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>IoT Smarko</title></head>
<body style="font-family: Arial; text-align: center; margin-top: 50px;">
<h1>Painel de Controlo ESP32</h1>
<div style="margin-bottom: 30px;">
<p><strong>Temperatura:</strong> {val_temp:.1f}C | <strong>Humidade:</strong> {val_umid:.1f}%</p>
<p><strong>LDR:</strong> {val_ldr} | <strong>PIR:</strong> {val_pir} | <strong>Distância:</strong> {val_dist}cm</p>
</div>
<div>
<a href="/?led1=toggle"><button style="padding:15px; margin:5px; width: 200px;">Luz Sala: {led_sala.value()}</button></a>
<a href="/?led2=toggle"><button style="padding:15px; margin:5px; width: 200px;">Luz Quarto: {led_quarto.value()}</button></a><br><br>
<a href="/?porta=toggle"><button style="padding:15px; margin:5px; width: 200px;">Porta: {estado_porta}</button></a>
<a href="/?alarme=toggle"><button style="padding:15px; margin:5px; width: 200px;">Alarme: {estado_alarme}</button></a>
</div>
</body>
</html>
"""
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\nAccess-Control-Allow-Origin: *\n\n')
            conn.sendall(html)
        except:
            pass
        finally:
            conn.close()
    except OSError:
        pass

    time.sleep(0.05)