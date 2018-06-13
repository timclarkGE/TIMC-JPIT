from tkinter import *
from tkinter import messagebox
import serial
import threading
import queue
import time

# Websites about Class and GUI
# https://jeffknupp.com/blog/2014/06/18/improve-your-python-python-classes-and-object-oriented-programming/
# http://python-textbok.readthedocs.io/en/1.0/Object_Oriented_Programming.html
# http://python-textbok.readthedocs.io/en/1.0/Introduction_to_GUI_Programming.html

#Threading
#https://www.troyfawkes.com/learn-python-multithreading-queues-basics/

class SetupMainWindow:
    def __init__(self):
        self.gui_width = 485
        self.gui_height = 600
        self.baud = 115200


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


class MainWindow:
    def __init__(self, master, parameters):
        self.parameters = parameters

        # Serial parameters
        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self.baud = self.parameters.baud

        # Start serial threads
        self.process_serial = SerialThread(self.read_queue, self.write_queue, self.baud)
        self.process_serial.start()
        time.sleep(0.5)
        # Create the main GUI window
        self.master = master
        master.geometry(str(parameters.gui_width) + "x" + str(parameters.gui_height))
        master.title("Tooling Inspection Motion Controller - Jet Pump Inspection Tool")
        #Add frames for each axis and function
        self.scanhead = AxisFrame(self.master, SetupScanheadFrame())
        self.pusher = AxisFrame(self.master, SetupPusherFrame())
        self.scan = ScanFrame(self.master, SetupScanFrame())
        self.fault = FaultFrame(self.master)



    def init_communication(self):    # Create queue for reading and writing serial data to the controller
        print(self.process_serial.is_port_open())
        if(self.process_serial.is_port_open()):
            self.scanhead.update_fbk()
            self.pusher.update_fbk()
        else:
            messagebox.showinfo("No Communication", "OFFLINE MODE")
        print(self.process_serial.is_port_open())




class SerialThread(threading.Thread):
    def __init__(self, read_queue, write_queue, baud):
        threading.Thread.__init__(self)
        self.read_queue = read_queue
        self.write_queue = write_queue
        self._is_running = 1
        self.port_open = 0
        self.baud = baud

    def run(self):

        # Open the serial port
        ports = ['COM%s' % (i + 1) for i in range(100)]
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        if len(result) == 1:
            self.s = serial.Serial(result[0], self.baud)
            self.port_open = 1

        else:
            # TODO:
            print("ERROR")
        while self._is_running:
            # Check if there are commands to be written
            if self.write_queue.qsize():
                command = self.write_queue.get().encode('ascii') + b' \n'
                self.s.write(command)
                _is_complete = 0
                data = ""
                while _is_complete == 0:
                    if self.s.inWaiting():
                        # Read the byte that is ready
                        c = self.s.read()

                        # #Decode the byte
                        c = c.decode('ascii')

                        # Append the ascii character to data
                        data += c

                        # Check if newline character which signifies End of String (EOS)
                        if (c == '\n'):
                            _is_complete = 1
                            self.read_queue.put(data)

    def stop(self):
        self._is_running = 0
        try:
            self.s.close()
        except:
            print("No Serial Port to Close")
    def is_port_open(self):
        return self.port_open

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


    def toggle_axis(self):
        if(self.state == 0):
            self.enable_axis()
        elif(self.state == 1):
            self.disable_axis()

    def enable_axis(self):
        acmd("ENABLE " + self.axisName)
        if ((0b1 & int(acmd("AXISSTATUS(" + self.axisName + ")"))) == 1):
            self.state=1
            self.activate_all_btns()

    def disable_axis(self):
        acmd("DISABLE " + self.axisName)
        if ((0b1 & int(acmd("AXISSTATUS(" + self.axisName + ")"))) == 0):
            print(int(acmd("AXISSTATUS(" + self.axisName + ")")))
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
        if ((0b1 & int(acmd("AXISSTATUS(" + self.axisName + ")"))) == 1):
            self.state = 1
            self.enableButton.config(text="ON", bg="#00aa00", state="normal")
            self.jog_fwd.config(state="active")
            self.jog_rev.config(state="active")
            self.set_pos.config(state="active")
            self.go_to.config(state="active")
            self.inc.config(state="active")
            self.vel.config(state="active")

    def set_position(self):
        posToSet = str(self.e_setPos.get())
        acmd("POSOFFSET SET " + self.axisName + ", " + posToSet)

    def move_to(self):
        distance = str(self.e_goTo.get())
        if (distance == ""):
            return
        speed = str(self.vel.get())
        acmd("MOVEABS " + self.axisName + " " + distance + " F " + speed)

    def move_inc(self):
        acmd("ABORT " + self.axisName)
        distance = str(self.e_inc.get())
        speed = str(self.vel.get())
        acmd("MOVEINC " + self.axisName + " " + distance + " F " + speed)

    def jog_forward(self):
        if(self.state == 1 and self.enableButton['state'] != 'disabled'):
            acmd("ABORT " + self.axisName)
            speed = str(self.vel.get())
            acmd("FREERUN " + self.axisName + " " + speed)

    def jog_backward(self):
        if (self.state == 1 and self.enableButton['state'] != 'disabled'):
            acmd("ABORT " + self.axisName)
            speed = str(-1*self.vel.get())
            acmd("FREERUN " + self.axisName + " " + speed)

    def stop_jog(self):
        acmd("FREERUN " + self.axisName + " 0")

    #Update Feedback
    def update_fbk(self):
        pos = acmd("PFBKPROG(" + self.axisName + ")")
        pos = round(float(pos), 2)
        pos = format(pos, '.2f')
        self.mtr_position.set(pos)

        cur = acmd("IFBK(" + self.axisName + ")")
        cur = float(cur) * 1000
        cur = round(cur)
        self.mtr_current.set(cur)

        test = acmd("PERR(" + self.axisName + ")")
        test = test.replace("\n", "")
        error = float(test)
        #self.updatePosError(self.canvas, error)

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
                      bg="#00aa00", width=10, state=DISABLED, command=lambda: stop_scan(self))
        self.pause = Button(topFrame, text="PAUSE", activeforeground="black", activebackground="#00aa00",
                       bg="#00aa00", width=10, state=DISABLED, command=lambda: pause_scan(self))
        self.resume = Button(topFrame, text="RESUME", activeforeground="black",
                        activebackground="#00aa00", bg="#00aa00", width=10, state=DISABLED,
                        command=lambda: resume_scan(self))
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
        rowSpaceTop=18
        self.label_0.grid(row=0, column=0, columnspan = 4, sticky=W)
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
            TIMC.scanhead.inactivate_all_btns(TRUE)
            TIMC.pusher.inactivate_all_btns(TRUE)
            self.start.config(state = "disabled")
            self.stop.config(state = "active")
            self.pause.config(state = "active")

            scan_points = [[0,0],
                           [10,0],
                           [10,1],
                           [0,1]]
            self.process_scan = ScanThread(scan_points)
            self.process_scan.start()

        def stop_scan(self):
            self.process_scan.stop()

        def pause_scan(self):
            self.process_scan.pause()

        def resume_scan(self):
            self.process_scan.resume()

