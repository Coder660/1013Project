from pymata4 import pymata4
import time

board = pymata4.Pymata4()

LDR_INPUT_PIN_1_ANALOG = 5

ser = 2
srclk = 3
rclk = 4
US5_TRIG_DIGITAL = 5
US5_ECHO_DIGITAL = 6

US1_TRIG_DIGITAL = 7
US1_ECHO_DIGITAL = 8

US2_TRIG_DIGITAL = 9
US2_ECHO_DIGITAL = 10


MAX_TIME_BETWEEN_US1_US2_DETECTIONS = 5
DETECTION_DISTANCE_MAX = 10

dayDetectedTimeAdd = True

trafficLightSequenceStarting1 =0
trafficLightSequenceRunning1 ={
    "Sequence0": False , 
    "Sequence1": False
}

trafficLightSequenceStarting2 =0
trafficLightSequenceRunning2 ={
    "Sequence0": False , 
    "Sequence1": False
}

trafficLightSequenceStarting6 = 0
trafficLightSequenceRunning6 ={
    "Sequence0": False , 
    "Sequence1": False
}

#Shift register will control TL6 (RED, YELLOW, GREEN) LEDS and FL1 and FL2

#TIMER_556_PIN_DIGITAL = 4

board.set_pin_mode_digital_output(ser)
board.set_pin_mode_digital_output(srclk)
board.set_pin_mode_digital_output(rclk)


def callback_LDR(data):
    global dayDetectedTimeAdd

    if(data[2] >= 800):
        dayDetectedTimeAdd = 5
    else:
        dayDetectedTimeAdd = 0



board.set_pin_mode_analog_input(LDR_INPUT_PIN_1_ANALOG,callback_LDR,50)

distanceUS5 = 0

last8US5Vals = []

def callback_US5(data):
    global distanceUS5
    global last8US5Vals

    last8US5Vals.append(data[2])
    while(len(last8US5Vals) > 8 ):
       last8US5Vals = last8US5Vals[-8:] 

    distanceUS5 = sum( last8US5Vals ) / len(last8US5Vals)

    #print(f"US5")

board.set_pin_mode_sonar(US5_TRIG_DIGITAL, US5_ECHO_DIGITAL, callback_US5)

time.sleep(0.5)

distanceUS1 = 0

last8US1Vals = []

def callback_US1(data):
    global distanceUS1
    global last8US1Vals

    last8US1Vals.append(data[2])
    while(len(last8US1Vals) > 8 ):
       last8US1Vals = last8US1Vals[-8:] 

    distanceUS1 = sum( last8US1Vals ) / len(last8US1Vals)

    if(distanceUS1 < DETECTION_DISTANCE_MAX ):
        print(f"distance: {data[2]}cm, time {time.localtime().tm_hour}:{time.localtime().tm_min}")


board.set_pin_mode_sonar(US1_TRIG_DIGITAL, US1_ECHO_DIGITAL, callback_US1)

time.sleep(0.5)

distanceUS2 = 0

last8US2Vals = []

def callback_US2(data):
    global distanceUS2
    global last8US2Vals

    last8US2Vals.append(data[2])
    while(len(last8US2Vals) > 8 ):
       last8US2Vals = last8US2Vals[-8:] 

    distanceUS2 = sum( last8US2Vals ) / len(last8US2Vals)


board.set_pin_mode_sonar(US2_TRIG_DIGITAL, US2_ECHO_DIGITAL, callback_US2)

time.sleep(0.5)




shiftRegisterStateStorage = [1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0]
# Qa RED_LED6, Qb YELLOW_LED6, Qc GREEN_LED6, Qd FL1, Qe FL2, Qf 555 timer subsystem 3, Qg RED_LED1, Qh YELLOW_LED1, 
# Qa GREEN_LED1, Qb RED_LED2, Qc YELLOW_LED2, Qd GREEN_LED2, Qe WL1.1, Qf WL1.2, Qg 555 timer subsystem 1, Qh Transistor subsystem 1


#print(shiftRegisterStateStorage)
#print(shiftRegisterStateStorageReversed)

board.digital_write(ser,0)
board.digital_write(srclk,0)
board.digital_write(rclk, 0)

def iterate_over_shift_register_array(arrayToIterate):
    for state in arrayToIterate:
        board.digital_write(ser, state)
        board.digital_write(srclk, 1)
        board.digital_write(srclk, 0)
        time.sleep(0.003)

    board.digital_write(rclk, 1)
    board.digital_write(rclk, 0)



