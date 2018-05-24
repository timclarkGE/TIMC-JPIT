from tkinter import *
from tkinter import messagebox
#Websites about Class and GUI
#https://jeffknupp.com/blog/2014/06/18/improve-your-python-python-classes-and-object-oriented-programming/
#http://python-textbok.readthedocs.io/en/1.0/Object_Oriented_Programming.html
#http://python-textbok.readthedocs.io/en/1.0/Introduction_to_GUI_Programming.html

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
        self.driveName = "Drive_AXIS_A"


class SetupPusherFrame:
    def __init__(self):
        self.axisName = "PUSHER"
        self.axisUnits = "in"
        self.jogText1 = "UP"
        self.jogText2 = "DOWN"
        self.speedMin = 0.05
        self.speedMax = 1
        self.speedRes = 0.05
        self.driveName = "Drive_AXIS_B"

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
        canvas = Canvas(frame, highlightthickness=0)
        canvas.grid(row=0, column=0)
        frame.pack(fill=X, padx=5, pady=5)
        frame.pack()

        self.mtrPosition = StringVar()
        self.mtrCurrent = StringVar()
        self.mtrError = StringVar()

        self.enableButton = Button(canvas, text="OFF", fg="black", bg="#d3d3d3", height=2, width=6, padx=3, pady=3,
                                   command=lambda: self.enableAxis())
        self.jog_fwd = Button(canvas, text=parameters.jogText1, activeforeground="black", activebackground="#00aa00",
                              bg="#00aa00", width=10, state=DISABLED)
        self.jog_rev = Button(canvas, text=parameters.jogText2, activeforeground="black", activebackground="#00aa00",
                              bg="#00aa00", width=10, state=DISABLED)
        self.setPos = Button(canvas, text=" Set ", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                             state=DISABLED, command=lambda: self.setPosition())
        self.goTo = Button(canvas, text="GoTo", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                           state=DISABLED, command=lambda: self.moveTo())
        self.inc = Button(canvas, text="Index", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                          state=DISABLED, command=lambda: self.moveInc())
        self.mtrPositionBox = Entry(canvas, state="readonly", width=10, textvariable=self.mtrPosition)
        self.mtrCurrentBox = Entry(canvas, state="readonly", width=10, textvariable=self.mtrCurrent)
        #self.placeHolder = Entry(canvas, state="readonly", width=10, textvariable=self.mtrError)
        self.e_setPos = Entry(canvas, width=10)
        self.e_goTo = Entry(canvas, width=10)
        self.e_inc = Entry(canvas, width=10)
        self.vel = Scale(canvas, from_=parameters.speedMin, to=parameters.speedMax, orient=HORIZONTAL, length=150,
                         label="            Velocity " + parameters.axisUnits + "/sec", resolution=parameters.speedRes)
        self.label_0 = Label(canvas, text=parameters.axisName, height=1, font=("Helvetica", 14))
        self.label_1 = Label(canvas, text="Pos. ("+parameters.axisUnits+")")
        self.label_2 = Label(canvas, text="Cur. (mA)")
        self.label_3 = Label(canvas, text="Pos. Error")

        #Draw box for position error that looks like disabled entry box.
        canvas.create_line(400, 29, 463, 29, fill="#A0A0A0")
        canvas.create_line(400, 29, 400, 47, fill="#A0A0A0")
        canvas.create_line(400, 47, 464, 47, fill="white")
        canvas.create_line(463, 51, 463, 48, fill="white")

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
        self.setPos.grid(row=4, column=3, pady=5)
        self.goTo.grid(row=4, column=4, pady=5)
        self.inc.grid(row=4, column=5, pady=5)
        self.vel.grid(row = 3, column = 1, columnspan = 2, rowspan = 2)

        self.jog_fwd.bind('<ButtonPress-1>', lambda event: self.jogForward())
        self.jog_fwd.bind('<ButtonRelease-1>', lambda event: self.stopJog())
        self.jog_rev.bind('<ButtonPress-1>', lambda event: self.jogBackward())
        self.jog_rev.bind('<ButtonRelease-1>', lambda event: self.stopJog())
        canvas.bind('<ButtonPress-2>', lambda event: self.updatePosError(canvas,25))
        #canvas.bind('<ButtonPress-2>', lambda event: print(event.x, event.y))


    #TODO, create function isEnabled

    def enableAxis(self):
        #acmd(ser, "ENABLE " + axisNameArray[axis])
        #if ((0b1 & int(acmd(ser, "AXISSTATUS(" + axisNameArray[axis] + ")"))) == 1):
        self.enableButton.config(text="ON", bg="#00aa00")
        self.jog_fwd.config(state="active")
        self.jog_rev.config(state="active")
        self.setPos.config(state="active")
        self.goTo.config(state="active")
        self.inc.config(state="active")
            #stateArray[axis] = 1

    def setPosition(self):
        posToSet = str(self.e_setPos.get())
        #acmd(ser, "POSOFFSET SET Drive_Axis_A, " + posToSet)
        print(posToSet)

    def moveTo(self):
        distance = str(self.e_goTo.get())
        if (distance == ""):
            return
        speed = str(self.vel.get())
        #acmd(ser, "MOVEABS Drive_Axis_A " + distance + " F " + speed)
        print(distance, speed)

    def moveInc(self):
        distance = str(self.e_inc.get())
        speed = str(self.vel.get())
        #acmd(ser, "MOVEINC Drive_Axis_A " + distance + " F " + speed)
        print(distance, speed)

    def jogForward(self):
        print("forward")
        #Check if button and state is disabled
        #acmd(ser, "ABORT Drive_Axis_A")
        #speed = str(sScan_circ_velocity.get())
        #acmd(ser, "FREERUN Drive_Axis_A " + speed)

    def jogBackward(self):
        print("backward")
        # Check if button and state is disabled
        #acmd(ser, "ABORT Drive_Axis_A")
        #speed = str(-1 * sScan_circ_velocity.get())
        #acmd(ser, "FREERUN Drive_Axis_A " + speed)

    def stopJog(self):
        print("STOP")
        #acmd(ser, "FREERUN Drive_Axis_A 0")

    def updatePosError(self, canvas, error):
        #Max Error for x1 = 401+61 = 462
        x0 = 401
        y0 = 52
        x1 = x0+error
        y1 = 68
        canvas.create_rectangle(x0,y0,x1,y1,fill="red", outline="red")
        messagebox.showinfo("HELP")



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
                       bg="#00aa00", width=10, command=lambda: self.placeHolder())
        self.stop = Button(topFrame, text="STOP", activeforeground="black", activebackground="#00aa00",
                      bg="#00aa00", width=10, state=DISABLED, command=lambda: self.placeHolder())
        self.pause = Button(topFrame, text="PAUSE", activeforeground="black", activebackground="#00aa00",
                       bg="#00aa00", width=10, state=DISABLED, command=lambda: self.placeHolder())
        self.resume = Button(topFrame, text="RESUME", activeforeground="black",
                        activebackground="#00aa00", bg="#00aa00", width=10, state=DISABLED,
                        command=lambda: self.placeHolder())
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

        def placeHolder():
            print("TODO")