class ScanThread(threading.Thread):
    def __init__(self, scan_points):
        threading.Thread.__init__(self)
        self._is_running = 1
        self._is_paused = 0
        self.scan_points = scan_points
        self.index = 0
        self.error = 0.01

    def run(self):
        while(self._is_running):
            # Check if the axis have been disabled due to a fault
            if(TIMC.scanhead.state and TIMC.pusher.state and (self._is_paused != 1)):
                # Go to point
                acmd("MOVEABS SCANHEAD " + str(self.scan_points[self.index][0]) + " F 10")
                acmd("MOVEABS PUSHER " + str(self.scan_points[self.index][1]) + " F 0.5")
                # Check if each axis is "in position"
                if ((0b100 & int(acmd("AXISSTATUS(SCANHEAD)")) == 4) and (0b100 & int(acmd("AXISSTATUS(PUSHER)")) == 4)):
                    if(self.index < (len(self.scan_points)-1)):
                        self.index += 1
                    else:
                        messagebox.showinfo("", "Scan is Complete")
                        self.stop()

    def stop(self):
        self._is_running = 0
        acmd("ABORT SCANHEAD")
        acmd("ABORT PUSHER")
        TIMC.scanhead.activate_all_btns()
        TIMC.pusher.activate_all_btns()
        TIMC.scan.start.config(state="active")
        TIMC.scan.stop.config(state="disabled")
        TIMC.scan.pause.config(state="disabled")
        TIMC.scan.resume.config(state="disabled")

    def pause(self):
        self._is_paused = 1
        acmd("ABORT SCANHEAD")
        acmd("ABORT PUSHER")
        TIMC.scan.pause.config(state="disabled")
        TIMC.scan.resume.config(state="active")

    def resume(self):
        self._is_paused = 0
        TIMC.scan.pause.config(state="active")
        TIMC.scan.resume.config(state="disabled")

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


def on_closing():
    TIMC.process_serial.stop()
    root.destroy()

# ASCII cmd
def acmd(text):
    TIMC.write_queue.put(text)
    data = TIMC.read_queue.get()
    if "!" in data:
        TIMC.fault.status.set("Bad Execution")
        return 0
    elif "#" in data:
        TIMC.fault.status.set("Ack but cannot execute")
        return 0
    elif "$" in data:
        TIMC.fault.status.set("Command timed out")
        return 0
    elif data == "":
        TIMC.fault.status.set("No data, check serial connection")
        return 0
    else:
        data = data.replace("%", "")
        #TIMC.fault.status.set("Success :"+data)
        return data






######################################
#             Main Code              #
######################################

# Open serial connection and test for communication with the Ensemble
#ser = init_com()

root = Tk()
TIMC = MainWindow(root, SetupMainWindow())
TIMC.init_communication()

#root.after(50, TIMC.scanhead.update_fbk())
#root.after(100, TIMC.pusher.update_fbk())


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