def shift_register_change_state(outputToChange):


    shiftRegisterStateStorage[outputToChange] = 0 if shiftRegisterStateStorage[outputToChange] == 1 else 1

    iterate_over_shift_register_array(shiftRegisterStateStorage[::-1])





def traffic_light_sequence_6(sequenceToRun):
    global trafficLightSequenceStarting6
    global trafficLightSequenceRunning6

    #print(dayDetectedTimeAdd)
    match(sequenceToRun):
        case 0:
            if(trafficLightSequenceRunning6["Sequence0"] == False):
               # print("INIF1")
                trafficLightSequenceStarting6 = time.time()
                trafficLightSequenceRunning6["Sequence0"]  = True
                shift_register_change_state(2)
                shift_register_change_state(0)

                if(dayDetectedTimeAdd == 5):
                    shift_register_change_state(3)
                    shift_register_change_state(4)
        case 1:
            
            if(trafficLightSequenceRunning6["Sequence1"] == False):
                #print("INIF2")


                if(distanceUS5 < DETECTION_DISTANCE_MAX):
                    #print("Inwhile")
                    if(shiftRegisterStateStorage[2] == 1):
                        shift_register_change_state(2)
                    if(shiftRegisterStateStorage[5] == 0):
                        shift_register_change_state(5)

                    trafficLightSequenceStarting6 = time.time() - 5 - dayDetectedTimeAdd
                else:
                    trafficLightSequenceRunning6["Sequence1"] = True

                    if(shiftRegisterStateStorage[2] == 1):
                        shift_register_change_state(2)
            

                    if(shiftRegisterStateStorage[3] == 1 and shiftRegisterStateStorage[4] == 1):
                        shift_register_change_state(3)
                        shift_register_change_state(4)

                    if(shiftRegisterStateStorage[5] == 1):
                        shift_register_change_state(5)
                    
                    shift_register_change_state(1)

        case 2:
           # print("INIF3")

            shift_register_change_state(1)
            shift_register_change_state(0)
            trafficLightSequenceRunning6["Sequence0"] = False
            trafficLightSequenceRunning6["Sequence1"] = False
            trafficLightSequenceStarting6 =0
  

def detection_distance_input_handler():
    global DETECTION_DISTANCE_MAX

    DETECTION_DISTANCE_MAX = input("Enter overheight limit: ")
    if(DETECTION_DISTANCE_MAX.isdigit()):
        DETECTION_DISTANCE_MAX = int(DETECTION_DISTANCE_MAX)
    elif(DETECTION_DISTANCE_MAX.isdecimal()):
        DETECTION_DISTANCE_MAX = float(DETECTION_DISTANCE_MAX)
    else:
        DETECTION_DISTANCE_MAX = 10

def traffic_light_sequence_1(sequenceToRun):
    global trafficLightSequenceStarting1
    global trafficLightSequenceRunning1

    match(sequenceToRun):
        case 0:
            if(trafficLightSequenceRunning1["Sequence0"] == False):
                trafficLightSequenceStarting1 = time.time()  
                trafficLightSequenceRunning1["Sequence0"] = True
                shift_register_change_state(8)
                shift_register_change_state(7)
                if(shiftRegisterStateStorage[14] == 0):
                    shift_register_change_state(14)
        case 1:
            if(trafficLightSequenceRunning1["Sequence1"] == False):
                trafficLightSequenceRunning1["Sequence1"] = True
                shift_register_change_state(7)
                shift_register_change_state(6)
                    
        case 2:
            if(distanceUS2 < DETECTION_DISTANCE_MAX):
                if(shiftRegisterStateStorage[15] == 0):
                    shift_register_change_state(15)
                trafficLightSequenceStarting1 = time.time() - 31
            else:
                shift_register_change_state(6)
                shift_register_change_state(8)
                trafficLightSequenceStarting1 = 0     
                trafficLightSequenceRunning1["Sequence0"] = False
                trafficLightSequenceRunning1["Sequence1"] = False
            
 
