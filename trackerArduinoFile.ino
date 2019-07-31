#define LED 2

int incomingByte = 0;

void setup() {
    pinMode(LED, OUTPUT);

    Serial.begin(500000);
}

void loop(){
    while(Serial.available() > 0 ){

    incomingByte = Serial.read();

    if(incomingByte == 48) 
        digitalWrite(LED, LOW);
    else if(incomingByte == 49)
        digitalWrite(LED, HIGH);
    else
        Serial.println("Unidentified command!");
    }
}