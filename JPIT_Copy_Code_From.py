##############################################
# Tooling Inspection Motion Controller GUI   #
# Tool: Jet Pump Inspection Tool             #
# PLM:  TBD                                  #
##############################################

# Author:   Timothy Clark
# Email:    timoty.clark@ge.com
# Date:     05/15/2018
# Company:  GE Hitachi
# Description
#   - Graphical User Interface using Tkinter package
#   - Requires python 3.6
#   - Lienar amplifiers to reduce EMI: Aerotech Ensemble ML
#   - Serial communication with Aerobasic ASCII commands
#
# ###########################################################



from tkinter import *
from tkinter import messagebox
#from f_printHeader import printHeader
#from f_openSerial import openSerial
#from f_isAlive import isAlive
#from f_disableDrive import disableDrive
#from f_acmd import acmd #function to write ASCII commands

#Calculated based on scan circ motor input gear box speed of 4000 RPM
MAX_CIRC_SPEED = 11.4 #deg/sec

#Acceptable difference between feedback and commanded position
ERROR = 0.01

#Program Variables
stateArray = [0,0,0,0,0] # Scan Circ, Scan Raidal, Position Circ, Position Radial, Performing Scan

axisNameArray = ["Drive_Axis_A", "Drive_Axis_B", "Drive_Axis_C", "Drive_Axis_D"]


#Call initialization functions
#printHeader()
#ser = openSerial()
#isAlive(ser)
#disableDrive(ser, axisNameArray)

#Set "NOWAIT" mode which allows for commands to be sent while moves are in progress
#acmd(ser, "WAIT MODE NOWAIT")

############################################
#                FUNCTIONS                 #
############################################

