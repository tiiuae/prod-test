from serial import Serial, SerialException # for serial communication with Saluki
# from serial.tools import list_ports # for serial communication with Saluki
import sys, os, subprocess, time #

# Global variables and constants
#VIDPID_STRING = 'USB VID:PID=0403:6001'
PORT = "/dev/ttyUSB0"
results = {'accel_X': False, 'accel_Y': False, 'accel_Z': False, 'baro': False, 'gps': False, 'ina226': False, 'microSD': False, 'sbus': False, 'ethernet': False}

# Sensor value limits
XY_LO_LIM = -1
XY_UP_LIM = 1
Z_UP_LIM = -9.81 + 1
Z_LO_LIM = -9.81 - 1
P_LO_LIM = 95000
P_UP_LIM = 105000

Y_LO_ORI = [-1, -1, 9.81 - 1]
Y_UP_ORI = [1, 1, 9.81 + 1]
Z_LO_ORI = [-9.81 - 1, 9.81 - 1, -1]
Z_UP_ORI = [-9.81 + 1, 9.81 + 1, 1]
        
def flushInput():
    for j in range(5):
        saluki.reset_input_buffer()
        j += 1
        time.sleep(0.01)

def restartApp():
    try:
        saluki.close()
    except NameError:
        pass
    finally:
        subprocess.call([sys.executable, os.path.realpath(__file__)] + sys.argv[1:])
    
def exitApp():
    try:
        saluki.close()
    except NameError:
        pass
    finally:
        os._exit(1)

def accel():
    global accStr
    saluki.write("listener sensor_accel\n".encode('ascii'))
    accStr = saluki.read_until(b'saluki>').decode('ascii')
    nAccIdx = accStr.find("TOPIC: sensor_accel")
    if nAccIdx > -1 and accStr[nAccIdx + 20] == '3':
        x0i = accStr.find("x: ") + 3
        y0i = accStr.find("y: ") + 3
        z0i = accStr.find("z: ") + 3
        x0v = float(accStr[x0i:].split('\n', 1)[0].strip())
        y0v = float(accStr[y0i:].split('\n', 1)[0].strip())
        z0v = float(accStr[z0i:].split('\n', 1)[0].strip())
        x1i = accStr.find("x: ", z0i) + 3
        y1i = accStr.find("y: ", z0i) + 3
        z1i = accStr.find("z: ", z0i) + 3
        x1v = float(accStr[x1i:].split('\n', 1)[0].strip())
        y1v = float(accStr[y1i:].split('\n', 1)[0].strip())
        z1v = float(accStr[z1i:].split('\n', 1)[0].strip())
        x2i = accStr.find("x: ", z1i) + 3
        y2i = accStr.find("y: ", z1i) + 3
        z2i = accStr.find("z: ", z1i) + 3
        x2v = float(accStr[x2i:].split('\n', 1)[0].strip())
        y2v = float(accStr[y2i:].split('\n', 1)[0].strip())
        z2v = float(accStr[z2i:].split('\n', 1)[0].strip())
        return [[x0v, x1v, x2v], [y0v, y1v, y2v], [z0v, z1v, z2v]]
    else:
        return None
    
def orientation():
    for i in range(3):
        xyz = accel()
        if xyz == None:
            print("No response from one or more accelerometers.")
            return
        print(xyz)
        x = min(xyz[0]) > XY_LO_LIM and max(xyz[0]) < XY_UP_LIM
        y = min(xyz[1]) > Y_LO_ORI[i] and max(xyz[1]) < Y_UP_ORI[i]
        z = min(xyz[2]) > Z_LO_ORI[i] and max(xyz[2]) < Z_UP_ORI[i]
        if not (x and y and z):
            print("Orientation test\033[0;31m failed\033[0m.")
            return
        elif i == 0:
            input("Flip the Saluki upside down and press [ENTER]. ")
        elif i == 1:
            input("Place the Saluki on its side (the side with no connectors or leds) and press [ENTER]. ")
        elif i == 2:
            print("Orientation test\033[0;32m passed\033[0m.")

