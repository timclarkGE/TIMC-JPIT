##############################################
# Tooling Inspection Motion Controller GUI   #
# Tool: Jet Pump Inspection Tool             #
# PLM:  TBD                                  #
##############################################

# Author:   Timothy Clark
# Email:    timoty.clark@ge.com
# Date:     06/21/2018
# Company:  GE Hitachi
# Description
#   - Graphical User Interface using Tkinter package
#   - Requires python 3.6
#   - Lienar amplifiers to reduce EMI: Aerotech Ensemble ML
#   - Serial communication with Aerobasic ASCII commands
#
# ###########################################################

# Resources used to write this code:
#   Websites about Class and GUI
#   https://jeffknupp.com/blog/2014/06/18/improve-your-python-python-classes-and-object-oriented-programming/
#   http://python-textbok.readthedocs.io/en/1.0/Object_Oriented_Programming.html
#   http://python-textbok.readthedocs.io/en/1.0/Introduction_to_GUI_Programming.html

# Threading
#   https://www.troyfawkes.com/learn-python-multithreading-queues-basics/
#   https://codewithoutrules.com/2017/08/16/concurrency-python/
#   https://www.slideshare.net/dabeaz/an-introduction-to-python-concurrency

# Serial Threads and Queues
#   https://stackoverflow.com/questions/16938647/python-code-for-serial-data-to-print-on-window


from tkinter import *
from tkinter import messagebox
import serial
import threading
import queue
import time

FBK_THREAD_WAIT = 0.0001
SCAN_THREAD_WAIT = 0.25

class SetupMainWindow:
    def __init__(self):
        self.gui_width = 485
        self.gui_height = 555
        self.baud = 115200


class SetupScanheadFrame:
    def __init__(self):
        self.axisName = "SCANHEAD"
        self.axisUnits = "deg"
        self.jogText1 = "CCW"
        self.jogText2 = "CW"
        self.speedMin = 0.5
        self.speedMax = 20
        self.speedRes = 0.5
        self.maxError = 0.22
        self.queue_name = "CTRL"


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
        self.queue_name = "CTRL"


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
        self.queue_name = "SCAN"


class MainWindow:
    def __init__(self, master, parameters):
        self.parameters = parameters

        # Serial parameters
        self.baud = self.parameters.baud
        self.online = 0

        # Queues for communication between threads
        self.qFBK_read = queue.Queue()
        self.qFBK_write = queue.Queue()
        self.qStatus_read = queue.Queue()
        self.qStatus_write = queue.Queue()
        self.qScan_read = queue.Queue()
        self.qScan_write = queue.Queue()
        self.qControl_read = queue.Queue()
        self.qControl_write = queue.Queue()
        self.qLog = queue.Queue()

        # Start serial threads
        self.process_serial = SerialThread(self.baud, self.qControl_read, self.qControl_write, self.qScan_read,
                                           self.qScan_write, self.qStatus_read, self.qStatus_write, self.qFBK_read,
                                           self.qFBK_write, self.qLog)
        self.process_serial.start()
        # Wait for serial thread to establish communication
        time.sleep(0.5)

        # Create the main GUI window
        self.master = master
        master.geometry(str(parameters.gui_width) + "x" + str(parameters.gui_height))
        master.title("Tooling Inspection Motion Controller - Jet Pump Inspection Tool")

        # Create frames for each axis and function
        self.scanhead = AxisFrame(self.master, SetupScanheadFrame())
        self.pusher = AxisFrame(self.master, SetupPusherFrame())
        self.scan = ScanFrame(self.master, SetupScanFrame())
        self.fault = FaultFrame(self.master)

        # Start communication with TIMC
        self.init_communication()

    # Main method for sending commands to TIMC
    def acmd(self, queue_name, text):

        # There are four read/write queues
        if (queue_name == "CTRL"):
            write_queue = self.qControl_write
            read_queue = self.qControl_read
        elif( queue_name == "SCAN"):
            write_queue = self.qScan_write
            read_queue = self.qScan_read
        elif(queue_name == "STATUS"):
            write_queue = self.qStatus_write
            read_queue = self.qStatus_read
        elif(queue_name == "FBK"):
            write_queue = self.qFBK_write
            read_queue = self.qFBK_read

        write_queue.put(text)
        data = read_queue.get()

        if "!" in data:
            print("(!) Bad Execution")
            return 0
        elif "#" in data:
            print("(#) ACK but cannot execute")
            return 0
        elif "$" in data:
            print("($) CMD timeout")
            return 0
        elif data == "":
            print("No data returned, check serial connection")
            return 0
        else:
            data = data.replace("%", "")
            return data

    def init_communication(self):
        if (self.process_serial.port_open == 0):
            self.fault.update_status("OFFLINE MODE")
            self.scanhead.enableButton.config(state="disabled")
            self.pusher.enableButton.config(state="disabled")
            self.scan.start.config(state="disabled")
            self.process_serial.stop()
            self.online = 0
        elif (self.process_serial.port_open == 1):
            self.online = 1