#Get user input about scan, calculate vertices, calculate move distances, calculate move times. All saved to scanArray
def initScan():
    global scanIndex, scanArray, sizeofScanArray

    if(stateArray[4] == 0):

        #Check if user forgot to intput data
        if(len(eScanWindow_scanStart.get()) == 0 or len(eScanWindow_scanStop.get()) == 0 or len(eScanWindow_indexStart.get()) == 0 or len(eScanWindow_indexStop.get()) == 0 or len(eScanWindow_indexSize.get()) == 0):
            messagebox.showinfo("Scan Error", "Scan Error: No Data")
            return

        #Convert user data to float
        scanStart = float(eScanWindow_scanStart.get())
        scanStop = float(eScanWindow_scanStop.get())
        indexStart = float(eScanWindow_indexStart.get())
        indexStop = float(eScanWindow_indexStop.get())
        indexSize = float(eScanWindow_indexSize.get())
        #Check if user input is valid
        if(scanStop < scanStart):
            messagebox.showinfo("Scan Error", "Scan Error: scanStop < scanStart")
            return
        if(indexStop < indexStart):
            messagebox.showinfo("Scan Error", "Scan Error: indexStop < indexStart")
            return
        if(v.get() == 0 and  indexStart <= 0):
            messagebox.showinfo("Scan Error", "Scan Error: indexStart must be greater than zero")
            return
        if(indexSize == 0):
            messagebox.showinfo("Scan Error", "Scan Error: Index Size is zero")
            return

        #Check if axes are enabled
        if(stateArray[0] == 0 ):
            messagebox.showinfo("Scan Error", "Scan Circ Axis Not Enabled")
            return
        if(stateArray[1] == 0 ):
            messagebox.showinfo("Scan Error", "Scan Radial Axis Not Enabled")
            return
        #If error checking above is successful disable appropriate buttons

        #Disable Scan Speed and entry boxes
        sScanWindow_velocity.config(state = "disabled")
        eScanWindow_scanStart.config(state = "disabled")
        eScanWindow_scanStop.config(state = "disabled")
        eScanWindow_indexStart.config(state = "disabled")
        eScanWindow_indexStop.config(state = "disabled")
        eScanWindow_indexSize.config(state = "disabled")
        bScanWindow_Start.config(state = "disabled")
        radio1.config(state = "disabled")
        radio2.config(state = "disabled")
        radio3.config(state = "disabled")
        radio4.config(state = "disabled")

        #Disable Scan Circ and Scan Radial inputs
        bScan_ENABLE_circ.config(state = "disabled")
        bScan_CCW.config(state = "disabled")
        bScan_CW.config(state = "disabled")
        bScan_Set_circ.config(state = "disabled")
        bScan_GoTo_circ.config(state = "disabled")
        bScan_Increment_circ.config(state = "disabled")
        sScan_circ_velocity.config(state = "disabled")
        eScan_circ_set.config(state = "disabled")
        eScan_circ_goto.config(state = "disabled")
        eScan_circ_increment.config(state = "disabled")

        bScan_ENABLE_rad.config(state = "disabled")
        bScan_IN.config(state = "disabled")
        bScan_OUT.config(state = "disabled")
        bScan_Set_rad.config(state = "disabled")
        bScan_GoTo_rad.config(state = "disabled")
        bScan_Increment_rad.config(state = "disabled")
        sScan_rad_velocity.config(state = "disabled")
        eScan_rad_set.config(state = "disabled")
        eScan_rad_goto.config(state = "disabled")
        eScan_rad_increment.config(state = "disabled")

        #Disable Position Circ and Position Radial inputs
        bPos_ENABLE_circ.config(state = "disabled")
        bPos_CCW.config(state = "disabled")
        bPos_CW.config(state = "disabled")
        bPos_Set_circ.config(state = "disabled")
        bPos_GoTo_circ.config(state = "disabled")
        bPos_Increment_circ.config(state = "disabled")
        sPos_circ_velocity.config(state = "disabled")
        ePos_circ_set.config(state = "disabled")
        ePos_circ_goto.config(state = "disabled")
        ePos_circ_increment.config(state = "disabled")

        bPos_ENABLE_rad.config(state = "disabled")
        bPos_IN.config(state = "disabled")
        bPos_OUT.config(state = "disabled")
        bPos_Set_rad.config(state = "disabled")
        bPos_GoTo_rad.config(state = "disabled")
        bPos_Increment_rad.config(state = "disabled")
        sPos_rad_velocity.config(state = "disabled")
        ePos_rad_set.config(state = "disabled")
        ePos_rad_goto.config(state = "disabled")
        ePos_rad_increment.config(state = "disabled")

        #Enable buttons for scan
        bScanWindow_Stop.config(state = "active")
        bScanWindow_Pause.config(state = "active")
        #Initialize state variable that scan is in progress
        stateArray[4] = 1

        #Initialize scanArray and index parameter
        scanIndex = 0
        w,h = 4,10000
        scanArray = [[0 for x in range(w)] for y in range(h)]

        #Below will populate scanArray with [r][theta][distance]
        #Note:  The conditional statements below specify points at which to break
        #       the while loop when all the vertices have been created for the scan.
        #       The comments are lacking to describe this logic because it's very
        #       complicated.

        #Circumferential Exam: If radio button value <v> is 0 scan is (deg), index is (in):
        if(v.get() == 0):
            #Array Format: [r][theta][distance][rem time], set first row of scanArray
            scanArray[scanIndex][0] = indexStart
            scanArray[scanIndex][1] = scanStart
            scanArray[scanIndex][2] = 0 #move distance is zero for first point

            #Initialize column variables which will change in while loop below based on algorithm
            rVar = indexStart
            thetaVar = scanStart
            prev_rVar = rVar
            prev_thetaVar = thetaVar

            #Loop to generate the rest of the scanArray vertices
            scanIndex = 1
            while(TRUE):
                #scanArray complete where delta index is divisible by indexSize
                if((indexStop - indexStart) % indexSize == 0 and indexStop == rVar and scanArray[scanIndex-2][0] == rVar):
                    break
                #Bi-directional scan
                if(d.get() == 0):
                    if((indexStop - indexStart) % indexSize != 0 and rVar + indexSize > indexStop and scanStart == thetaVar):
                        break
                    if((scanIndex+1)%2 == 1):
                        #Increment rVar
                        rVar = rVar + indexSize
                    if(scanIndex%2 == 1):
                        #Toggle thetaVar
                        thetaVar = scanStart if thetaVar == scanStop else scanStop

                    scanArray[scanIndex][0] = rVar
                    scanArray[scanIndex][1] = thetaVar
                    #print(scanArray[scanIndex][:])

                #Uni-directional scan
                elif(d.get() == 1):
                    if((indexStop - indexStart) % indexSize != 0 and rVar + indexSize > indexStop and scanStop == thetaVar):
                        break
                    if((scanIndex+3)%3 == 0):
                        #Increment rVar
                        rVar = rVar + indexSize
                    if((scanIndex+2)%3 == 0):
                        thetaVar = scanStop
                    elif((scanIndex+2)%3 != 0):
                        thetaVar = scanStart

                    scanArray[scanIndex][0] = rVar
                    scanArray[scanIndex][1] = thetaVar
                    #print(scanArray[scanIndex][:])

                #Calculate move distance
                if(prev_rVar != rVar):
                    distance = abs(rVar - prev_rVar)
                if(prev_thetaVar != thetaVar):
                    #Arc Length Formula: theta/360 * 2*pi*r
                    distance = 2*3.141592*rVar*abs(prev_thetaVar - thetaVar)/360

                scanArray[scanIndex][2] = abs(distance)
                #print(scanArray[scanIndex][2])

                #Update loop parameters
                scanIndex += 1
                prev_rVar = rVar
                prev_thetaVar = thetaVar

            #While loop complete but scanIndex is too large
            scanIndex -= 1

        #Radial Exam:
        elif(v.get() == 1):
            #Array Format: [r][theta], set first row of scanArray
            scanArray[scanIndex][0] = scanStart
            scanArray[scanIndex][1] = indexStart
            scanArray[scanIndex][2] = 0 #move distance is zero for first point
            #Initialize column variables which will change in while loop below based on algorithm
            rVar = scanStart
            thetaVar = indexStart
            prev_rVar = rVar
            prev_thetaVar = thetaVar

            #Loop to generate the rest of the scanArray vertices
            scanIndex = 1
            while(TRUE):
                #scanArray complete where delta index is divisible by indexSize
                if((indexStop - indexStart) % indexSize == 0 and scanArray[scanIndex-1][2] == abs(scanStop - scanStart) and thetaVar == indexStop):
                    break
                #Bi-directional scan
                if(d.get() == 0):
                    #condition if Bi-directional and one more scan line to center is necessary
                    if((indexStop - indexStart) % indexSize != 0 and rVar == scanStart and (thetaVar + indexSize) > indexStop):
                        break
                    if(scanIndex%2 == 1):
                        #Toggle rVar
                        rVar = scanStart if rVar == scanStop else scanStop
                    if((scanIndex+1)%2 == 1):
                        #Increment thetaVar
                        thetaVar = thetaVar + indexSize
                    scanArray[scanIndex][0] = rVar
                    scanArray[scanIndex][1] = thetaVar
                    #print(scanArray[scanIndex][:])

                #Uni-directional scan
                elif(d.get() == 1):
                    #condition if Uni-directional and one more scan line to stopScan is necessary
                    if((indexStop - indexStart) % indexSize != 0 and rVar == scanStop and (thetaVar + indexSize) > indexStop):
                        break
                    if((scanIndex+3)%3 == 1):
                        #Toggle rVar
                        rVar = scanStart if rVar == scanStop else scanStop
                    elif((scanIndex+3)%3 != 1):
                        rVar = scanStart
                    if((scanIndex+1)%3 == 1):
                        #Increment thetaVar
                        thetaVar = thetaVar + indexSize
                    scanArray[scanIndex][0] = rVar
                    scanArray[scanIndex][1] = thetaVar
                    #print(scanArray[scanIndex][:])

                #Calculate move distance
                if(prev_rVar != rVar):
                    distance = abs(rVar - prev_rVar)
                if(prev_thetaVar != thetaVar):
                    distance = 2*3.141592*scanStop*abs(prev_thetaVar - thetaVar)/360
                scanArray[scanIndex][2] = distance
                #print(scanArray[scanIndex][2])

                #Update loop parameters
                scanIndex += 1
                prev_rVar = rVar
                prev_thetaVar = thetaVar

            #While loop complete but scanIndex is too large
            scanIndex -= 1

    else:
        messagebox.showinfo("Scan Error", "Scan Error")
        return

    sizeofScanArray = scanIndex #started from counting at zero
    scanIndex = 0

    #Add up the total distance moved
    i = sizeofScanArray
    totalScanDistance = 0
    while(i >= 0):
        totalScanDistance += scanArray[i][2]
        i-=1

    #Calculate total scan time
    scanSpeed = sScanWindow_velocity.get()

    #Program loop speed affects the duration of the exam
    totalScanTime = totalScanDistance/scanSpeed + (0.5456*sizeofScanArray + 3.4393)
    #print("Total Time: %d Size: %d" %(totalScanTime, sizeofScanArray))
    #print("Time Start: %d" %time.time())

    #Calculated time error based on emperical results. y = time, x = vertices: y = 0.1699x + 2.33
    timeError = (0.5456*sizeofScanArray + 3.4393)/sizeofScanArray

    #Loop and insert remaining time into scanArray
    i = 0
    timeRemaining = totalScanTime
    moveTime = 0
    while(i <= sizeofScanArray):
        moveTime = (scanArray[i][2]/scanSpeed) + timeError #distance/speed
        scanArray[i][3] = timeRemaining - moveTime
        timeRemaining -= moveTime
        i+=1

    #Update Time Entry Box of Scan Window
    hours = int(totalScanTime / 3600)
    mins = int((totalScanTime - (hours * 3600)) / 60)
    seconds = int(totalScanTime - hours*3600 - mins*60)
    scanTimeText.set(str(hours).zfill(2) + ":" + str(mins).zfill(2) + ":" + str(seconds).zfill(2))
    #messagebox.showinfo("Scan Time", "Estimated Scan Time = " + str(hours).zfill(2) + ":" + str(mins).zfill(2) + ":" + str(seconds).zfill(2) + " Vertices: " + str(sizeofScanArray))