# Hard-coded port in Linux version
# Find Saluki v2 COM port based on VID:PID
# for comport, device, hwid in list_ports.comports():
#     if VIDPID_STRING in hwid:
#         break           
# else:
#     print("Error! Trace cable disconnected.")
#     input("Press [ENTER] to try again. ")
#     restartApp()

# Connect to Saluki via serial
try:
    saluki = Serial(port=PORT, baudrate=115200, timeout=15)
    print("Successully connected to {}.".format(PORT))
    saluki.write('\n'.encode('ascii'))
    b = saluki.read(1)
    # Ignore '\xff'
    while b == b'\xff':
        b = saluki.read(1)
    if b == b'':
        # No bytes received, Saluki powered off or trace disconnected
        print("Failed to connect to Saluki. Check power and trace cables.")
        input("Press [ENTER] to try again. ")
        restartApp()
    elif b == b'\r':
        # Saluki has already booted, reboot now
        #saluki.write("param set SYS_AUTOSTART 4400\n".encode('ascii'))
        saluki.write("reboot\n".encode('ascii'))
        saluki.read_until(b'reboot') # trash
        bootStr = saluki.read_until(b'saluki>').decode('ascii')
    else:
        # Boot in progress, reboot when finished
        bootStr = saluki.read_until(b'saluki>').decode('ascii')
        #saluki.write("param set SYS_AUTOSTART 4400\n".encode('ascii'))
        saluki.write("reboot\n".encode('ascii'))
        saluki.read_until(b'reboot') # trash
        bootStr = saluki.read_until(b'saluki>').decode('ascii')

except SerialException:
    print("Error! Serial port in use.")
    input("Press [ENTER] to try again. ")
    restartApp()

