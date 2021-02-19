/*
  Example for receiving
  
  https://github.com/sui77/rc-switch/
  
  If you want to visualize a telegram copy the raw data and 
  paste it into http://test.sui.li/oszi/
*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <RCSwitch.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define SEALEVELPRESSURE_HPA (1013.25)

WiFiClient espClient;
PubSubClient client(espClient);

RCSwitch reciever = RCSwitch();
RCSwitch transmitter = RCSwitch();

Adafruit_BME280 bme;

const char* ssid = "No Internet Access";
const char* password = TODO;
const char* mqtt_broker = "192.168.178.202";
const char* mqtt_broker_wifi = "192.168.178.203";
const int mqtt_broker_port = 8883;

const char* mqtt_status_topic = "mqtt/esp_bme_rf/status";
const char* mqtt_bme_topic = "room/data";
const char* mqtt_recieve_topic = "room/data/rf/recieve";
const char* mqtt_transmit_topic = "room/data/rf/transmit";

String rf_data;
String bme_data;

const int char_buff_len = 150;
char char_buff[char_buff_len];

unsigned long previousMillis = 0;
const long interval = 60*1000;

int switch_state = 0;

unsigned long delayTime;
float temperature, humidity, pressure, altitude;

void setup_wifi() {

    delay(10);
    // We start by connecting to a WiFi network
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        delay(250);
    }
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(LED_BUILTIN, HIGH);
}


void setup_mqtt() {
    // Loop until we're reconnected
    bool wlan_client = false;
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection to host ");
        if (wlan_client == true) {
            Serial.print(mqtt_broker_wifi);
        }
        else {
            Serial.print(mqtt_broker);
        }
        Serial.print("...");
        // Create a random client ID
        String clientId = "Esp-bme-rf-";
        clientId += String(random(0xffff), HEX);
        // Attempt to connect
        if (client.connect(clientId.c_str(), mqtt_status_topic, 0, false, "offline")) {
            Serial.println("connected");
            // ... and resubscribe
            client.subscribe(mqtt_transmit_topic);
            
        } else {
            if (wlan_client == true) {
                client.setServer(mqtt_broker_wifi, mqtt_broker_port);
                wlan_client = false;
            }
            else {
                client.setServer(mqtt_broker, mqtt_broker_port);
                wlan_client = true;
            }
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            // Wait 5 seconds before retrying
            for (int i = 0; i < 5; i++) {
              delay(1000);
              digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
            }
            delay(100);
            // digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
            // delay(100);
            // digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
            // delay(100);
            // digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));

        }
    }
    // Once connected, publish an announcement...
    client.publish(mqtt_status_topic, "online", false);
    digitalWrite(LED_BUILTIN, HIGH);
}

/*
void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    String S_payload = "";
    for (unsigned int i = 0; i < length; i++) {
        S_payload += (char)payload[i];
    }
    int i_payload = S_payload.toInt();
    Serial.println(S_payload);
    Serial.println(i_payload);

    if (S_payload.toInt() != 0)
        transmitter.send(i_payload, length);
}
*/

void setup() {
    delay(10);
    pinMode(LED_BUILTIN, OUTPUT);

    Serial.begin(115200);
    randomSeed(micros());

    client.setServer(mqtt_broker, mqtt_broker_port);
    //client.setCallback(callback);

    setup_wifi();
    setup_mqtt();
    //client.loop();

    // setup bme i2c
    bme.begin(0x76);

    // setup reciever on pin 0 and transmitter on pin 1
    reciever.enableReceive(0);
    //transmitter.enableTransmit(2);
    //transmitter.setProtocol(1, 500);
}


void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        setup_wifi();
        setup_mqtt();
    }
    if (!client.loop()) {
        setup_mqtt();
    }

    if (reciever.available()) {
        output(
            reciever.getReceivedValue(),
            reciever.getReceivedBitlength(),
            reciever.getReceivedDelay(),
            reciever.getReceivedProtocol()
        );
        rf_data = get_rf_string(
            reciever.getReceivedValue(),
            reciever.getReceivedBitlength(),
            reciever.getReceivedDelay(),
            reciever.getReceivedProtocol()
        );
        if (rf_data != "{}")
        rf_data.toCharArray(char_buff, char_buff_len);
            client.publish(mqtt_recieve_topic, char_buff);
        reciever.resetAvailable();
    }

    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
        // save the last time you blinked the LED
        previousMillis = currentMillis;

        bme_data = get_bme_data(
            bme.readTemperature(),
            bme.readHumidity(),
            bme.readPressure(),
            bme.readAltitude(SEALEVELPRESSURE_HPA)
        );
        bme_data.toCharArray(char_buff, char_buff_len);
        client.publish(mqtt_bme_topic, char_buff);
    }
}
