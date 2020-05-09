#include <ESP8266WiFi.h> 
#include <PubSubClient.h>  

const char* ssid = "022696";
const char* password = TODO;
const char* mqtt_broker = "lennyspi.local";
const int mqtt_broker_port = 8883;

const char* mqtt_battery_topic = "mqtt/door_sensor/status/battery";
const char* mqtt_door_topic = "room/data/door";

const int buff_len = 20;
char buffer[buff_len];


WiFiClient espClient;
PubSubClient client(espClient);

ADC_MODE(ADC_VCC);

void setup_wifi() {

    delay(10);
    // We start by connecting to a WiFi network
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        //led_blink(500, 250);
        Serial.print(".");
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        delay(250);
    }
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    
    randomSeed(micros());
}


void setup() {
    pinMode(LED_BUILTIN, OUTPUT);     // Initialize the BUILTIN_LED pin as an output
    Serial.begin(115200);
    setup_wifi();
    client.setServer(mqtt_broker, mqtt_broker_port);
}

void loop() {
    int vcc = ESP.getVcc();
    Serial.println(vcc);
    String str = String(vcc);
    str.toCharArray(buffer, buff_len); 
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        // Create a random client ID
        String clientId = "Door-Sensor-";
        clientId += String(random(0xffff), HEX);
        // Attempt to connect
        if (client.connect(clientId.c_str(), mqtt_door_topic, 0, true, "closed")) {
            Serial.println("connected");
            delay(50);
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            // Wait 5 seconds before retrying
            for (int i = 0; i < 5; i++) {
              delay(1000);
              digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
            }
            digitalWrite(LED_BUILTIN, LOW);
        }
    }
    if (client.publish(mqtt_door_topic, "open", true))
        Serial.println("published");
    delay(50);
    if (client.publish(mqtt_battery_topic, buffer, true))
        Serial.println("published");

    delay(50);
    Serial.println("Going to sleep.");
    ESP.deepSleep(0);
}