class SerialThread(threading.Thread):

    def __init__(self, baud, qControl_read, qControl_write, qScan_read, qScan_write, qStatus_read, qStatus_write,
                 qFBK_read, qFBK_write, qLog):
        threading.Thread.__init__(self)
        self.qControl_read = qControl_read
        self.qControl_write = qControl_write
        self.qScan_read = qScan_read
        self.qScan_write = qScan_write
        self.qStatus_read = qStatus_read
        self.qStatus_write = qStatus_write
        self.qFBK_read = qFBK_read
        self.qFBK_write = qFBK_write
        self.qLog = qLog

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
            self.s = serial.Serial(result[0], self.baud, timeout = 0.05)

            # Send a command to check if communication has been established
            self.s.write("ACKNOWLEDGEALL".encode('ascii') + b' \n')
            data = self.s.readline().decode('ascii')
            if ('%' in data):
                self.port_open = 1
                self.s.write("WAIT MODE NOWAIT".encode('ascii') + b' \n')
                # Throw away second response
                data = self.s.readline().decode('ascii')
        elif (len(result) > 1):
            self.port_open = 0
            self._is_running = 0
        else:
            self._is_running = 0

        # Thread main loop
        while self._is_running:
            # Check data in queue with queue priority being: qControl, qScan, qStatus, qFBK_write, qFBK_read, qLog
            time.sleep(FBK_THREAD_WAIT)
            if self.qControl_write.qsize():
                command = self.qControl_write.get().encode('ascii') + b' \n'
                try:
                    self.s.write(command)
                except:
                    on_closing()
                data = self.s.readline().decode('ascii')
                self.qControl_read.put(data)
                self.qLog.put("CTRL: " + str(command) + str(data))
            elif self.qScan_write.qsize():
                command = self.qScan_write.get().encode('ascii') + b' \n'
                self.s.write(command)
                data = self.s.readline().decode('ascii')
                self.qScan_read.put(data)
                self.qLog.put("SCAN: " + str(command) + str(data))
            elif self.qStatus_write.qsize():
                command = self.qStatus_write.get().encode('ascii') + b' \n'
                self.s.write(command)
                data = self.s.readline().decode('ascii')
                self.qStatus_read.put(data)
                self.qLog.put("STAT: " + str(command) + str(data))
            elif self.qFBK_write.qsize():
                command = self.qFBK_write.get().encode('ascii') + b' \n'
                self.s.write(command)
                data = self.s.readline().decode('ascii')
                self.qFBK_read.put(data)
                self.qLog.put("FBK : " + str(command) + str(data))

    def stop(self):
        self._is_running = 0
        try:
            self.s.close()
        except:
            print("No Serial Port to Close")