def stopScan():
    stateArray[4] = 0
    bScanWindow_Stop.config(state = "disabled")
    bScanWindow_Pause.config(state = "disabled")
    bScanWindow_Resume.config(state = "disabled")
    bScanWindow_Start.config(state = "active")


    acmd(ser, "ABORT Drive_Axis_A")
    acmd(ser, "ABORT Drive_Axis_B")

    #Enable scan speed bar and entry boxes
    sScanWindow_velocity.config(state = "normal")
    eScanWindow_scanStart.config(state = "normal")
    eScanWindow_scanStop.config(state = "normal")
    eScanWindow_indexStart.config(state = "normal")
    eScanWindow_indexStop.config(state = "normal")
    eScanWindow_indexSize.config(state = "normal")
    radio1.config(state = "normal")
    radio2.config(state = "normal")
    radio3.config(state = "normal")
    radio4.config(state = "normal")

    #Enable Scan Circ and Scan Radial inputs
    bScan_ENABLE_circ.config(state = "normal")
    bScan_CCW.config(state = "normal")
    bScan_CW.config(state = "normal")
    bScan_Set_circ.config(state = "normal")
    bScan_GoTo_circ.config(state = "normal")
    bScan_Increment_circ.config(state = "normal")
    sScan_circ_velocity.config(state = "normal")
    eScan_circ_set.config(state = "normal")
    eScan_circ_goto.config(state = "normal")
    eScan_circ_increment.config(state = "normal")

    bScan_ENABLE_rad.config(state = "normal")
    bScan_IN.config(state = "normal")
    bScan_OUT.config(state = "normal")
    bScan_Set_rad.config(state = "normal")
    bScan_GoTo_rad.config(state = "normal")
    bScan_Increment_rad.config(state = "normal")
    sScan_rad_velocity.config(state = "normal")
    eScan_rad_set.config(state = "normal")
    eScan_rad_goto.config(state = "normal")
    eScan_rad_increment.config(state = "normal")

    #Enable Position Circ and Position Radial inputs
    bPos_ENABLE_circ.config(state = "normal")
    bPos_CCW.config(state = "normal")
    bPos_CW.config(state = "normal")
    bPos_Set_circ.config(state = "normal")
    bPos_GoTo_circ.config(state = "normal")
    bPos_Increment_circ.config(state = "normal")
    sPos_circ_velocity.config(state = "normal")
    ePos_circ_set.config(state = "normal")
    ePos_circ_goto.config(state = "normal")
    ePos_circ_increment.config(state = "normal")

    bPos_ENABLE_rad.config(state = "normal")
    bPos_IN.config(state = "normal")
    bPos_OUT.config(state = "normal")
    bPos_Set_rad.config(state = "normal")
    bPos_GoTo_rad.config(state = "normal")
    bPos_Increment_rad.config(state = "normal")
    sPos_rad_velocity.config(state = "normal")
    ePos_rad_set.config(state = "normal")
    ePos_rad_goto.config(state = "normal")
    ePos_rad_increment.config(state = "normal")

#Scan Window must change units based on scan type
def changeUnits():
    #If radio button value <v> is 0 scan is (deg), index is (in)
    if(v.get() == 0):
        scanStartText.set("Scan Start (deg)")
        scanStopText.set("Scan Stop (deg)")
        indexStartText.set("Index Start (in)")
        indexStopText.set("Index Stop (in)")
        indexSizeText.set("Index Size (in)")
    elif(v.get() == 1):
        scanStartText.set("Scan Start (in)")
        scanStopText.set("Scan Stop (in)")
        indexStartText.set("Index Start (deg)")
        indexStopText.set("Index Stop (deg)")
        indexSizeText.set("Index Size (deg)")

def disableAxis(axis):

    if(axis == 0):
        acmd(ser, "DISABLE " + axisNameArray[axis])
        if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
            bScan_ENABLE_circ.config(text = "OFF", bg = "red")
            bScan_CCW.config(state = "disabled")
            bScan_CW.config(state = "disabled")
            bScan_Set_circ.config(state = "disabled")
            bScan_GoTo_circ.config(state = "disabled")
            bScan_Increment_circ.config(state = "disabled")
            stateArray[axis] = 0
        else:
            messagebox.showinfo("ERROR", "Cannot Disable Axis: %s" %axisNameArray[axis])
    elif(axis == 1):
        acmd(ser, "DISABLE " + axisNameArray[axis])
        if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
            bScan_ENABLE_rad.config(text = "OFF", bg = "red")
            bScan_IN.config(state = "disabled")
            bScan_OUT.config(state = "disabled")
            bScan_Set_rad.config(state = "disabled")
            bScan_GoTo_rad.config(state = "disabled")
            bScan_Increment_rad.config(state = "disabled")
            stateArray[axis] = 0
        else:
            messagebox.showinfo("ERROR", "Cannot Disable Axis: %s" %axisNameArray[axis])
    elif(axis == 2):
        acmd(ser, "DISABLE " + axisNameArray[axis])
        if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
            #print("Axis 2 disabled")
            bPos_ENABLE_circ.config(text = "OFF", bg = "red")
            bPos_CCW.config(state = "disabled")
            bPos_CW.config(state = "disabled")
            bPos_Set_circ.config(state = "disabled")
            bPos_GoTo_circ.config(state = "disabled")
            bPos_Increment_circ.config(state = "disabled")
            stateArray[axis] = 0
        else:
            messagebox.showinfo("ERROR", "Cannot Disable Axis: %s" %axisNameArray[axis])
    elif(axis == 3):
        acmd(ser, "DISABLE " + axisNameArray[axis])
        if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
            #print("Axis 3 disabled")
            bPos_ENABLE_rad.config(text = "OFF", bg = "red")
            bPos_IN.config(state = "disabled")
            bPos_OUT.config(state = "disabled")
            bPos_Set_rad.config(state = "disabled")
            bPos_GoTo_rad.config(state = "disabled")
            bPos_Increment_rad.config(state = "disabled")
            stateArray[axis] = 0
        else:
            messagebox.showinfo("ERROR", "Cannot Disable Axis: %s" %axisNameArray[axis])