print("Saluki booted.")
try:
    #PX4GUID
    guidIdx = bootStr.find("PX4GUID: ") + 9
    guid = bootStr[guidIdx:].split('\n', 1)[0]
    print("PX4GUID: " + guid)

    # GPS STATUS
    print("Waiting for GPS... ", end='', flush=True)
    initStr = saluki.read_until(b'NEO-M8N-0').decode('ascii')
    if initStr.find("NEO-M8N-0") > -1:
        print("ready.")
        time.sleep(2) # GPS actually ready in ~1s
    else:
        print("timeout.")
    saluki.write("gps status\n".encode('ascii'))
    gpsStr = saluki.read_until(b'saluki>').decode('ascii')
    gpsStaIdx = gpsStr.find("status: ")
    if gpsStaIdx < 0 or gpsStr[gpsStaIdx + 8:gpsStaIdx + 14] == 'NOT OK':
        print("GPS not connected.")
    else:
        results['gps'] = True

    # LISTENER ACCEL (via accel function)
    xyz = accel()
    if xyz != None:
        if min(xyz[0]) < XY_LO_LIM or max(xyz[0]) > XY_UP_LIM:
            print("X-axis of one or more accelerometers out of approved range.")
        else:
            results['accel_X'] = True
        if min(xyz[1]) < XY_LO_LIM or max(xyz[1]) > XY_UP_LIM:
            print("Y-axis of one or more accelerometers out of approved range.")
        else:
            results['accel_Y'] = True
        if min(xyz[2]) < Z_LO_LIM or max(xyz[2]) > Z_UP_LIM:
            print("Z-axis of one or more accelerometers out of approved range.")
        else:
            results['accel_Z'] = True
    else:
        print("No response from one or more accelerometers.")

    # LISTENER BARO
    saluki.write("listener sensor_baro\n".encode('ascii'))
    barStr = saluki.read_until(b'saluki>').decode('ascii')
    nBarIdx = barStr.find("TOPIC: sensor_baro")
    if nBarIdx > -1 and barStr[nBarIdx + 19] == '2':
        p0i = barStr.find("pressure: ") + 10
        p1i = barStr.find("pressure: ", p0i) + 10
        p0v = float(barStr[p0i:].split('\n', 1)[0].strip())
        p1v = float(barStr[p1i:].split('\n', 1)[0].strip())
        ps = [p0v, p1v]
        if min(ps) < P_LO_LIM or max(ps) > P_UP_LIM:
            print("Pressure of one or both barometers out of approved range.")
        else:
            results['baro'] = True
    else:
        print("No response from one or more barometers.")

    # INA226
    saluki.write("ina226 status\n".encode('ascii'))
    inaStr = saluki.read_until(b'saluki>').decode('ascii')
    if inaStr.find("Running on I2C Bus 2") > -1:
        results['ina226'] = True
    else:
        print("Power module (INA226) not connected.")

    # SBUS
    saluki.write("rc_input status\n".encode('ascii'))
    rcStr = saluki.read_until(b'saluki>').decode('ascii')
    uartIdx = rcStr.find("UART RX bytes: ")
    if uartIdx < 0:
        print("SBUS not connected.")
    else:
        uartBytes = int(rcStr[uartIdx + 15:].split('\n', 1)[0].strip())
        if uartBytes < 1:
            print("SBUS not connected.")
        else:
            print("SBUS bytes: {}".format(uartBytes))
            results['sbus'] = True

    # Ethernet ping
    saluki.write("ping -c 1 192.168.200.100\n".encode('ascii'))
    ethStr = saluki.read_until(b'saluki>').decode('ascii')
    if ethStr.find("No response") != -1:
        results['ethernet'] = True
    else:
        print("Ping failed. Check ethernet cable connection.")
        
    # SD CARD
    # Create directory and file on MicroSD card
    saluki.write("cd /fs/microsd\nmkdir prod_test_dir\nls\ncd prod_test_dir\ncat > prod_test_file\n".encode('ascii'))
    # Reboot
    saluki.write("reboot\n".encode('ascii)'))
    saluki.read_until(b'reboot') # trash
    bootStr = saluki.read_until(b'saluki>').decode('ascii')
    saluki.write("cd /fs/microsd/prod_test_dir\nls\n".encode('ascii'))
    sdStr = saluki.read_until(b'prod_test_file').decode('ascii')
    if sdStr.find("prod_test_file") > -1:
        results['microSD'] = True
    else:
        print("MicroSD test failed.")
    saluki.write("cd /fs/microsd\nrm -r prod_test_dir\n".encode('ascii'))

    # Sensors
    try:
        print("\nacceleration: {}\npressure: {}\n".format(xyz, ps))
    except NameError:
        pass
    
    # Summary
    flushInput()
    for i in results:
        if results[i]:
            print("{} passed.".format(i))
        else:
            print("\033[0;31m{} failed.\033[0m".format(i)) # red text
    if all(results.values()):
        print("\033[0;32mAll tests passed!\033[0m") # green text

    # Menu
    while True:   
        key = input("\n[a] to run tests again\n[o] to run orientation test\n[p] to print raw trace data\n[q] to quit\ncmd: ").upper()
        if key == 'Q':
            exitApp()
        elif key == 'O':
            orientation()
        elif key == 'P':
            print(bootStr +'\n\n' + accStr +'\n\n' + barStr +'\n\n' + inaStr + '\n\n' + gpsStr + '\n\n' + ethStr)
        elif key == 'A':
            restartApp()

except SerialException:
    print("Serial error! Check trace cable and that there are no other sessions open. ({})".format(PORT))
    input("Press [ENTER] to close test app. ")
    exitApp()
except UnicodeDecodeError:
    print("Other error!")
    input("Press [ENTER] to close test app. ")
    exitApp()
except (ValueError, IndexError):
    print("Parsing error! Unexpected output from trace.")
    input("Press [ENTER] to close test app. ")
    exitApp()
