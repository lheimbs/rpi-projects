#include <RCSwitch.h>
RCSwitch mySwitch = RCSwitch();

const int INTERNAL_LED = 1;
const int EXTERNAL_LED = 4;

void setup() {
    mySwitch.enableReceive(0);  // Receiver on interrupt 0 => that is pin #2
    pinMode(INTERNAL_LED, OUTPUT);
    pinMode(EXTERNAL_LED, OUTPUT);

    digitalWrite(INTERNAL_LED, HIGH);
    delay(500);
    digitalWrite(INTERNAL_LED, LOW);
    delay(500);
}

void loop() {
    if (mySwitch.available()) {
        if (mySwitch.getReceivedValue() == 10000) {
            digitalWrite(EXTERNAL_LED,HIGH);
            digitalWrite(INTERNAL_LED, HIGH);
            delay(500);
            digitalWrite(INTERNAL_LED, LOW);
            digitalWrite(EXTERNAL_LED,LOW);
        }
        mySwitch.resetAvailable();
        delay(10);
    }
}