# Will create an axis frame with all buttons, entry boxes, and scales
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
        self.queue = parameters.queue_name

        self.enableButton = Button(self.canvas, text="OFF", fg="black", bg="#d3d3d3", height=2, width=6, padx=3, pady=3,
                                   command=lambda: self.toggle_axis())
        self.jog_neg = Button(self.canvas, text=parameters.jogText1, activeforeground="black",
                              activebackground="#00aa00",
                              bg="#00aa00", width=10, state=DISABLED)
        self.jog_pos = Button(self.canvas, text=parameters.jogText2, activeforeground="black",
                              activebackground="#00aa00",
                              bg="#00aa00", width=10, state=DISABLED)
        self.set_pos = Button(self.canvas, text=" Set ", activeforeground="black", activebackground="#00aa00",
                              bg="#00aa00",
                              state=DISABLED, command=lambda: self.set_position())
        self.go_to = Button(self.canvas, text="GoTo", activeforeground="black", activebackground="#00aa00",
                            bg="#00aa00",
                            state=DISABLED, command=lambda: self.move_to())
        self.inc = Button(self.canvas, text="Index", activeforeground="black", activebackground="#00aa00", bg="#00aa00",
                          state=DISABLED, command=lambda: self.move_inc())
        self.mtrPositionBox = Entry(self.canvas, state="readonly", width=10, textvariable=self.mtr_position)
        self.mtrCurrentBox = Entry(self.canvas, state="readonly", width=10, textvariable=self.mtr_current)
        # self.placeHolder = Entry(canvas, state="readonly", width=10, textvariable=self.mtrError)
        self.e_setPos = Entry(self.canvas, width=10)
        self.e_goTo = Entry(self.canvas, width=10)
        self.e_inc = Entry(self.canvas, width=10)
        self.vel = Scale(self.canvas, from_=parameters.speedMin, to=parameters.speedMax, orient=HORIZONTAL, length=150,
                         label="            Velocity " + parameters.axisUnits + "/sec", resolution=parameters.speedRes)
        self.vel.set((parameters.speedMax - parameters.speedMin) * 0.25)
        self.vel.config(state="disabled")
        self.label_0 = Label(self.canvas, text=parameters.axisName, height=1, font=("Helvetica", 14))
        self.label_1 = Label(self.canvas, text="Pos. (" + parameters.axisUnits + ")")
        self.label_2 = Label(self.canvas, text="Cur. (mA)")
        self.label_3 = Label(self.canvas, text="Pos. Error")

        # Draw box for position error that looks like disabled entry box.
        self.canvas.create_line(400, 29, 463, 29, fill="#A0A0A0")
        self.canvas.create_line(400, 29, 400, 47, fill="#A0A0A0")
        self.canvas.create_line(400, 47, 464, 47, fill="white")
        self.canvas.create_line(463, 51, 463, 48, fill="white")

        # GRID
        self.label_0.grid(row=0, column=0, columnspan=5, sticky=W)
        self.enableButton.grid(row=1, column=0, rowspan=3, padx=15)
        self.jog_neg.grid(row=1, column=1, rowspan=2, padx=3)
        self.jog_pos.grid(row=1, column=2, rowspan=2, padx=3)
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
        self.vel.grid(row=3, column=1, columnspan=2, rowspan=2)

        # Reverse Motion direction is selected in the parameter file for both axis thus functions are switched below
        self.jog_pos.bind('<ButtonPress-1>', lambda event: self.jog_positive())
        self.jog_pos.bind('<ButtonRelease-1>', lambda event: self.stop_jog())
        self.jog_neg.bind('<ButtonPress-1>', lambda event: self.jog_negative())
        self.jog_neg.bind('<ButtonRelease-1>', lambda event: self.stop_jog())

    def toggle_axis(self):
        if (self.state == 0):
            self.enable_axis()
        elif (self.state == 1):
            self.disable_axis()

    def enable_axis(self):
        TIMC.acmd(self.queue, "ENABLE " + self.axisName)
        if ((0b1 & int(TIMC.acmd(self.queue, "AXISSTATUS(" + self.axisName + ")"))) == 1):
            self.state = 1
            self.activate_all_btns()
            if (TIMC.scan.start['state'] == "disabled"):
                self.inactivate_all_btns()

    def disable_axis(self):
        TIMC.acmd(self.queue, "DISABLE " + self.axisName)
        if ((0b1 & int(TIMC.acmd(self.queue, "AXISSTATUS(" + self.axisName + ")"))) == 0):
            self.enableButton.config(text="OFF", bg="#d3d3d3")
            self.state = 0
            self.inactivate_all_btns()

    def inactivate_all_btns(self):

        self.jog_pos.config(state="disabled")
        self.jog_neg.config(state="disabled")
        self.set_pos.config(state="disabled")
        self.go_to.config(state="disabled")
        self.inc.config(state="disabled")
        self.vel.config(state="disabled")

    def activate_all_btns(self):
        if ((0b1 & int(TIMC.acmd(self.queue, "AXISSTATUS(" + self.axisName + ")"))) == 1):
            self.state = 1
            self.enableButton.config(text="ON", bg="#00aa00", state="normal")
            self.jog_pos.config(state="active")
            self.jog_neg.config(state="active")
            self.set_pos.config(state="active")
            self.go_to.config(state="active")
            self.inc.config(state="active")
            self.vel.config(state="active")

    def set_position(self):
        posToSet = str(self.e_setPos.get())
        TIMC.acmd(self.queue, "POSOFFSET SET " + self.axisName + ", " + posToSet)

    def move_to(self):
        distance = str(self.e_goTo.get())
        if (distance == ""):
            return
        speed = str(self.vel.get())
        TIMC.acmd(self.queue, "MOVEABS " + self.axisName + " " + distance + " F " + speed)

    def move_inc(self):
        TIMC.acmd(self.queue, "ABORT " + self.axisName)
        distance = str(self.e_inc.get())
        speed = str(self.vel.get())
        TIMC.acmd(self.queue, "MOVEINC " + self.axisName + " " + distance + " F " + speed)

    def jog_positive(self):
        if (self.state == 1 and self.enableButton['state'] != 'disabled'):
            TIMC.acmd(self.queue, "ABORT " + self.axisName)
            speed = str(self.vel.get())
            TIMC.acmd(self.queue, "FREERUN " + self.axisName + " " + speed)

    def jog_negative(self):
        if (self.state == 1 and self.enableButton['state'] != 'disabled'):
            TIMC.acmd(self.queue, "ABORT " + self.axisName)
            speed = str(-1 * self.vel.get())
            TIMC.acmd(self.queue, "FREERUN " + self.axisName + " " + speed)

    def stop_jog(self):
        if (TIMC.online):
            TIMC.acmd(self.queue, "FREERUN " + self.axisName + " 0")

    def updatePosError(self, error):
        # Max Error for x1 = 401+61 = 462
        calc_error = int(abs((error / self.max_pos_error)) * 61)
        if (calc_error > 61):
            calc_error = 61
        # color = root.cget("bg")
        # print(color)
        x0 = 401
        y0 = 30
        x1 = x0 + calc_error
        y1 = 46
        # Legacy error, leaving this until I"m sure the bug is gone
        try:
            self.canvas.create_rectangle(x0, y0, x0 + 61, y1, fill="SystemButtonFace", outline="SystemButtonFace")
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="red", outline="red")
        except:
            print("Error")


