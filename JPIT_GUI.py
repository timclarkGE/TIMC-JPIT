from tkinter import *
from tkinter import messagebox
import serial
import datetime
import time
#Websites about Class and GUI
#https://jeffknupp.com/blog/2014/06/18/improve-your-python-python-classes-and-object-oriented-programming/
#http://python-textbok.readthedocs.io/en/1.0/Object_Oriented_Programming.html
#http://python-textbok.readthedocs.io/en/1.0/Introduction_to_GUI_Programming.html

#Threading
#https://www.troyfawkes.com/learn-python-multithreading-queues-basics/



gui_width=485
gui_height=600

class SetupScanheadFrame:
    def __init__(self):
        self.axisName = "SCANHEAD"
        self.axisUnits = "deg"
        self.jogText1 = "CCW"
        self.jogText2 = "CW"
        self.speedMin = 0.5
        self.speedMax = 15
        self.speedRes = 0.5
        self.maxError = 0.22


class SetupPusherFrame:
    def __init__(self):
        self.axisName = "PUSHER"
        self.axisUnits = "in"
        self.jogText1 = "UP"
        self.jogText2 = "DOWN"
        self.speedMin = 0.05
        self.speedMax = 1
        self.speedRes = 0.05
        self.maxError = 1

class SetupScanFrame:
    def __init__(self):
        self.axisName = "SCAN WINDOW"
        self.scanSpeedMin = 0.5
        self.scanSpeedMax = 15
        self.scanSpeedRes = 0.5
        self.indexSpeedMin = 0.05
        self.indexSpeedMax = 1
        self.indexSpeedRes = 0.05
        self.scanAxisUnits = "deg"
        self.indexAxisUnits = "in"