class FaultFrame():
    def __init__(self, master):
        frame = Frame(master, borderwidth=2, relief=SUNKEN)
        canvas = Canvas(frame, highlightthickness=0)
        canvas.grid(row=0, column=0)
        frame.pack(fill=X, padx=5, pady=5)
        frame.pack()

        self.label_0 = Label(canvas, text="FAULT STATUS", height=1, font=("Helvetica", 14))
        self.button = Button(canvas, text="FAULT\nRESET", fg="black", bg="#d3d3d3", height=2, width=5, state=DISABLED)
        #self.label_0 = Label(canvas, text="GE HITACHI", height=2, font=("Helvetica", 10))
        self.entry = Entry(canvas, width=59)
        self.label_0.grid(row=0, column=0, columnspan=2, sticky=W)
        self.entry.grid(row=1, column=0, columnspan=2, padx=30)
        self.button.grid(row=1,column=2, pady=5, padx=5)


root = Tk()
root.geometry(str(gui_width)+"x"+str(gui_height))
root.title("Tooling Inspection Motion Controller - Jet Pump Inspection Tool")

#Create the GUI
scanhead = AxisFrame(root, SetupScanheadFrame())
pusher = AxisFrame(root, SetupPusherFrame())
scan = ScanFrame(root, SetupScanFrame())
fault = FaultFrame(root)
root.mainloop()