# Will create a scan frame with all buttons, entry boxes, and scales
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

        self.scanType = IntVar()
        self.scanTimeText = StringVar()
        self.scanTimeText.set("00:00:00")
        self.queue = parameters.queue_name

        # LEFT FRAME WIDGETS
        self.start = Button(topFrame, text="START", activeforeground="black", activebackground="#00aa00",
                            bg="#00aa00", width=10, command=lambda: self.start_scan())
        self.stop = Button(topFrame, text="STOP", activeforeground="black", activebackground="#00aa00",
                           bg="#00aa00", width=10, state=DISABLED, command=lambda: self.stop_scan())
        self.pause = Button(topFrame, text="PAUSE", activeforeground="black", activebackground="#00aa00",
                            bg="#00aa00", width=10, state=DISABLED, command=lambda: self.pause_scan())
        self.resume = Button(topFrame, text="RESUME", activeforeground="black",
                             activebackground="#00aa00", bg="#00aa00", width=10, state=DISABLED,
                             command=lambda: self.resume_scan())
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
        self.scanVelocity.set((parameters.scanSpeedMax - parameters.scanSpeedMin) * 0.25)
        self.indexVelocity.set((parameters.indexSpeedMax - parameters.indexSpeedMin) * 0.25)
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
        self.radio_0 = Radiobutton(middleFrame, text="Bi-directional", variable=self.scanType, value=0)
        self.radio_1 = Radiobutton(middleFrame, text="Uni-directional", variable=self.scanType, value=1)
        self.time = Entry(middleFrame, state="readonly", width=10, textvariable=self.scanTimeText)

        # GRID TOP
        rowSpaceTop = 18
        self.label_0.grid(row=0, column=0, columnspan=4, sticky=W)
        self.start.grid(row=1, column=0, pady=5, padx=rowSpaceTop)
        self.stop.grid(row=1, column=1, pady=5, padx=rowSpaceTop)
        self.pause.grid(row=1, column=2, pady=5, padx=rowSpaceTop)
        self.resume.grid(row=1, column=3, pady=5, padx=rowSpaceTop)

        # GRID LEFT
        self.scanVelocity.grid(row=0, column=0, padx=5)
        self.indexVelocity.grid(row=1, column=0, padx=5, pady=5)

        # GRID MIDDLE
        middleFrame.grid_rowconfigure(2, minsize=20)
        self.radio_0.grid(row=0, column=0, sticky=W, padx=20)
        self.radio_1.grid(row=1, column=0, sticky=W, padx=20)
        self.label_6.grid(row=3, column=0)
        self.time.grid(row=4, column=0)

        # GRID RIGHT
        rowSpaceRight = 1
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
        # Get input from user and store to local variable
        self.scan_start = float(self.e_scanStart.get())
        self.scan_stop = float(self.e_scanStop.get())
        self.index_start = float(self.e_indexStart.get())
        self.index_stop = float(self.e_indexStop.get())
        self.index_size = float(self.e_indexSize.get())
        self.scan_speed = float(self.scanVelocity.get())
        self.index_speed = float(self.indexVelocity.get())

        # Check user inputs
        if (self.scan_stop == self.scan_start):
            messagebox.showinfo("Bad Scan Input", "Scan Stop equals Scan Start")
            return
        if (self.index_stop == self.index_start):
            messagebox.showinfo("Bad Scan Input", "Index Stop equals Index Start")
            return
        if (self.index_stop > self.index_start):
            messagebox.showinfo("Bad Scan Input", "Index Start must be greater than Index Stop")
            return
        if ((self.index_stop - self.index_start) % self.index_size > 0.000001):
            messagebox.showinfo("Bad Scan Input", "Index Size must be a multiple of Index Start - Index Stop")
            return
        # Calculate the scan points with the given user input, self.scan_points will be created and initialized
        self.create_scan_points()
        self.deactivate_scan_widgets()
        TIMC.scanhead.inactivate_all_btns()
        TIMC.pusher.inactivate_all_btns()

        # Prepare the GUI for scanning by disabling/activating appropriate widgets
        # Modify widgets if inputs are correct

        # Create a scan thread
        self.process_scan = ScanThread(self.scan_points,
                                       self.scan_speed,
                                       self.index_speed,
                                       self.scan_start,
                                       self.scan_stop,
                                       self.index_start,
                                       self.index_stop,
                                       self.index_size,
                                       self.queue)
        self.process_scan.start()

    def stop_scan(self):
        self.activate_scan_widgets()
        TIMC.scanhead.activate_all_btns()
        TIMC.pusher.activate_all_btns()
        self.process_scan.stop()

    def pause_scan(self):
        self.process_scan.pause()

    def resume_scan(self):
        self.process_scan.resume()

    def create_scan_points(self):
        # Scan type variable: 0 = bidirectional, 1 unidirectional

        # Variables for generating scan points
        i_var = self.index_start + self.index_size    # Initialize index variable
        s_var = self.scan_start                  # Initialize scan variable
        s_toggle = [self.scan_start, self.scan_stop]  # Toggle values for the scan axis scan points
        x = 0                               # Toggle control variable

        # Calculate the number of points in the scan
        # Uni-directional
        if (self.scanType.get() == 1):
            size = int(abs(self.index_stop - self.index_start) / self.index_size * 3 + 3)

        # Bi-directional
        elif (self.scanType.get() == 0):
            size = int(abs(self.index_stop - self.index_start) / self.index_size * 2 + 2)

        # 2D array for scan points [scan][index]
        w, h = 2, size
        self.scan_points = [[0 for x in range(w)] for y in range(h)]

        # Calculate scan points and store to 2D array scan_points
        # Uni-directional
        if (self.scanType.get() == 1):
            for i in range(0, size):
                # Set s_var
                if (i % 3 == 1):
                    s_var = self.scan_stop
                # Increment i_var
                elif (i % 3 == 0):
                    i_var -= self.index_size
                else:
                    s_var = self.scan_start
                self.scan_points[i][0] = s_var
                self.scan_points[i][1] = i_var
                #print(s_var,i_var)
        # Bi-directional
        elif (self.scanType.get() == 0):
            for i in range(0, size):
                # Toggle s_var
                if (i % 2):
                    x = 1 if x == 0 else 0
                    s_var = s_toggle[x]
                # Increment i_var
                else:
                    i_var -= self.index_size
                self.scan_points[i][0] = s_var
                self.scan_points[i][1] = i_var
                #print(s_var, i_var)

    # At the conclusion of a scan or stopped scan, activate all widgets for scan
    def activate_scan_widgets(self):
        # Configure widgets in scan frame
        self.start.config(state="active")
        self.stop.config(state="disabled")
        self.pause.config(state="disabled")
        self.resume.config(state="disabled")
        self.e_scanStart.config(state="normal")
        self.e_scanStop.config(state="normal")
        self.e_indexStart.config(state="normal")
        self.e_indexStop.config(state="normal")
        self.e_indexSize.config(state="normal")
        self.radio_0.config(state="normal")
        self.radio_1.config(state="normal")
        self.scanVelocity.config(state="normal")
        self.indexVelocity.config(state="normal")
        self.scanTimeText.set("00:00:00")
        time.sleep(0.25)
        TIMC.acmd(self.queue, "ABORT SCANHEAD")
        TIMC.acmd(self.queue, "ABORT PUSHER")

    # Prepares scan window widgets for scan by disabling all inputs
    def deactivate_scan_widgets(self):
        self.start.config(state="disabled")
        self.stop.config(state="active")
        self.pause.config(state="active")
        self.e_scanStart.config(state="disabled")
        self.e_scanStop.config(state="disabled")
        self.e_indexStart.config(state="disabled")
        self.e_indexStop.config(state="disabled")
        self.e_indexSize.config(state="disabled")
        self.radio_0.config(state="disabled")
        self.radio_1.config(state="disabled")
        self.scanVelocity.config(state="disabled")
        self.indexVelocity.config(state="disabled")

