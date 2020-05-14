static const char* bin2tristate(const char* bin);
static char * dec2binWzerofill(unsigned long Dec, unsigned int bitLength);


String get_bme_data(float temperature, float humidity, float pressure, float altitude) {
    temperature = temperature - 4.0f;
    pressure = pressure / 100.0F;

    String retVal = "{\"temperature\":";
    retVal += temperature;
    retVal += ",\"humidity\":";
    retVal += humidity;
    retVal += ",\"pressure\":";
    retVal += pressure;
    retVal += ",\"altitude\":";
    retVal += altitude;
    retVal += "}";

    Serial.println(retVal);
    return retVal;
}


String get_rf_string(unsigned long decimal, unsigned int length, unsigned int delay, unsigned int protocol) {
    String retVal = "{";
    if (decimal != 0) {
        const char* b = dec2binWzerofill(decimal, length);
        retVal += "\"decimal\":";
        retVal += decimal;
        
        retVal += ",\"length\":";
        retVal += length;
        
        retVal += ",\"binary\":\"";
        retVal += b;
        
        retVal += "\",\"pulse-length\":";
        retVal += delay;
        
        retVal += ",\"protocol\":";
        retVal += protocol;
    }
    retVal += "}";
    return retVal;
}


void output(unsigned long decimal, unsigned int length, unsigned int delay, unsigned int protocol) {
    if (decimal == 0) {
        Serial.print("Unknown encoding.");
    } else {
        const char* b = dec2binWzerofill(decimal, length);
        Serial.print("Decimal: ");
        Serial.print(decimal);
        Serial.print(" (");
        Serial.print( length );
        Serial.print("Bit) Binary: ");
        Serial.print( b );
        Serial.print(" Tri-State: ");
        Serial.print( bin2tristate( b) );
        Serial.print(" PulseLength: ");
        Serial.print(delay);
        Serial.print(" microseconds");
        Serial.print(" Protocol: ");
        Serial.println(protocol);
    }
      Serial.println();
      Serial.println();
}


static const char* bin2tristate(const char* bin) {
    static char returnValue[50];
    int pos = 0;
    int pos2 = 0;
    while (bin[pos]!='\0' && bin[pos+1]!='\0') {
        if (bin[pos]=='0' && bin[pos+1]=='0') {
            returnValue[pos2] = '0';
        } else if (bin[pos]=='1' && bin[pos+1]=='1') {
            returnValue[pos2] = '1';
        } else if (bin[pos]=='0' && bin[pos+1]=='1') {
            returnValue[pos2] = 'F';
        } else {
            return "not applicable";
        }
        pos = pos+2;
        pos2++;
    }
    returnValue[pos2] = '\0';
    return returnValue;
}


static char * dec2binWzerofill(unsigned long Dec, unsigned int bitLength) {
    static char bin[64]; 
    unsigned int i=0;
    
    while (Dec > 0) {
        bin[32+i++] = ((Dec & 1) > 0) ? '1' : '0';
        Dec = Dec >> 1;
    }
    
    for (unsigned int j = 0; j< bitLength; j++) {
        if (j >= bitLength - i) {
            bin[j] = bin[ 31 + i - (j - (bitLength - i)) ];
        } else {
            bin[j] = '0';
        }
    }
    bin[bitLength] = '\0';
    
    return bin;
}