def traffic_light_sequence_2(sequenceToRun):
    global trafficLightSequenceStarting2
    global trafficLightSequenceRunning2


    match(sequenceToRun):
        case 0:
            if(trafficLightSequenceRunning2["Sequence0"] == False):
                #print("Case1")
                trafficLightSequenceStarting2 = time.time()  
                trafficLightSequenceRunning2["Sequence0"] = True
                shift_register_change_state(11)
                shift_register_change_state(10)
                if(shiftRegisterStateStorage[14] == 0):
                    shift_register_change_state(14)
        case 1:
            if(trafficLightSequenceRunning2["Sequence1"] == False):
                #print("Case2")

                trafficLightSequenceRunning2["Sequence1"] = True
                shift_register_change_state(10)
                shift_register_change_state(9)
        case 2:
            if(distanceUS2 < DETECTION_DISTANCE_MAX):
                if(shiftRegisterStateStorage[15] == 0):
                    shift_register_change_state(15)
                trafficLightSequenceStarting2 = time.time() - 31
            else:

                shift_register_change_state(9)
                shift_register_change_state(11)
                trafficLightSequenceStarting2 = 0     
                trafficLightSequenceRunning2["Sequence0"] = False
                trafficLightSequenceRunning2["Sequence1"] = False
   
def traffic_light_sequence_segmented(runningSequence, startingTime, currentTime, detectionDist, min1,max1,min2,max2, trafficLightFunction, detectionDist2):
    if(detectionDist < DETECTION_DISTANCE_MAX or runningSequence["Sequence0"] or detectionDist2 < DETECTION_DISTANCE_MAX):
        if(runningSequence["Sequence0"] == False):
            trafficLightFunction(0)

        
        if(runningSequence["Sequence1"] == False and  min1<=(currentTime - startingTime)<=max1  and runningSequence["Sequence0"]):
            trafficLightFunction(1)

        if( min2<= (currentTime - startingTime)<= max2 and runningSequence["Sequence0"] and runningSequence["Sequence1"]):
            trafficLightFunction(2)

def set_warning_lights(wl1, wl2):
    shiftRegisterStateStorage[12] = wl1
    shiftRegisterStateStorage[13] = wl2
    iterate_over_shift_register_array(shiftRegisterStateStorage[::-1])


def turn_off_PA():
    if(shiftRegisterStateStorage[6] == 0 and shiftRegisterStateStorage[9] == 0 and shiftRegisterStateStorage[14] == 1 and shiftRegisterStateStorage[7] == 0 and shiftRegisterStateStorage[10] == 0):
        shiftRegisterStateStorage[14] = 0
        if(shiftRegisterStateStorage[15] == 1):
            shiftRegisterStateStorage[15] = 0
        iterate_over_shift_register_array(shiftRegisterStateStorage[::-1])
    


def main():
    global DETECTION_DISTANCE_MAX
    global trafficLightSequenceStarting1
    global trafficLightSequenceRunning1
    global trafficLightSequenceStarting2
    global trafficLightSequenceRunning2
    global trafficLightSequenceStarting6
    global trafficLightSequenceRunning6

    lastFlashTime = 0


    print("Executing")
    try:
        iterate_over_shift_register_array(shiftRegisterStateStorage[::-1])

        detection_distance_input_handler()        

        while(True):
            time.time()

            #Logic if same vehicle between US1 and US2
            traffic_light_sequence_segmented(trafficLightSequenceRunning2, trafficLightSequenceStarting2, time.time(), distanceUS2, 1,100,31,100,traffic_light_sequence_2, DETECTION_DISTANCE_MAX)
                    
            #TL1 Logic 
            traffic_light_sequence_segmented(trafficLightSequenceRunning1, trafficLightSequenceStarting1, time.time(), distanceUS1, 1,100,31,100,traffic_light_sequence_1, distanceUS2)

            #TL6 Logic
            traffic_light_sequence_segmented(trafficLightSequenceRunning6, trafficLightSequenceStarting6, time.time(), distanceUS5, 5 +dayDetectedTimeAdd,100 +dayDetectedTimeAdd,8 +dayDetectedTimeAdd,100 +dayDetectedTimeAdd,traffic_light_sequence_6, DETECTION_DISTANCE_MAX)
            
            if(( trafficLightSequenceRunning1["Sequence0"] or trafficLightSequenceRunning2["Sequence0"]) and shiftRegisterStateStorage[8] == 0 and shiftRegisterStateStorage[11] ==0):
                if time.time() - lastFlashTime >= 0.25:
                    if shiftRegisterStateStorage[12] == 1:
                        set_warning_lights(0, 1)
                        lastFlashTime = time.time()

                    else:
                        set_warning_lights(1, 0)
                        lastFlashTime = time.time()
            else:
                if(shiftRegisterStateStorage[12] == 1 or shiftRegisterStateStorage[13] == 1):
                    set_warning_lights(0,0)

            turn_off_PA()
            
            time.sleep(0.025)
        


    except KeyboardInterrupt:
        print("Program ending...")
        board.shutdown()
        exit()


if(__name__ == "__main__"):
    main()