class ScanThread(threading.Thread):
    def __init__(self, scan_points, scan_speed, index_speed, scan_start, scan_stop, index_start, index_stop,
                 index_size, queue):
        threading.Thread.__init__(self)
        self._is_running = 1
        self._is_paused = 0
        self.scan_points = scan_points
        self.scan_speed = scan_speed
        self.index_speed = index_speed
        self.scan_start = scan_start
        self.scan_stop = scan_stop
        self.index_start = index_start
        self.index_stop = index_stop
        self.index_size = index_size
        self.queue = queue
        self.i = 0

        self.scanhead_moved = 0
        self.number_scanhead_moves = 0
        self.pusher_moved = 0
        self.number_pusher_moves = 0

        self.movement_start_time = 0
        self.movement_elapsed_time = 0
        self.avg_scanhead_move_time = abs(scan_start - scan_stop) / scan_speed
        self.avg_pusher_move_time = abs(index_size / index_speed)
        self.last_update_time = time.time()



    def run(self):
        while (self._is_running):
            time.sleep(SCAN_THREAD_WAIT)

            if ((time.time() - self.last_update_time) > 1 and self.i != 0 and self.i < len(self.scan_points)):
                self.calc_rem_scan_time()

            scan_status = int(TIMC.acmd(self.queue, "AXISSTATUS(SCANHEAD)"))
            scan_enabled = 0b1 & scan_status
            scan_in_pos = 0b100 & scan_status

            # Limit the number of calls to the controller by checking scanhead axis first
            if (scan_enabled and scan_in_pos and self._is_paused != 1):
                # If scanhead is in position and not faulted, check the same for the pusher
                index_status = int(TIMC.acmd(self.queue, "AXISSTATUS(PUSHER)"))
                index_enabled = 0b1 & index_status
                index_in_pos = 0b100 & index_status
                if (index_enabled and index_in_pos and self._is_paused != 1):
                    if self.i < (len(self.scan_points)):
                        # Command scanhead to move to next scan point
                        TIMC.acmd(self.queue,
                                  "MOVEABS SCANHEAD " + str(self.scan_points[self.i][0]) + " F " + str(
                                      self.scan_speed))
                        # Check if scanhead is in position despite being told to move to the next scan point.
                        scan_status = int(TIMC.acmd(self.queue, "AXISSTATUS(SCANHEAD)"))
                        scan_enabled = 0b1 & scan_status
                        scan_in_pos = 0b100 & scan_status
                        if (scan_enabled and scan_in_pos and self._is_paused != 1):
                            # Command pusher to move to next scan point
                            TIMC.acmd(self.queue,
                                      "MOVEABS PUSHER " + str(self.scan_points[self.i][1]) + " F " + str(
                                          self.index_speed))
                            # Check if pusher is in position despite being told to move to the next scan point.
                            index_status = int(TIMC.acmd(self.queue, "AXISSTATUS(PUSHER)"))
                            index_enabled = 0b1 & index_status
                            index_in_pos = 0b100 & index_status
                            if (index_enabled and index_in_pos and self._is_paused != 1):
                                # Movement complete, calculate move time for each
                                if (self.i == 0):
                                    self.movement_start_time = time.time()
                                else:
                                    self.movement_elapsed_time = time.time() - self.movement_start_time + self.movement_elapsed_time
                                    self.scanhead_moved = self.scan_points[self.i][0] - self.scan_points[self.i - 1][0]
                                    self.pusher_moved = self.scan_points[self.i][1] - self.scan_points[self.i - 1][1]
                                    if (self.scanhead_moved):
                                        self.avg_scanhead_move_time = (
                                                self.avg_scanhead_move_time * self.number_scanhead_moves + self.movement_elapsed_time)
                                        self.number_scanhead_moves += 1
                                        self.avg_scanhead_move_time /= self.number_scanhead_moves
                                    elif (self.pusher_moved):
                                        self.avg_pusher_move_time = (
                                                self.avg_pusher_move_time * self.number_pusher_moves + self.movement_elapsed_time)
                                        self.number_pusher_moves += 1
                                        self.avg_pusher_move_time /= self.number_pusher_moves
                                    # Reset time variables
                                    self.movement_start_time = time.time()
                                    self.movement_elapsed_time = 0

                                # Ready for next scan point
                                self.i += 1
                    else:
                        messagebox.showinfo("", "Scan is Complete")
                        self.stop()
                # One or both axes are not enabled due to a fault
                elif (index_enabled == 0):
                    self.pause()
            elif (scan_enabled == 0):
                self.pause()

    def stop(self):
        TIMC.scan.activate_scan_widgets()
        TIMC.scanhead.activate_all_btns()
        TIMC.pusher.activate_all_btns()
        self._is_running = 0

    def pause(self):
        self._is_paused = 1
        TIMC.acmd(self.queue, "ABORT SCANHEAD")
        TIMC.acmd(self.queue, "ABORT PUSHER")
        TIMC.scan.pause.config(state="disabled")
        TIMC.scan.resume.config(state="active")
        self.movement_elapsed_time = time.time() - self.movement_start_time

    def resume(self):
        self._is_paused = 0
        TIMC.scan.pause.config(state="active")
        TIMC.scan.resume.config(state="disabled")
        self.movement_start_time = time.time()

    def calc_rem_scan_time(self):

        scanhead_pos = float(TIMC.acmd(self.queue, "PFBKPROG(SCANHEAD)"))
        pusher_pos = float(TIMC.acmd(self.queue, "PFBKPROG(PUSHER)"))
        scan_time = 0

        # Determine which axis is moving
        self.scanhead_moving = abs(self.scan_points[self.i][0] - self.scan_points[self.i - 1][0])
        self.pusher_moving = abs(self.scan_points[self.i][1] - self.scan_points[self.i - 1][1])
        # Calculate time to complete move to next scan point
        if (self.scanhead_moving and self.pusher_moving == 0 and self.i != (len(self.scan_points) - 1)):
            scan_time = abs(scanhead_pos - self.scan_points[self.i][0]) / self.scan_speed
        elif (self.pusher_moving and self.scanhead_moving == 0):
            scan_time = abs(pusher_pos - self.scan_points[self.i][1]) / self.index_speed
        # If not on the last move, then calculate remaining scan time
        for i in range(self.i+1, len(self.scan_points)):
            scanhead_move = abs(self.scan_points[i][0] - self.scan_points[i - 1][0])
            pusher_move = abs(self.scan_points[i][1] - self.scan_points[i - 1][1])
            if (scanhead_move and pusher_move == 0):
                scan_time += self.avg_scanhead_move_time
            elif (pusher_move and scanhead_move == 0):
                scan_time += self.avg_pusher_move_time

        hours = int(scan_time / 3600)
        mins = int((scan_time - (hours * 3600)) / 60)
        seconds = int(scan_time - hours * 3600 - mins * 60)
        TIMC.scan.scanTimeText.set(str(hours).zfill(2) + ":" + str(mins).zfill(2) + ":" + str(seconds).zfill(2))