#Function will enable <axis> if the axis state variable returns that the axis enable was successful
def enableAxisBtn(axis):

    if(axis == 0):
        if(stateArray[axis] == 0):
            acmd(ser, "ENABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 1):
                bScan_ENABLE_circ.config(text = "ON", bg = "#00aa00")
                bScan_CCW.config(state = "active")
                bScan_CW.config(state = "active")
                bScan_Set_circ.config(state = "active")
                bScan_GoTo_circ.config(state = "active")
                bScan_Increment_circ.config(state = "active")
                stateArray[axis] = 1
        else:
            acmd(ser, "DISABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
                bScan_ENABLE_circ.config(text = "OFF", bg = "red")
                bScan_CCW.config(state = "disabled")
                bScan_CW.config(state = "disabled")
                bScan_Set_circ.config(state = "disabled")
                bScan_GoTo_circ.config(state = "disabled")
                bScan_Increment_circ.config(state = "disabled")
                stateArray[axis] = 0
    elif(axis == 1):
        if(stateArray[axis] == 0):
            acmd(ser, "ENABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 1):
                bScan_ENABLE_rad.config(text = "ON", bg = "#00aa00")
                bScan_IN.config(state = "active")
                bScan_OUT.config(state = "active")
                bScan_Set_rad.config(state = "active")
                bScan_GoTo_rad.config(state = "active")
                bScan_Increment_rad.config(state = "active")
                stateArray[axis] = 1
        else:
            acmd(ser, "DISABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
                bScan_ENABLE_rad.config(text = "OFF", bg = "red")
                bScan_IN.config(state = "disabled")
                bScan_OUT.config(state = "disabled")
                bScan_Set_rad.config(state = "disabled")
                bScan_GoTo_rad.config(state = "disabled")
                bScan_Increment_rad.config(state = "disabled")
                stateArray[axis] = 0
    elif(axis == 2):
        if(stateArray[axis] == 0):
            acmd(ser, "ENABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 1):
                bPos_ENABLE_circ.config(text = "ON", bg = "#00aa00")
                bPos_CCW.config(state = "active")
                bPos_CW.config(state = "active")
                bPos_Set_circ.config(state = "active")
                bPos_GoTo_circ.config(state = "active")
                bPos_Increment_circ.config(state = "active")
                stateArray[axis] = 1
        else:
            acmd(ser, "DISABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
                #print("Axis 2 disabled")
                bPos_ENABLE_circ.config(text = "OFF", bg = "red")
                bPos_CCW.config(state = "disabled")
                bPos_CW.config(state = "disabled")
                bPos_Set_circ.config(state = "disabled")
                bPos_GoTo_circ.config(state = "disabled")
                bPos_Increment_circ.config(state = "disabled")
                stateArray[axis] = 0
    elif(axis == 3):
        if(stateArray[axis] == 0):
            acmd(ser, "ENABLE " + axisNameArray[axis])
            #print("Axis 3 enabled")
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 1):
                bPos_ENABLE_rad.config(text = "ON", bg = "#00aa00")
                bPos_IN.config(state = "active")
                bPos_OUT.config(state = "active")
                bPos_Set_rad.config(state = "active")
                bPos_GoTo_rad.config(state = "active")
                bPos_Increment_rad.config(state = "active")
                stateArray[axis] = 1
        else:
            acmd(ser, "DISABLE " + axisNameArray[axis])
            if((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 0):
                #print("Axis 3 disabled")
                bPos_ENABLE_rad.config(text = "OFF", bg = "red")
                bPos_IN.config(state = "disabled")
                bPos_OUT.config(state = "disabled")
                bPos_Set_rad.config(state = "disabled")
                bPos_GoTo_rad.config(state = "disabled")
                bPos_Increment_rad.config(state = "disabled")
                stateArray[axis] = 0

def moveInc(axis):
    if(axis == 0):
        distance = str(eScan_circ_increment.get())
        speed = str(sScan_circ_velocity.get())
        acmd(ser, "MOVEINC Drive_Axis_A " + distance + " F " + speed)
    elif(axis == 1):
        distance = str(eScan_rad_increment.get())
        speed = str(sScan_rad_velocity.get())
        acmd(ser, "MOVEINC Drive_Axis_B "+ distance + " F " + speed)
    elif(axis == 2):
        distance = str(ePos_circ_increment.get())
        speed = str(sPos_circ_velocity.get())
        acmd(ser, "MOVEINC Drive_Axis_C "+ distance + " F " + speed)
    elif(axis == 3):
        distance = str(ePos_rad_increment.get())
        speed = str(sPos_rad_velocity.get())
        acmd(ser, "MOVEINC Drive_Axis_D "+ distance + " F " + speed)

def moveTo(axis):
    if(axis == 0):
        distance = str(eScan_circ_goto.get())
        if(distance == ""):
            return
        speed = str(sScan_circ_velocity.get())
        acmd(ser, "MOVEABS Drive_Axis_A " + distance + " F " + speed)
    elif(axis == 1):
        distance = str(eScan_rad_goto.get())
        if(distance == ""):
            return
        speed = str(sScan_rad_velocity.get())
        acmd(ser, "MOVEABS Drive_Axis_B " + distance + " F " + speed)
    elif(axis == 2):
        distance = str(ePos_circ_goto.get())
        if(distance == ""):
            return
        speed = str(sPos_circ_velocity.get())
        acmd(ser, "MOVEABS Drive_Axis_C " + distance + " F " + speed)
    elif(axis == 3):
        distance = str(ePos_rad_goto.get())
        if(distance == ""):
            return
        speed = str(sPos_rad_velocity.get())
        acmd(ser, "MOVEABS Drive_Axis_D " + distance + " F " + speed)

def moveToVar(axis, location, speed):
    if(axis == 0):
        acmd(ser, "MOVEABS Drive_Axis_A " + str(location) + " F " + str(speed))
    elif(axis == 1):
        acmd(ser, "MOVEABS Drive_Axis_B " + str(location) + " F " + str(speed))
    elif(axis == 2):
        acmd(ser, "MOVEABS Drive_Axis_C " + str(location) + " F " + str(speed))
    elif(axis == 3):
        acmd(ser, "MOVEABS Drive_Axis_D " + str(location) + " F " + str(speed))

def startJog(axis, direction):
    if(axis == 0 and stateArray[0] and bScan_CW['state'] != 'disabled' and bScan_CCW['state'] != 'disabled'):
        acmd(ser, "ABORT Drive_Axis_A")
        if(direction == "forward"):
            speed = str(sScan_circ_velocity.get())
        elif(direction == "backward"):
            speed = str(-1*sScan_circ_velocity.get())
        acmd(ser, "FREERUN Drive_Axis_A " + speed)
    elif(axis == 1 and stateArray[1] and bScan_IN['state'] != 'disabled' and bScan_OUT['state'] != 'disabled'):
        acmd(ser, "ABORT Drive_Axis_B")
        if(direction == "forward"):
            speed = str(sScan_rad_velocity.get())
        elif(direction == "backward"):
            speed = str(-1*sScan_rad_velocity.get())
        acmd(ser, "FREERUN Drive_Axis_B " + speed)
    elif(axis == 2 and stateArray[2] and bPos_CW['state'] != 'disabled' and bPos_CCW['state'] != 'disabled'):
        acmd(ser, "ABORT Drive_Axis_C")
        if(direction == "forward"):
            speed = str(sPos_circ_velocity.get())
        elif(direction == "backward"):
            speed = str(-1*sPos_circ_velocity.get())
        acmd(ser, "FREERUN Drive_Axis_C " + speed)
    elif(axis == 3 and stateArray[3] and bPos_IN['state'] != 'disabled' and bPos_OUT['state'] != 'disabled'):
        acmd(ser, "ABORT Drive_Axis_D")
        if(direction == "forward"):
            speed = str(sPos_rad_velocity.get())
        elif(direction == "backward"):
            speed = str(-1*sPos_rad_velocity.get())
        acmd(ser, "FREERUN Drive_Axis_D " + speed)

def stopJog(axis):
    if(axis == 0 and stateArray[0] and bScan_CW['state'] != 'disabled' and bScan_CCW['state'] != 'disabled'):
        acmd(ser, "FREERUN Drive_Axis_A 0")
    elif(axis == 1 and stateArray[1] and bScan_IN['state'] != 'disabled' and bScan_OUT['state'] != 'disabled'):
        acmd(ser, "FREERUN Drive_Axis_B 0")
    elif(axis == 2 and stateArray[2] and bPos_CW['state'] != 'disabled' and bPos_CCW['state'] != 'disabled'):
        acmd(ser, "FREERUN Drive_Axis_C 0")
    elif(axis == 3 and stateArray[3] and bPos_IN['state'] != 'disabled' and bPos_OUT['state'] != 'disabled'):
        acmd(ser, "FREERUN Drive_Axis_D 0")

def setPos(axis):
    if(axis == 0):
        posToSet = str(eScan_circ_set.get())
        acmd(ser, "POSOFFSET SET Drive_Axis_A, " + posToSet)
    elif(axis == 1):
        posToSet = str(eScan_rad_set.get())
        acmd(ser, "POSOFFSET SET Drive_Axis_B, " + posToSet)
    elif(axis == 2):
        posToSet = str(ePos_circ_set.get())
        acmd(ser, "POSOFFSET SET Drive_Axis_C, " + posToSet)
    elif(axis == 3):
        posToSet = str(ePos_rad_set.get())
        acmd(ser, "POSOFFSET SET Drive_Axis_D, " + posToSet)

#Updates the GUI with position and current feedback values
def updateFBK():
    from f_acmd import acmd

    pos = acmd(ser, "PFBKPROG(Drive_Axis_A)")
    pos = round(float(pos),2)
    pos = format(pos,'.2f')
    scanCircPosition.set(pos)

    cur = acmd(ser, "IFBK(Drive_Axis_A)")
    cur = float(cur)*1000
    cur = round(cur)
    scanCircCurrent.set(cur)

    pos = acmd(ser, "PFBKPROG(Drive_Axis_B)")
    pos = round(float(pos),2)
    pos = format(pos,'.2f')
    scanRadPosition.set(pos)

    cur = acmd(ser, "IFBK(Drive_Axis_B)")
    cur = float(cur)*1000
    cur = round(cur)
    scanRadCurrent.set(cur)

    pos = acmd(ser, "PFBKPROG(Drive_Axis_C)")
    pos = round(float(pos),2)
    pos = format(pos,'.2f')
    posCircPosition.set(pos)

    cur = acmd(ser, "IFBK(Drive_Axis_C)")
    cur = float(cur)*1000
    cur = round(cur)
    posCircCurrent.set(cur)

    pos = acmd(ser, "PFBKPROG(Drive_Axis_D)")
    pos = round(float(pos),2)
    pos = format(pos,'.2f')
    posRadPosition.set(pos)

    cur = acmd(ser, "IFBK(Drive_Axis_D)")
    cur = float(cur)*1000
    cur = round(cur)
    posRadCurrent.set(cur)

    root.after(75, updateFBK)

def checkFaults():
    faultArray = [  "PositionError Fault",  #0
                    "OverCurrent Fault",    #1
                    "CW/Positive End-of-Travel Limit Fault",    #2
                    "CCW/Negative End-of-Travel Limit Fault",   #3
                    "CW/High Software Limit Fault", #4
                    "CCW/Low Software Limit Fault", #5
                    "Amplifier Fault",  #6
                    "Position Feedback Fault",  #7
                    "Velocity Feedback Fault",  #8
                    "Hall Sensor Fault",    #9
                    "Maximum Velocity Command Fault",   #10
                    "Emergency Stop Fault", #11
                    "Velocity Error Fault", #12
                    "N/A",  #13
                    "N/A",  #14
                    "External Fault",   #15
                    "N/A",  #16
                    "Motor Temperature Fault",  #17
                    "Amplifier Temperature Fault",  #18
                    "Encoder Fault",    #19
                    "Communication Lost Fault", #20
                    "N/A",  #21
                    "N/A",  #22
                    "Feedback Scaling Fault",   #23
                    "Marker Search Fault",  #24
                    "N/A",  #25
                    "N/A",  #26
                    "Voltage Clamp Fault",  #27
                    "Power Supply Fault"    #28
                    ]

    fault_A = int(acmd(ser, "AXISFAULT (Drive_Axis_A)"))
    fault_B = int(acmd(ser, "AXISFAULT (Drive_Axis_B)"))
    fault_C = int(acmd(ser, "AXISFAULT (Drive_Axis_C)"))
    fault_D = int(acmd(ser, "AXISFAULT (Drive_Axis_D)"))

    #If ESTOP fault, else check all other
    if(0b100000000000 & fault_A):
        pauseScan()
        disableAxis(0)
        disableAxis(1)
        disableAxis(2)
        disableAxis(3)

        messagebox.showinfo("FAULT: ESTOP", "%s" %faultArray[11])
        acmd(ser, "ACKNOWLEDGEALL")
    else:
        faultMask = 1
        if(fault_A != 0):
            disableAxis(0)
            pauseScan()
            for i in range(0, len(faultArray)):
                if((fault_A & (faultMask << i)) != 0):
                    messagebox.showinfo("FAULT: Scan Circ Axis", "%s" %faultArray[i])
            acmd(ser, "ACKNOWLEDGEALL")

        if(fault_B != 0):
            disableAxis(1)
            pauseScan()
            for i in range(0, len(faultArray)):
                if((fault_B & (faultMask << i)) != 0):
                    messagebox.showinfo("FAULT: Scan Radial Axis", "%s" %faultArray[i])
            acmd(ser, "ACKNOWLEDGEALL")

        if(fault_C != 0):
            disableAxis(2)
            pauseScan()
            for i in range(0, len(faultArray)):
                if((fault_C & (faultMask << i)) != 0):
                    messagebox.showinfo("FAULT: Position Circ Axis", "%s" %faultArray[i])
            acmd(ser, "ACKNOWLEDGEALL")

        if(fault_D != 0):
            disableAxis(3)
            pauseScan()
            for i in range(0, len(faultArray)):
                if((fault_D & (faultMask << i)) != 0):
                    messagebox.showinfo("FAULT: Position Radial Axis", "%s" %faultArray[i])
            acmd(ser, "ACKNOWLEDGEALL")

    root.after(1000, checkFaults)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        disableDrive(ser, axisNameArray)
        root.destroy()

def scanTimeUpdate():
    if(stateArray[4] == 1):
        #When scanIndex == 0, scanArray[0][3] == total scan time
        if(scanIndex == 0):
            totalSeconds = scanArray[scanIndex][3]
        #When scanIndex is greater than 0 but not larger than array so divide by zero never happens
        elif(scanIndex <= sizeofScanArray):
            #If scan circ axis is in position, and scan rad is moving
            if(abs(float(eScan_circ_position.get()) - scanArray[scanIndex][1]) < ERROR and abs(float(eScan_rad_position.get()) - scanArray[scanIndex][0]) > ERROR ):
                deltaMove = abs(scanArray[scanIndex][0] - scanArray[scanIndex - 1][0])
                deltaTime = abs(scanArray[scanIndex][3] - scanArray[scanIndex - 1][3])
                percentRemaining = abs(float(eScan_rad_position.get()) - scanArray[scanIndex][0]) / deltaMove
                totalSeconds = scanArray[scanIndex][3] + percentRemaining * deltaTime
            #If scan rad axis is in position, and scan circ is moving
            elif(abs(float(eScan_rad_position.get()) - scanArray[scanIndex][0]) < ERROR and abs(float(eScan_circ_position.get()) - scanArray[scanIndex][1]) > ERROR ):
                deltaMove = abs(scanArray[scanIndex][1] - scanArray[scanIndex - 1][1])
                deltaTime = abs(scanArray[scanIndex][3] - scanArray[scanIndex - 1][3])
                percentRemaining = abs(float(eScan_circ_position.get()) - scanArray[scanIndex][1]) / deltaMove
                totalSeconds = scanArray[scanIndex][3] + percentRemaining * deltaTime
            #Neither axis is moving, but ready to move on to next location
            else:
                totalSeconds = scanArray[scanIndex+1][3]

            hours = int(totalSeconds / 3600)
            mins = int((totalSeconds - (hours * 3600)) / 60)
            seconds = int(totalSeconds - hours*3600 - mins*60)
            scanTimeText.set(str(hours).zfill(2) + ":" + str(mins).zfill(2) + ":" + str(seconds).zfill(2))

    root.after(1000, scanTimeUpdate)

def nextScanMove():
    global scanIndex, sizeofScanArray
    checkBackTime = 50

    #Check if in scan mode
    if(stateArray[4] == 1):
        inPosA = int(acmd(ser, "AXISSTATUS(Drive_Axis_A)"))
        inPosB = int(acmd(ser, "AXISSTATUS(Drive_Axis_B)"))

        inPosA = (inPosA & 0b100) >> 2
        inPosB = (inPosB & 0b100) >> 2

        #Check if scan is complete
        if(scanIndex == sizeofScanArray and inPosA == 1 and inPosB == 1):
            #print("End Time: %f " %time.time())
            messagebox.showinfo("Scan Complete", "The Scan is completed")
            stopScan()
            root.after(checkBackTime, nextScanMove)
            return

        #If not in position then check back in 100 ms, otherwise get scan speed
        if(inPosA != 1 or inPosB != 1):
            root.after(checkBackTime, nextScanMove)
            return
        else:
            scanSpeed = sScanWindow_velocity.get()

        #Axes are in commanded position, get position of axes.
        pos_A = acmd(ser, "PFBKPROG(Drive_Axis_A)")
        pos_A = round(float(pos_A),5)
        pos_A = format(pos_A,'.3f')

        pos_B = acmd(ser, "PFBKPROG(Drive_Axis_B)")
        pos_B = round(float(pos_B),5)
        pos_B = format(pos_B,'.3f')


        #Check if commanded position equals scanArray vertex
        if(abs(float(pos_A) - scanArray[scanIndex][1]) < ERROR and abs(float(pos_B) - scanArray[scanIndex][0]) < ERROR):
            #Increment scanIndex
            scanIndex += 1

            #Convert in/sec to deg/sec
            convertedSpeed = (abs(scanArray[scanIndex -1][1] - scanArray[scanIndex][1])/(scanArray[scanIndex][2]/scanSpeed))
            if(convertedSpeed > MAX_CIRC_SPEED):
                convertedSpeed = MAX_CIRC_SPEED

            #Call next move; moveToVar(axis, location, speed)
            if(convertedSpeed):
                moveToVar(0,scanArray[scanIndex][1], convertedSpeed)
            moveToVar(1,scanArray[scanIndex][0], scanSpeed)
        #Axis are in a commanded position but that position does not equal current scanArray vertex
        else:
            #Move to scan starting location at a hard coded velocity
            if(scanIndex == 0):
                #Hard coded speed to start of scan
                convertedSpeed = 6
                scanSpeed = 0.5
            else:
                convertedSpeed = (abs(scanArray[scanIndex -1][1] - scanArray[scanIndex][1])/(scanArray[scanIndex][2]/scanSpeed))
                if(convertedSpeed > MAX_CIRC_SPEED):
                    convertedSpeed = MAX_CIRC_SPEED
            if(convertedSpeed):
                moveToVar(0,scanArray[scanIndex][1], convertedSpeed)
            moveToVar(1,scanArray[scanIndex][0], scanSpeed)

    #Check back in checkBackTime
    root.after(checkBackTime, nextScanMove)

def pauseScan():
    acmd(ser, "ABORT Drive_Axis_A")
    acmd(ser, "ABORT Drive_Axis_B")
    bScanWindow_Pause.config(state = "disabled")
    bScanWindow_Resume.config(state = "active")
    #Scan mode is paused change scan state
    stateArray[4] = 0

def resumeScan():
    #Resume scan state
    bScanWindow_Pause.config(state = "active")
    bScanWindow_Resume.config(state = "disabled")
    stateArray[4] = 1

def controllerReset(ser):
    #Reset the controller, wait and re-establish connection
    result = messagebox.askquestion("RESET?", "ALL position data will be lost and GUI will shutdown.\nAre you sure you want to reset controller?", icon='warning')
    if result == 'yes':
        acmd(ser, "RESET")
    else:
        return

#################################
#      Creation of GUI          #
#################################

root = Tk()

#Motion Control Window Size
root.geometry("725x650")
root.title("Tooling Inspection Motion Controller - Jet Pump Inspection Tool")

scanCircPosition = StringVar()
scanCircCurrent = StringVar()
scanRadPosition = StringVar()
scanRadCurrent = StringVar()
posCircPosition = StringVar()
posCircCurrent = StringVar()
posRadPosition = StringVar()
posRadCurrent = StringVar()

root.after(0, updateFBK)
root.after(500, checkFaults)
root.after(600, scanTimeUpdate)
root.after(700, nextScanMove)


#Create frames for GUI: Scan, Position, Scan Window
scan_frame = Frame(root, width = 500-6-20, height = 310, borderwidth = 2, relief = SUNKEN)
position_frame = Frame(root, width = 500-6-20, height = 310, borderwidth = 2, relief = SUNKEN)
scanWindow_frame = Frame(root, width = 225, height = 500, borderwidth = 2, relief = SUNKEN)
logoWindow_frame = Frame(root, width = 220, height = 120, borderwidth = 2, relief = SUNKEN)
scan_frame.grid_propagate(0)
position_frame.grid_propagate(0)
scanWindow_frame.grid_propagate(0)
logoWindow_frame.grid_propagate(0)


###############
#  Scan Frame #
###############

#Create Widgets for Scan Frame
bScan_CCW = Button(scan_frame, text = "CCW", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  width = 10, state = DISABLED)
bScan_CW = Button(scan_frame, text = "CW", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  width = 10, state = DISABLED)
bScan_ENABLE_circ = Button(scan_frame, text = "OFF", fg = "black", bg = "red",  height = 2, width = 6, padx = 3, pady = 3, command = lambda: enableAxisBtn(0))
bScan_Set_circ = Button(scan_frame, text = " Set ", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: setPos(0))
bScan_GoTo_circ = Button(scan_frame, text = "GoTo", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveTo(0))
bScan_Increment_circ = Button(scan_frame, text = "Index", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveInc(0))
eScan_circ_position = Entry(scan_frame, state = "readonly", width = 10, textvariable = scanCircPosition)
eScan_circ_current = Entry(scan_frame, state = "readonly", width = 10, textvariable = scanCircCurrent)
eScan_circ_set = Entry(scan_frame, width = 10)
eScan_circ_goto = Entry(scan_frame, width = 10)
eScan_circ_increment = Entry(scan_frame, width = 10)
sScan_circ_velocity = Scale(scan_frame, from_=0.5, to=MAX_CIRC_SPEED, orient=HORIZONTAL, length = 150, label = "            Velocity deg/s", resolution = 0.1)

bScan_IN = Button(scan_frame, text = "IN", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED)
bScan_OUT = Button(scan_frame, text = "OUT", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED)
bScan_ENABLE_rad = Button(scan_frame, text = "OFF", fg = "black", bg = "red",  height = 2, width = 6, padx = 3, pady = 3, command = lambda: enableAxisBtn(1))
bScan_Set_rad = Button(scan_frame, text = " Set ", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: setPos(1))
bScan_GoTo_rad = Button(scan_frame, text = "GoTo", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveTo(1))
bScan_Increment_rad = Button(scan_frame, text = "Index", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveInc(1))
eScan_rad_position = Entry(scan_frame, state = "readonly", width = 10, textvariable = scanRadPosition)
eScan_rad_current = Entry(scan_frame, state = "readonly", width = 10, textvariable = scanRadCurrent)
eScan_rad_set = Entry(scan_frame, width = 10)
eScan_rad_goto = Entry(scan_frame, width = 10)
eScan_rad_increment = Entry(scan_frame, width = 10)
sScan_rad_velocity = Scale(scan_frame, from_=0.01, to=.77, orient=HORIZONTAL, length = 150, label = "            Velocity in/s", resolution = 0.01)

lScan10 = Label(scan_frame, text = "Scan Circ", height = 2, font=("Helvetica", 14))
lScan11 = Label(scan_frame, text = "Scan Radial", height = 2, font=("Helvetica", 14))
lScan1 = Label(scan_frame, text = "Pos. (deg)")
lScan2 = Label(scan_frame, text = "Cur. (mA)")
lScan3 = Label(scan_frame, text = "Pos. (in)")
lScan4 = Label(scan_frame, text = "Cur. (mA)")

#Grid the Scan Frame
lScan10.grid(row = 0, column = 1, columnspan = 2)
bScan_ENABLE_circ.grid(row = 1, column = 0, rowspan = 3, padx = 15)
bScan_CCW.grid(row = 1, column = 1, rowspan = 2, padx = 3)
bScan_CW.grid(row = 1, column = 2, rowspan = 2, padx = 3)
lScan1.grid(row = 0, column = 3, columnspan = 2, sticky = S)
lScan2.grid(row = 0, column = 4, columnspan = 2, sticky = S)
eScan_circ_position.grid(row = 1, column = 3, columnspan =2, padx = 3)
eScan_circ_current.grid(row = 1, column = 4, columnspan = 2)

eScan_circ_set.grid(row = 3, column = 3, padx = 2)
eScan_circ_goto.grid(row = 3, column = 4, padx = 2)
eScan_circ_increment.grid(row = 3, column = 5, padx = 2)
bScan_Set_circ.grid(row = 4, column = 3, pady = 5)
bScan_GoTo_circ.grid(row = 4, column = 4, pady = 5)
bScan_Increment_circ.grid(row = 4, column = 5, pady = 5)

sScan_circ_velocity.grid(row = 3, column = 1, columnspan = 2, rowspan = 2)

scan_frame.grid_rowconfigure(5, minsize = 25)

lScan11.grid(row = 6, column = 1, columnspan = 2)
bScan_ENABLE_rad.grid(row = 7, column = 0, rowspan = 3, padx = 15)
bScan_IN.grid(row = 7, column = 1, rowspan = 2, padx = 3)
bScan_OUT.grid(row = 7, column = 2, rowspan = 2, padx = 3)
lScan3.grid(row = 6, column = 3, columnspan = 2, sticky = S)
lScan4.grid(row = 6, column = 4, columnspan = 2, sticky = S)
eScan_rad_position.grid(row = 7, column = 3, columnspan = 2, padx = 3)
eScan_rad_current.grid(row = 7, column = 4, columnspan = 2)

eScan_rad_set.grid(row = 9, column = 3, padx = 2)
eScan_rad_goto.grid(row = 9, column = 4, padx = 2)
eScan_rad_increment.grid(row = 9, column = 5, padx = 2)
bScan_Set_rad.grid(row = 10, column = 3, pady = 5)
bScan_GoTo_rad.grid(row = 10, column = 4, pady = 5)
bScan_Increment_rad.grid(row = 10, column = 5, pady = 5)


sScan_rad_velocity.grid(row = 9, column = 1, columnspan = 2, rowspan = 2)

###################
#  Position Frame #
###################

#Create Widgets for Position Frame
bPos_CCW = Button(position_frame, text = "CCW", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED, command = lambda: moveInc(2))
bPos_CW = Button(position_frame, text = "CW", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED, command = lambda: moveInc(2))
bPos_ENABLE_circ = Button(position_frame, text = "OFF", fg = "black", bg = "red",  height = 2, width = 6, padx = 3, pady = 3, command = lambda: enableAxisBtn(2))
bPos_Set_circ = Button(position_frame, text = " Set ", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: setPos(2))
bPos_GoTo_circ = Button(position_frame, text = "GoTo", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveTo(2))
bPos_Increment_circ = Button(position_frame, text = "Index", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveInc(2))
ePos_circ_position = Entry(position_frame, state = "readonly", width = 10, textvariable = posCircPosition)
ePos_circ_current = Entry(position_frame, state = "readonly", width = 10, textvariable = posCircCurrent)
ePos_circ_set = Entry(position_frame, width = 10)
ePos_circ_goto = Entry(position_frame, width = 10)
ePos_circ_increment = Entry(position_frame, width = 10)
sPos_circ_velocity = Scale(position_frame, from_=0.01, to=.77, orient=HORIZONTAL, length = 150, label = "            Velocity in/s", resolution = 0.01)

bPos_IN = Button(position_frame, text = "IN", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  width = 10, state = DISABLED, command = lambda: moveInc(3))
bPos_OUT = Button(position_frame, text = "OUT", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  width = 10, state = DISABLED, command = lambda: moveInc(3))
bPos_ENABLE_rad = Button(position_frame, text = "OFF", fg = "black", bg = "red",  height = 2, width = 6, padx = 3, pady = 3, command = lambda: enableAxisBtn(3))
bPos_Set_rad = Button(position_frame, text = " Set ", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: setPos(3))
bPos_GoTo_rad = Button(position_frame, text = "GoTo", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveTo(3))
bPos_Increment_rad = Button(position_frame, text = "Index", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00",  state = DISABLED, command = lambda: moveInc(3))
ePos_rad_position = Entry(position_frame, state = "readonly", width = 10, textvariable = posRadPosition)
ePos_rad_current = Entry(position_frame, state = "readonly", width = 10, textvariable = posRadCurrent)
ePos_rad_set = Entry(position_frame, width = 10)
ePos_rad_goto = Entry(position_frame, width = 10)
ePos_rad_increment = Entry(position_frame, width = 10)
sPos_rad_velocity = Scale(position_frame, from_=0.01, to=.77, orient=HORIZONTAL, length = 150, label = "            Velocity in/s", resolution = 0.01)

lPos10 = Label(position_frame, text = "Position Circ", height = 2, font=("Helvetica", 14))
lPos11 = Label(position_frame, text = "Position Radial", height = 2, font=("Helvetica", 14))
lPos1 = Label(position_frame, text = "Pos. (in)")
lPos2 = Label(position_frame, text = "Cur. (mA)")
lPos3 = Label(position_frame, text = "Pos. (in)")
lPos4 = Label(position_frame, text = "Cur. (mA)")

#Grid the Position Frame
lPos10.grid(row = 0, column = 1, columnspan = 2)
bPos_ENABLE_circ.grid(row = 1, column = 0, rowspan = 3, padx = 15)
bPos_CCW.grid(row = 1, column = 1, rowspan = 2, padx = 3)
bPos_CW.grid(row = 1, column = 2, rowspan = 2, padx = 3)
lPos1.grid(row = 0, column = 3, columnspan = 2, sticky = S)
lPos2.grid(row = 0, column = 4, columnspan = 2, sticky = S)
ePos_circ_position.grid(row = 1, column = 3, columnspan = 2, padx = 3)
ePos_circ_current.grid(row = 1, column = 4, columnspan = 2)

ePos_circ_set.grid(row = 3, column = 3, padx = 2)
ePos_circ_goto.grid(row = 3, column = 4, padx = 2)
ePos_circ_increment.grid(row = 3, column = 5, padx = 2)
bPos_Set_circ.grid(row = 4, column = 3, pady = 5)
bPos_GoTo_circ.grid(row = 4, column = 4, pady = 5)
bPos_Increment_circ.grid(row = 4, column = 5, pady = 5)

sPos_circ_velocity.grid(row = 3, column = 1, columnspan = 2, rowspan = 2)

position_frame.grid_rowconfigure(5, minsize = 25)

lPos11.grid(row = 6, column = 1, columnspan = 2)
bPos_ENABLE_rad.grid(row = 7, column = 0, rowspan = 3, padx = 15)
bPos_IN.grid(row = 7, column = 1, rowspan = 2, padx = 3)
bPos_OUT.grid(row = 7, column = 2, rowspan = 2, padx = 3)
lPos3.grid(row = 6, column = 3, columnspan = 2, sticky = S)
lPos4.grid(row = 6, column = 4, columnspan = 2, sticky = S)
ePos_rad_position.grid(row = 7, column = 3, columnspan = 2, padx = 3)
ePos_rad_current.grid(row = 7, column = 4, columnspan = 2)

ePos_rad_set.grid(row = 9, column = 3, padx = 2)
ePos_rad_goto.grid(row = 9, column = 4, padx = 2)
ePos_rad_increment.grid(row = 9, column = 5, padx = 2)
bPos_Set_rad.grid(row = 10, column = 3, pady = 5)
bPos_GoTo_rad.grid(row = 10, column = 4, pady = 5)
bPos_Increment_rad.grid(row = 10, column = 5, pady = 5)


sPos_rad_velocity.grid(row = 9, column = 1, columnspan = 2, rowspan = 2)


######################
#  Scan Window Frame #
######################

#Sting and Integer values for radio buttons
v = IntVar()
d = IntVar()
scanStartText = StringVar()
scanStopText = StringVar()
indexStartText = StringVar()
indexStopText = StringVar()
indexSizeText = StringVar()
scanTimeText = StringVar()
scanStartText.set("Scan Start (deg)")
scanStopText.set("Scan Stop (deg)")
indexStartText.set("Index Start (in)")
indexStopText.set("Index Stop (in)")
indexSizeText.set("Index Size (in)")
scanTimeText.set("00:00:00")

#Create Widgets for Scan Window Frame
bScanWindow_Start = Button(scanWindow_frame, text = "START", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, command = initScan)
bScanWindow_Stop = Button(scanWindow_frame, text = "STOP", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED, command = stopScan)
bScanWindow_Pause = Button(scanWindow_frame, text = "PAUSE", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED, command = pauseScan)
bScanWindow_Resume = Button(scanWindow_frame, text = "RESUME", activeforeground = "black", activebackground = "#00aa00", bg = "#00aa00", width = 10, state = DISABLED, command = resumeScan)
eScanWindow_time = Entry(scanWindow_frame, state = "readonly", width = 10, textvariable = scanTimeText)
radio1 = Radiobutton(scanWindow_frame, text = "     Circ                 Radial", variable = v, value = 0, command = changeUnits)
radio2 = Radiobutton(scanWindow_frame, text = "     Radial              Circ", variable = v, value = 1, command = changeUnits)
radio3 = Radiobutton(scanWindow_frame, text = "Bi-directional", variable = d, value = 0)
radio4 = Radiobutton(scanWindow_frame, text = "Uni-directional", variable = d, value = 1)
eScanWindow_scanStart = Entry(scanWindow_frame, width = 10)
eScanWindow_scanStop = Entry(scanWindow_frame,  width = 10)
eScanWindow_indexStart = Entry(scanWindow_frame,  width = 10)
eScanWindow_indexStop = Entry(scanWindow_frame,  width = 10)
eScanWindow_indexSize = Entry(scanWindow_frame,  width = 10)

sScanWindow_velocity = Scale(scanWindow_frame, from_=0.01, to=0.5, orient=HORIZONTAL, length = 150, label = "            Velocity in/s", resolution = 0.01)

lScanWindow0 = Label(scanWindow_frame, text = "Scan Window", height = 2, font=("Helvetica", 14))
lScanWindow1 = Label(scanWindow_frame, text = "Remaining Time")
lScanWindow2 = Label(scanWindow_frame, text = "Scan Axis       Index Axis")
lScanWindow3 = Label(scanWindow_frame, text = "---------------------------")
lScanWindow4 = Label(scanWindow_frame, textvariable = scanStartText)
lScanWindow5 = Label(scanWindow_frame, textvariable = scanStopText)
lScanWindow6 = Label(scanWindow_frame, textvariable = indexStartText)
lScanWindow7 = Label(scanWindow_frame, textvariable = indexStopText)
lScanWindow8 = Label(scanWindow_frame, textvariable = indexSizeText)

#Grid the Scan Window Frame
bScanWindow_Start.grid(row = 1, column = 0, pady = 5, padx = 5)
bScanWindow_Stop.grid(row = 1, column = 1, pady = 5, padx = 5)
bScanWindow_Pause.grid(row = 2, column = 0, pady = 5, padx = 5)
bScanWindow_Resume.grid(row = 2, column = 1, pady = 5, padx = 5)
lScanWindow1.grid(row = 3, column = 0, columnspan = 2)
eScanWindow_time.grid(row = 4, column = 0, columnspan = 2)
scanWindow_frame.grid_rowconfigure(5, minsize = 15)
lScanWindow2.grid(row = 6, column = 0, columnspan = 2, sticky = S)
lScanWindow3.grid(row = 7, column = 0, columnspan = 2, sticky = N)
radio1.grid(row = 8, column = 0, columnspan = 2, sticky = W)
radio2.grid(row = 9, column = 0, columnspan = 2, sticky = W)
sScanWindow_velocity.grid(row = 10, columnspan = 2, pady =10)
eScanWindow_scanStart.grid(row = 11, column = 1)
eScanWindow_scanStop.grid(row = 12, column = 1)
eScanWindow_indexStart.grid(row = 13, column = 1)
eScanWindow_indexStop.grid(row = 14, column = 1)
eScanWindow_indexSize.grid(row = 15, column = 1)
lScanWindow4.grid(row = 11, column = 0, sticky = E)
lScanWindow5.grid(row = 12, column = 0, sticky = E)
lScanWindow6.grid(row = 13, column = 0, sticky = E)
lScanWindow7.grid(row = 14, column = 0, sticky = E)
lScanWindow8.grid(row = 15, column = 0, sticky = E)
radio3.grid(row = 16, column = 0, sticky = S, pady = 8)
radio4.grid(row = 16, column = 1, sticky = S, pady = 8)
scanWindow_frame.grid_columnconfigure(0, minsize = 100)

lScanWindow0.grid(row = 0, column = 0, columnspan = 2, sticky = W)

######################
# Logo Window Frame  #
######################

photo = PhotoImage(file = "General_Electric_logo_Small.png" )
bLogoWindow_Reset = Button(logoWindow_frame, text = "RESET",  width = 10, relief = RAISED, command = lambda: controllerReset(ser))
logoLabel = Label(logoWindow_frame, image = photo)
geHitachi = Label(logoWindow_frame, text = "GE HITACHI")
timc = Label(logoWindow_frame, text = "  Tooling Inspection Motion Controller")
toolName = Label(logoWindow_frame, text = "  Access Hole Cover")
logoLabel.grid(row = 0, column = 0, sticky = E)
geHitachi.grid(row = 0, column = 1, sticky = W)
timc.grid(row = 1, column = 0, columnspan = 2)
toolName.grid(row = 2, column = 0, columnspan = 2)
logoWindow_frame.grid_columnconfigure(0, minsize = 60)
bLogoWindow_Reset.grid(row = 3, columnspan = 2)


#Create status bar and menu objects
#status = Label(root, text = "Future Status Bar?", bd = 1, relief = SUNKEN, anchor = W )
#status.pack(side = BOTTOM, fill = X)

################
# Grid Frames  #
################
scan_frame.grid(row = 0, column = 0, padx = 5, pady = 5)
position_frame.grid(row = 1, column = 0, padx = 6, pady =6)
scanWindow_frame.grid(row = 0, column = 1, rowspan = 2, sticky = N, padx = 6, pady = 6)
logoWindow_frame.grid(row = 1, column = 1,sticky = SE, padx = 6, pady = 6)

#Bind jog buttons to mouse click
bScan_CCW.bind('<ButtonPress-1>', lambda event, axis = 0, direction = "backward": startJog(axis, direction))
bScan_CCW.bind('<ButtonRelease-1>', lambda event, axis = 0: stopJog(axis))
bScan_CW.bind('<ButtonPress-1>', lambda event, axis = 0, direction = "forward": startJog(axis, direction))
bScan_CW.bind('<ButtonRelease-1>', lambda event, axis = 0: stopJog(axis))

bScan_IN.bind('<ButtonPress-1>', lambda event, axis = 1, direction = "backward": startJog(axis, direction))
bScan_IN.bind('<ButtonRelease-1>', lambda event, axis = 1: stopJog(axis))
bScan_OUT.bind('<ButtonPress-1>', lambda event, axis = 1, direction = "forward": startJog(axis, direction))
bScan_OUT.bind('<ButtonRelease-1>', lambda event, axis = 1: stopJog(axis))

bPos_CCW.bind('<ButtonPress-1>', lambda event, axis = 2, direction = "backward": startJog(axis, direction))
bPos_CCW.bind('<ButtonRelease-1>', lambda event, axis = 2: stopJog(axis))
bPos_CW.bind('<ButtonPress-1>', lambda event, axis = 2, direction = "forward": startJog(axis, direction))
bPos_CW.bind('<ButtonRelease-1>', lambda event, axis = 2: stopJog(axis))


bPos_IN.bind('<ButtonPress-1>', lambda event, axis = 3, direction = "backward": startJog(axis, direction))
bPos_IN.bind('<ButtonRelease-1>', lambda event, axis = 3: stopJog(axis))
bPos_OUT.bind('<ButtonPress-1>', lambda event, axis = 3, direction = "forward": startJog(axis, direction))
bPos_OUT.bind('<ButtonRelease-1>', lambda event, axis = 3: stopJog(axis))

menu = Menu(root)
root.config(menu = menu)
subMenu = Menu(menu)
menu.add_cascade(label = "File", menu = subMenu)
subMenu.add_command(label = "Exit", command = root.quit)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