#Will create an axis frame with all buttons, entry boxes, and scales
class AxisFrame:
    def __init__(self, master, parameters):
        frame = Frame(master, borderwidth=2, relief=SUNKEN)
        self.canvas = Canvas(frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        frame.pack(fill=X, padx=5, pady=5)
        frame.pack()

        self.state = 0
        self.axisName = parameters.axisName
        self.max_pos_error = parameters.maxError
        self.mtr_position = StringVar()
        self.mtr_current = StringVar()
        self.mtr_error = StringVar()

        self.enableButton = Button(self.canvas, text="OFF", fg="black", bg="#d3d3d3", height=2, width=6, padx=3, pady=3,
                                   command=lambda: self.toggle_axis())
        self.jog_fwd = Button(self.canvas, text=parameters.jogText1, activeforeground="black", activebackground="#00aa00",
                              bg="#00aa00", width=10, state=DISABLED)
        self.jog_rev = Button(self.canvas, text=parameters.jogText2, activeforeground="black", activebackground="#00aa00",
                              bg="#00aa00", width=10, state=DISABLED)
        self.set_pos = Button(self.canvas, text=" Set ", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                             state=DISABLED, command=lambda: self.set_position())
        self.go_to = Button(self.canvas, text="GoTo", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                           state=DISABLED, command=lambda: self.move_to())
        self.inc = Button(self.canvas, text="Index", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                          state=DISABLED, command=lambda: self.move_inc())
        self.mtrPositionBox = Entry(self.canvas, state="readonly", width=10, textvariable=self.mtr_position)
        self.mtrCurrentBox = Entry(self.canvas, state="readonly", width=10, textvariable=self.mtr_current)
        #self.placeHolder = Entry(canvas, state="readonly", width=10, textvariable=self.mtrError)
        self.e_setPos = Entry(self.canvas, width=10)
        self.e_goTo = Entry(self.canvas, width=10)
        self.e_inc = Entry(self.canvas, width=10)
        self.vel = Scale(self.canvas, from_=parameters.speedMin, to=parameters.speedMax, orient=HORIZONTAL, length=150,
                         label="            Velocity " + parameters.axisUnits + "/sec", resolution=parameters.speedRes)
        self.vel.set((parameters.speedMax-parameters.speedMin)*0.25)
        self.vel.config(state="disabled")
        self.label_0 = Label(self.canvas, text=parameters.axisName, height=1, font=("Helvetica", 14))
        self.label_1 = Label(self.canvas, text="Pos. ("+parameters.axisUnits+")")
        self.label_2 = Label(self.canvas, text="Cur. (mA)")
        self.label_3 = Label(self.canvas, text="Pos. Error")

        #Draw box for position error that looks like disabled entry box.
        self.canvas.create_line(400, 29, 463, 29, fill="#A0A0A0")
        self.canvas.create_line(400, 29, 400, 47, fill="#A0A0A0")
        self.canvas.create_line(400, 47, 464, 47, fill="white")
        self.canvas.create_line(463, 51, 463, 48, fill="white")

        #GRID
        self.label_0.grid(row = 0, column = 0, columnspan=5, sticky=W)
        self.enableButton.grid(row=1, column=0, rowspan=3, padx=15)
        self.jog_fwd.grid(row=1, column=1, rowspan=2, padx=3)
        self.jog_rev.grid(row=1, column=2, rowspan=2, padx=3)
        self.label_1.grid(row=0, column=3, sticky=S)
        self.label_2.grid(row=0, column=4, sticky=S)
        self.label_3.grid(row=0, column=5, sticky=S)
        self.mtrPositionBox.grid(row=1, column=3, padx=3)
        self.mtrCurrentBox.grid(row=1, column=4, padx=3)
        #self.placeHolder.grid(row=1, column=5, padx=3)
        self.e_setPos.grid(row=3, column=3, padx=2)
        self.e_goTo.grid(row=3, column=4, padx=2)
        self.e_inc.grid(row=3, column=5, padx=2)
        self.set_pos.grid(row=4, column=3, pady=5)
        self.go_to.grid(row=4, column=4, pady=5)
        self.inc.grid(row=4, column=5, pady=5)
        self.vel.grid(row = 3, column = 1, columnspan = 2, rowspan = 2)

        self.jog_fwd.bind('<ButtonPress-1>', lambda event: self.jog_forward())
        self.jog_fwd.bind('<ButtonRelease-1>', lambda event: self.stop_jog())
        self.jog_rev.bind('<ButtonPress-1>', lambda event: self.jog_backward())
        self.jog_rev.bind('<ButtonRelease-1>', lambda event: self.stop_jog())
        self.canvas.bind('<ButtonPress-2>', lambda event: self.updatePosError(self.canvas,25))
        #canvas.bind('<ButtonPress-2>', lambda event: print(event.x, event.y))


    def toggle_axis(self):
        if(self.state == 0):
            self.enable_axis()
        elif(self.state == 1):
            self.disable_axis()

    def enable_axis(self):
        acmd(ser, "ENABLE " + self.axisName)
        if ((0b1 & int(acmd(ser, "AXISSTATUS(" + self.axisName + ")"))) == 1):
            self.state=1
            self.activate_all_btns()

    def disable_axis(self):
        acmd(ser, "DISABLE " + self.axisName)
        if ((0b1 & int(acmd(ser, "AXISSTATUS(" + self.axisName + ")"))) == 0):
            self.enableButton.config(text="OFF", bg="#d3d3d3")
            self.state=0
            self.inactivate_all_btns(FALSE)

    def inactivate_all_btns(self, value):
        if(value):
            self.enableButton.config(state="disabled")
        self.jog_fwd.config(state="disabled")
        self.jog_rev.config(state="disabled")
        self.set_pos.config(state="disabled")
        self.go_to.config(state="disabled")
        self.inc.config(state="disabled")
        self.vel.config(state="disabled")

    def activate_all_btns(self):
        self.enableButton.config(text="ON", bg="#00aa00")
        self.jog_fwd.config(state="active")
        self.jog_rev.config(state="active")
        self.set_pos.config(state="active")
        self.go_to.config(state="active")
        self.inc.config(state="active")
        self.vel.config(state="active")

    def set_position(self):
        posToSet = str(self.e_setPos.get())
        acmd(ser, "POSOFFSET SET " + self.axisName + ", " + posToSet)

    def move_to(self):
        distance = str(self.e_goTo.get())
        if (distance == ""):
            return
        speed = str(self.vel.get())
        acmd(ser, "MOVEABS " + self.axisName + " " + distance + " F " + speed)

    def move_inc(self):
        acmd(ser, "ABORT " + self.axisName)
        distance = str(self.e_inc.get())
        speed = str(self.vel.get())
        acmd(ser, "MOVEINC " + self.axisName + " " + distance + " F " + speed)

    def jog_forward(self):
        if(self.state == 1 and self.enableButton['state'] != 'disabled'):
            acmd(ser, "ABORT " + self.axisName)
            speed = str(self.vel.get())
            acmd(ser, "FREERUN " + self.axisName + " " + speed)

    def jog_backward(self):
        if (self.state == 1 and self.enableButton['state'] != 'disabled'):
            acmd(ser, "ABORT " + self.axisName)
            speed = str(-1*self.vel.get())
            acmd(ser, "FREERUN " + self.axisName + " " + speed)

    def stop_jog(self):
        acmd(ser, "FREERUN " + self.axisName + " 0")

    #Update Feedback
    def update_fbk(self):
        pos = acmd(ser, "PFBKPROG(" + self.axisName + ")")
        pos = round(float(pos), 2)
        pos = format(pos, '.2f')
        self.mtr_position.set(pos)

        cur = acmd(ser, "IFBK(" + self.axisName + ")")
        cur = float(cur) * 1000
        cur = round(cur)
        self.mtr_current.set(cur)

        test = acmd(ser, "PERR(" + self.axisName + ")")
        test = test.replace("\n", "")
        error = float(test)
        self.updatePosError(self.canvas, error)

        root.after(75, self.update_fbk)

    def updatePosError(self, canvas, error):
        #TODO check this later when in the mockup.
        #Max Error for x1 = 401+61 = 462
        calc_error = int((error/self.max_pos_error)*61)
        x0 = 401
        y0 = 30
        x1 = x0+calc_error
        y1 = 46
        canvas.create_rectangle(x0,y0,x1,y1,fill="red", outline="red")



#Will create a scan frame with all buttons, entry boxes, and scales
class ScanFrame:
    def __init__(self, master, parameters):

        mainFrame = Frame(master, borderwidth=2, relief=SUNKEN)
        topFrame = Frame(mainFrame)
        leftFrame = Frame(mainFrame)
        middleFrame = Frame(mainFrame)
        rightFrame = Frame(mainFrame)

        rightFrame.grid(row=1, column=2)
        middleFrame.grid(row=1, column=1)
        leftFrame.grid(row=1, column=0)
        topFrame.grid(row=0, column=0, columnspan=3)
        mainFrame.pack(fill=X, padx=5, pady=5)
        mainFrame.pack()

        scanType = IntVar()
        scanTimeText = StringVar()
        scanTimeText.set("00:00:00")

        #LEFT FRAME WIDGETS
        self.start = Button(topFrame, text="START", activeforeground="black", activebackground="#00aa00",
                       bg="#00aa00", width=10, command=lambda: start_scan(self))
        self.stop = Button(topFrame, text="STOP", activeforeground="black", activebackground="#00aa00",
                      bg="#00aa00", width=10, state=DISABLED, command=lambda: start_scan(self))
        self.pause = Button(topFrame, text="PAUSE", activeforeground="black", activebackground="#00aa00",
                       bg="#00aa00", width=10, state=DISABLED, command=lambda: start_scan(self))
        self.resume = Button(topFrame, text="RESUME", activeforeground="black",
                        activebackground="#00aa00", bg="#00aa00", width=10, state=DISABLED,
                        command=lambda: start_scan(self))
        self.scanVelocity = Scale(leftFrame, from_=parameters.scanSpeedMin, to=parameters.scanSpeedMax,
                                  orient=HORIZONTAL,
                                  length=150,
                                  label="        Scan Speed " + parameters.scanAxisUnits + "/sec",
                                  resolution=parameters.scanSpeedRes)
        self.indexVelocity = Scale(leftFrame, from_=parameters.indexSpeedMin, to=parameters.indexSpeedMax,
                                   orient=HORIZONTAL,
                                   length=150,
                                   label="        Index Speed " + parameters.indexAxisUnits + "/sec",
                                   resolution=parameters.indexSpeedRes)

        self.label_0 = Label(topFrame, text=parameters.axisName, height=1, font=("Helvetica", 14))
        self.label_1 = Label(rightFrame, text="Scan Start (deg)")
        self.label_2 = Label(rightFrame, text="Scan Stop (deg)")
        self.label_3 = Label(rightFrame, text="Index Start (in)")
        self.label_4 = Label(rightFrame, text="Index Stop (in)")
        self.label_5 = Label(rightFrame, text="Index Size (in)")
        self.label_6 = Label(middleFrame, text="Remaining Time")

        self.e_scanStart = Entry(rightFrame, width=10)
        self.e_scanStop = Entry(rightFrame, width=10)
        self.e_indexStart = Entry(rightFrame, width=10)
        self.e_indexStop = Entry(rightFrame, width=10)
        self.e_indexSize = Entry(rightFrame, width=10)
        self.radio_0 = Radiobutton(middleFrame, text="Bi-directional", variable=scanType, value=0)
        self.radio_1 = Radiobutton(middleFrame, text="Uni-directional", variable=scanType, value=1)
        self.time = Entry(middleFrame, state="readonly", width=10, textvariable=scanTimeText)

        #GRID TOP
        rowSpaceTop=15
        self.label_0.grid(row=0, column=0, sticky=W)
        self.start.grid(row=1, column=0, pady=5, padx=rowSpaceTop)
        self.stop.grid(row=1, column=1, pady=5, padx=rowSpaceTop)
        self.pause.grid(row=1, column=2, pady=5, padx=rowSpaceTop)
        self.resume.grid(row=1, column=3, pady=5, padx=rowSpaceTop)

        #GRID LEFT
        self.scanVelocity.grid(row=0, column=0, padx=5)
        self.indexVelocity.grid(row=1, column=0, padx=5, pady=5)

        # GRID MIDDLE
        middleFrame.grid_rowconfigure(2,minsize=20)
        self.radio_0.grid(row=0, column=0, sticky=W, padx=20)
        self.radio_1.grid(row=1, column=0, sticky=W, padx=20)
        self.label_6.grid(row=3, column=0)
        self.time.grid(row=4, column=0)

        #GRID RIGHT
        rowSpaceRight=1
        self.label_1.grid(row=2, column=3, pady=rowSpaceRight)
        self.label_2.grid(row=3, column=3, pady=rowSpaceRight)
        self.label_3.grid(row=4, column=3, pady=rowSpaceRight)
        self.label_4.grid(row=5, column=3, pady=rowSpaceRight)
        self.label_5.grid(row=6, column=3, pady=rowSpaceRight)
        self.e_scanStart.grid(row=2, column=4)
        self.e_scanStop.grid(row=3, column=4)
        self.e_indexStart.grid(row=4, column=4)
        self.e_indexStop.grid(row=5, column=4)
        self.e_indexSize.grid(row=6, column=4)

        def start_scan(self):
            scanhead.inactivate_all_btns(TRUE)
            pusher.inactivate_all_btns(TRUE)

            #Create Scan Points



class FaultFrame():
    def __init__(self, master):
        frame = Frame(master, borderwidth=2, relief=SUNKEN)
        canvas = Canvas(frame, highlightthickness=0)
        canvas.grid(row=0, column=0)
        frame.pack(fill=X, padx=5, pady=5)
        frame.pack()
        self.status = StringVar()

        self.label_0 = Label(canvas, text="FAULT STATUS", height=1, font=("Helvetica", 14))
        self.button = Button(canvas, text="FAULT\nRESET", fg="black", bg="#d3d3d3", height=2, width=5, state=DISABLED)
        #self.label_0 = Label(canvas, text="GE HITACHI", height=2, font=("Helvetica", 10))
        self.entry = Entry(canvas, width=59, textvariable = self.status)
        self.label_0.grid(row=0, column=0, columnspan=2, sticky=W)
        self.entry.grid(row=1, column=0, columnspan=2, padx=30)
        self.button.grid(row=1,column=2, pady=5, padx=5)


def init_com():
    port = "COM"
    baud = 115200

    serialError = 0

    for x in range(1, 100):
         try:
             ser = serial.Serial(port+str(x), baud, timeout = 0.05)
         except Exception as e:
             serialError = serialError + 1
    if serialError >= 99:
          return 0
    if ser.isOpen():
        ser.write(b'ACKNOWLEDGEALL\n')
        data = ser.readline().decode('ascii')
        if "%" in data:
            return ser
        else:
            ser.close()
            return 0

def on_closing():
    try:
        ser.close()
    except:
        print("No Serial Port to Close")

    root.destroy()


def acmd(ser, text):
    ser.write(text.encode('ascii') + b' \n')
    data = ser.readline().decode('ascii')
    if "!" in data:
        fault.status.set("Bad Execution")
        return 0
    elif "#" in data:
        fault.status.set("Ack but cannot execute")
        return 0
    elif "$" in data:
        fault.status.set("Command timed out")
        return 0
    elif data == "":
        fault.status.set("No data, check serial connection")
        return 0
    else:
        data = data.replace("%", "")
        fault.status.set("Success :"+data)
        return data






######################################
#             Main Code              #
######################################

# Open serial connection and test for communication with the Ensemble
ser = init_com()

#Create the GUI window
root = Tk()
root.geometry(str(gui_width)+"x"+str(gui_height))
root.title("Tooling Inspection Motion Controller - Jet Pump Inspection Tool")
#Create the frames of the GUI
scanhead = AxisFrame(root, SetupScanheadFrame())
pusher = AxisFrame(root, SetupPusherFrame())
scan = ScanFrame(root, SetupScanFrame())
fault = FaultFrame(root)

root.after(75, scanhead.update_fbk())
root.after(75, pusher.update_fbk())

#Check if serial communication
if(ser == 0):
    fault.status.set("No Communication with Ensemble")
elif(ser.isOpen()):
    fault.status.set("Communication with Ensemble on "+ser.name)
    acmd(ser, "WAIT MODE NOWAIT")

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