class FaultFrame():
    def __init__(self, master):
        self.frame = Frame(master, borderwidth=2, relief=SUNKEN)
        self.canvas = Canvas(self.frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        self.frame.pack(fill=X, padx=5, pady=5)
        self.frame.pack()
        self.status_text = StringVar()

        self.label_0 = Label(self.canvas, text="FAULT STATUS", height=1, font=("Helvetica", 14))
        self.button = Button(self.canvas, text="FAULT\nRESET", fg="black", bg="#d3d3d3", height=2, width=5,
                             command=lambda: self.fault_ack())
        # self.label_0 = Label(canvas, text="GE HITACHI", height=2, font=("Helvetica", 10))
        self.entry = Entry(self.canvas, width=59, textvariable=self.status_text)
        self.label_0.grid(row=0, column=0, columnspan=2, sticky=W)
        self.entry.grid(row=1, column=0, columnspan=2, padx=30)
        self.button.grid(row=1, column=2, pady=5, padx=5)

    def update_status(self, text):
        self.canvas.config(bg="red")
        self.label_0.config(bg="red")
        self.status_text.set(text)

    def fault_ack(self):
        if (TIMC.online):
            TIMC.acmd("CTRL", "ACKNOWLEDGEALL")
            self.canvas.config(bg="SystemButtonFace")
            self.label_0.config(bg="SystemButtonFace")
            self.status_text.set("")


class UpdateStatus(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self._is_running = 1
        self.fault_array = ["PositionError Fault",  # 0
                            "OverCurrent Fault",  # 1
                            "CW/Positive End-of-Travel Limit Fault",  # 2
                            "CCW/Negative End-of-Travel Limit Fault",  # 3
                            "CW/High Software Limit Fault",  # 4
                            "CCW/Low Software Limit Fault",  # 5
                            "Amplifier Fault",  # 6
                            "Position Feedback Fault",  # 7
                            "Velocity Feedback Fault",  # 8
                            "Hall Sensor Fault",  # 9
                            "Maximum Velocity Command Fault",  # 10
                            "Emergency Stop Fault",  # 11
                            "Velocity Error Fault",  # 12
                            "N/A",  # 13
                            "N/A",  # 14
                            "External Fault",  # 15
                            "N/A",  # 16
                            "Motor Temperature Fault",  # 17
                            "Amplifier Temperature Fault",  # 18
                            "Encoder Fault",  # 19
                            "Communication Lost Fault",  # 20
                            "N/A",  # 21
                            "N/A",  # 22
                            "Feedback Scaling Fault",  # 23
                            "Marker Search Fault",  # 24
                            "N/A",  # 25
                            "N/A",  # 26
                            "Voltage Clamp Fault",  # 27
                            "Power Supply Fault"  # 28
                            ]

    def run(self):
        while(self._is_running):
            # Spread out the calls to status
            s_fault = int(TIMC.acmd("STATUS", "AXISFAULT (SCANHEAD)"))
            p_fault = int(TIMC.acmd("STATUS", "AXISFAULT (PUSHER)"))

            # If ESTOP fault, else check all other
            if (0b100000000000 & s_fault or 0b100000000000 & p_fault):
                TIMC.scanhead.disable_axis()
                TIMC.pusher.disable_axis()
                TIMC.fault.update_status("ESTOP was pressed")
            else:
                faultMask = 1
                if (s_fault != 0):
                    TIMC.scanhead.disable_axis()
                    for i in range(0, len(self.fault_array)):
                        if ((s_fault & (faultMask << i)) != 0):
                            TIMC.fault.update_status("FAULT: Scanhead " + str(self.fault_array[i]))

                if (p_fault != 0):
                    TIMC.pusher.disable_axis()
                    for i in range(0, len(self.fault_array)):
                        if ((p_fault & (faultMask << i)) != 0):
                            TIMC.fault.update_status("FAULT: Pusher " + str(self.fault_array[i]))
            time.sleep(1)
    def stop(self):
        self._is_running = 0

# Update the feedback on the GUI
class UpdateFeedback(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self._is_running = 1
        self.write_index = 0
        self.read_index = 0
        self.write_cmd = ["PFBKPROG(SCANHEAD)", "IFBK(SCANHEAD)", "PERR(SCANHEAD)", "PFBKPROG (PUSHER)", "IFBK(PUSHER)",
                          "PERR(PUSHER)"]


    def run(self):
        while (self._is_running):
            time.sleep(FBK_THREAD_WAIT)
            # If there is something in the read queue, update the correct variable
            if (TIMC.qFBK_read.qsize()):

                data = TIMC.qFBK_read.get()
                data = data.replace("%", "")
                if (self.read_index == 0):
                    pos = round(float(data), 2)
                    pos = format(pos, '.2f')
                    TIMC.scanhead.mtr_position.set(pos)
                    self.read_index += 1
                elif (self.read_index == 1):
                    cur = float(data) * 1000
                    cur = round(cur)
                    TIMC.scanhead.mtr_current.set(cur)
                    self.read_index += 1
                elif (self.read_index == 2):
                    err = data.replace("\n", "")
                    err = float(err)
                    TIMC.scanhead.updatePosError(err)
                    self.read_index += 1
                elif (self.read_index == 3):
                    pos = round(float(data), 2)
                    pos = format(pos, '.2f')
                    TIMC.pusher.mtr_position.set(pos)
                    self.read_index += 1
                elif (self.read_index == 4):
                    cur = float(data) * 1000
                    cur = round(cur)
                    TIMC.pusher.mtr_current.set(cur)
                    self.read_index += 1
                elif (self.read_index == 5):
                    err = data.replace("\n", "")
                    err = float(err)
                    TIMC.pusher.updatePosError(err)
                    self.read_index = 0
                else:
                    print("HERE")
            if (TIMC.qFBK_write.qsize() == 0):
                TIMC.qFBK_write.put(self.write_cmd[self.write_index])
                if (self.write_index < 5):
                    self.write_index += 1
                else:
                    self.write_index = 0
    def stop(self):
        self._is_running = 0

class UpdateLog(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self._is_running = 1
        self.queue = queue
        self.estop_flag = 0
        self.fault_array = ["PositionError Fault",  # 0
                            "OverCurrent Fault",  # 1
                            "CW/Positive End-of-Travel Limit Fault",  # 2
                            "CCW/Negative End-of-Travel Limit Fault",  # 3
                            "CW/High Software Limit Fault",  # 4
                            "CCW/Low Software Limit Fault",  # 5
                            "Amplifier Fault",  # 6
                            "Position Feedback Fault",  # 7
                            "Velocity Feedback Fault",  # 8
                            "Hall Sensor Fault",  # 9
                            "Maximum Velocity Command Fault",  # 10
                            "Emergency Stop Fault",  # 11
                            "Velocity Error Fault",  # 12
                            "N/A",  # 13
                            "N/A",  # 14
                            "External Fault",  # 15
                            "N/A",  # 16
                            "Motor Temperature Fault",  # 17
                            "Amplifier Temperature Fault",  # 18
                            "Encoder Fault",  # 19
                            "Communication Lost Fault",  # 20
                            "N/A",  # 21
                            "N/A",  # 22
                            "Feedback Scaling Fault",  # 23
                            "Marker Search Fault",  # 24
                            "N/A",  # 25
                            "N/A",  # 26
                            "Voltage Clamp Fault",  # 27
                            "Power Supply Fault"  # 28
                            ]


    def run(self):
        while(self._is_running):
            time.sleep(FBK_THREAD_WAIT)
            if (self.queue.qsize()):
                data = self.queue.get()
                data = data.replace("b'","")
                data = data.replace("\n", "")
                data = data.replace("\\n","")
                data = data.replace("%", "")
                data = data.replace("'","")
                # Eliminate all results from feedback
                if("FBK" not in data):
                    # Stat
                    if("STAT:" in data):
                        data = data.replace("STAT:", "")
                        if("SCANHEAD" in data):
                            data = int(data.replace("AXISFAULT (SCANHEAD)", ""))
                            if (data and not  self.estop_flag):
                                for i in range(0, len(self.fault_array)):
                                    faultMask = 1
                                    if ((data & (faultMask << i)) != 0):
                                        if(i == 11):
                                            self.estop_flag = 1
                                            print("ESTOP Pressed")
                                        else:
                                            print("FAULT: Scanhead " + str(self.fault_array[i]))

                        elif("PUSHER" in data):
                            data = int(data.replace("AXISFAULT (PUSHER)", ""))
                            if (data and not  self.estop_flag):
                                faultMask = 1
                                for i in range(0, len(self.fault_array)):
                                    if ((data & (faultMask << i)) != 0):
                                        if (i == 11):
                                            self.estop_flag = 1
                                            print("ESTOP Pressed")
                                        else:
                                            print("FAULT: Scanhead " + str(self.fault_array[i]))
                    elif("CTRL:" in data and not "STATUS" in data):
                        if("ACKNOWLEDGEALL" in data):
                            self.estop_flag = 0
                        print(data)
                    #else:
                        #print("Junk: ",data)

    def stop(self):
        self._is_running = 0

def on_closing():
    exception_flag = 0
    if(TIMC.online):
        try:
            TIMC.scanhead.disable_axis()
        except:
            exception_flag = 1
        try:
            TIMC.pusher.disable_axis()
        except:
            exception_flag = 1
        try:
            process_status.stop()
        except:
            exception_flag = 1
        try:
            process_log.stop()
        except:
            exception_flag = 1
        try:
            process_feedback.stop()
        except:
            exception_flag = 1
        try:
            TIMC.process_serial.stop()
        except:
            exception_flag = 1
    if(exception_flag):
        print("ERROR CLOSING A THREAD")
    root.destroy()

def print_queue_sizes():
    print("FBK_r:", TIMC.qFBK_read.qsize(), " qFBK_w:", TIMC.qFBK_write.qsize(), " qStatus_r:",
          TIMC.qStatus_read.qsize(), " qStatus_w:", TIMC.qStatus_write.qsize(), " qScan_r:", TIMC.qScan_read.qsize(),
          " qScan_w:",
          TIMC.qScan_write.qsize(), " qControl_r", TIMC.qControl_read.qsize(), " qControl_w",
          TIMC.qControl_write.qsize(), " qLog:", TIMC.qLog.qsize())

######################################
#             Main Code              #
######################################

root = Tk()
TIMC = MainWindow(root, SetupMainWindow())

if (TIMC.online):
    # Start thread to updated position, current and error feedback for each axis
    process_feedback = UpdateFeedback()
    process_feedback.start()

    # Start thread to monitor for ESTOP and faults etc.
    process_status = UpdateStatus()
    process_status.start()

    # Start thread for generating log file
    process_log = UpdateLog(TIMC.qLog)
    process_log.start()

    # If axis are enabled at startup, disabled them
    TIMC.scanhead.disable_axis()
    TIMC.pusher.disable_axis()

    TIMC.scan.e_scanStart.insert(END, "0")
    TIMC.scan.e_scanStop.insert(END, "20")
    TIMC.scan.e_indexStart.insert(END, "0")
    TIMC.scan.e_indexStop.insert(END, "-2")
    TIMC.scan.e_indexSize.insert(END, "1")
    TIMC.scanhead.enable_axis()
    TIMC.pusher.enable_axis()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

