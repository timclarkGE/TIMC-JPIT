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
# https://www.troyfawkes.com/learn-python-multithreading-queues-basics/
# https://codewithoutrules.com/2017/08/16/concurrency-python/
# https://www.slideshare.net/dabeaz/an-introduction-to-python-concurrency

# Serial Threads and Queues
# https://stackoverflow.com/questions/16938647/python-code-for-serial-data-to-print-on-window

FBK_THREAD_WAIT = 0.0001
SCAN_THREAD_WAIT = 0.25

start_time = time.time()
elapsed_time = 0

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
        self.online = 1

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
        self.init_communication()

    def acmd(self, text):
        global start_time, elapsed_time
        self.write_queue.put(text)
        data = self.read_queue.get()
        print(text, repr(data))
        elapsed_time = time.time() - start_time
        if(elapsed_time > 0.1):
            print("========== 100+ ms ==========")
            start_time = time.time()
            elapsed_time = 0

        if "!" in data:
            self.fault.update_status("TIMC: Bad Execution")
            return 0
        elif "#" in data:
            #TODO: when jogging at fast speeds, this error will pop up when attempting to change direction before the axis has stopped.
            self.fault.update_status("TIMC: Acknowledge but cannot execute command")
            return 0
        elif "$" in data:
            self.fault.update_status("TIMC: Command timed out")
            return 0
        elif data == "":
            #TODO: check that unplugging the serial connection creates this error
            self.fault.update_status("TIMC: No data, check serial connection")
            return 0
        else:
            data = data.replace("%", "")
            # self.fault.update_status("Success :"+data)
            return data

    def init_communication(self):
        if(self.process_serial.port_open == 0):
            self.fault.update_status("OFFLINE MODE")
            self.scanhead.enableButton.config(state="disabled")
            self.pusher.enableButton.config(state="disabled")
            self.scan.start.config(state="disabled")
            self.online = 0
        elif(self.process_serial.port_open == 1):
            self.acmd("ACKNOWLEDGEALL")
            self.acmd("WAIT MODE NOWAIT")


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
        elif(len(result) > 1):
            self.port_open = 2
        else:
            self._is_running = 0
            try:
                TIMC.fault.update_status("TEST")
            except:
                print("TIMC Window Not Initialized")

        while self._is_running:
            # Check if there are commands to be written
            time.sleep(FBK_THREAD_WAIT)
            if self.write_queue.qsize():
                command = self.write_queue.get().encode('ascii') + b' \n'
                self.s.write(command)
                data = self.s.readline().decode('ascii')
                self.read_queue.put(data)

    def stop(self):
        self._is_running = 0
        try:
            self.s.close()
        except:
            print("No Serial Port to Close")

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
        TIMC.acmd("ENABLE " + self.axisName)
        if ((0b1 & int(TIMC.acmd("AXISSTATUS(" + self.axisName + ")"))) == 1):
            self.state=1
            self.activate_all_btns()

    def disable_axis(self):
        TIMC.acmd("DISABLE " + self.axisName)
        if ((0b1 & int(TIMC.acmd("AXISSTATUS(" + self.axisName + ")"))) == 0):
            self.enableButton.config(text="OFF", bg="#d3d3d3")
            self.state=0
            self.inactivate_all_btns()

    def inactivate_all_btns(self):

        self.jog_fwd.config(state="disabled")
        self.jog_rev.config(state="disabled")
        self.set_pos.config(state="disabled")
        self.go_to.config(state="disabled")
        self.inc.config(state="disabled")
        self.vel.config(state="disabled")

    def activate_all_btns(self):
        if ((0b1 & int(TIMC.acmd("AXISSTATUS(" + self.axisName + ")"))) == 1):
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
        TIMC.acmd("POSOFFSET SET " + self.axisName + ", " + posToSet)

    def move_to(self):
        distance = str(self.e_goTo.get())
        if (distance == ""):
            return
        speed = str(self.vel.get())
        TIMC.acmd("MOVEABS " + self.axisName + " " + distance + " F " + speed)

    def move_inc(self):
        TIMC.acmd("ABORT " + self.axisName)
        distance = str(self.e_inc.get())
        speed = str(self.vel.get())
        TIMC.acmd("MOVEINC " + self.axisName + " " + distance + " F " + speed)

    def jog_forward(self):
        if(self.state == 1 and self.enableButton['state'] != 'disabled'):
            TIMC.acmd("ABORT " + self.axisName)
            speed = str(self.vel.get())
            TIMC.acmd("FREERUN " + self.axisName + " " + speed)

    def jog_backward(self):
        if (self.state == 1 and self.enableButton['state'] != 'disabled'):
            TIMC.acmd("ABORT " + self.axisName)
            speed = str(-1*self.vel.get())
            TIMC.acmd("FREERUN " + self.axisName + " " + speed)

    def stop_jog(self):
        if(TIMC.online):
            TIMC.acmd("FREERUN " + self.axisName + " 0")

    def updatePosError(self, canvas, error):
        #TODO check this later when in the mockup.
        #Max Error for x1 = 401+61 = 462
        calc_error = int(abs((error/self.max_pos_error))*61)
        if(calc_error>61):
            calc_error = 61
        color = root.cget("bg")
        x0 = 401
        y0 = 30
        x1 = x0+calc_error
        y1 = 46
        canvas.create_rectangle(x0,y0,x0+61,y1, fill=color, outline=color)
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

        self.scanType = IntVar()
        self.scanTimeText = StringVar()
        self.scanTimeText.set("00:00:00")

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
            TIMC.scanhead.inactivate_all_btns()
            TIMC.pusher.inactivate_all_btns()
            self.start.config(state = "disabled")
            self.stop.config(state = "active")
            self.pause.config(state = "active")
            self.e_scanStart.config(state = "disabled")
            self.e_scanStop.config(state = "disabled")
            self.e_indexStart.config(state="disabled")
            self.e_indexStop.config(state="disabled")
            self.e_indexSize.config(state="disabled")
            self.radio_0.config(state = "disabled")
            self.radio_1.config(state="disabled")
            self.scanVelocity.config(state = "disabled")
            self.indexVelocity.config(state="disabled")

            # Create Scan Points
            # 0 = bidirectional, 1 unidirectional

            scan_start = int(self.e_scanStart.get())
            scan_stop = int(self.e_scanStop.get())
            index_start = int(self.e_indexStart.get())
            index_stop = int(self.e_indexStop.get())
            index = int(self.e_indexSize.get())


            i_var = index_start+index
            s_var = scan_start
            s_toggle = [scan_start, scan_stop]
            x = 0  # Toggle variable

            # Calc number of points for the scan
            # Uni-directional
            if(self.scanType.get() == 1):
                size = abs(index_stop - index_start) * 3 + 3

            # Bi-directional
            elif(self.scanType.get() == 0):
                size = abs(index_stop - index_start) * 2 + 2


            w, h = 4, size
            scan_points = [[0 for x in range(w)] for y in range(h)]

            # Calculate position for each point in scan
            # Uni-directional
            if(self.scanType.get() == 1):
                for i in range(0,size):
                    # Set s_var
                    if (i % 3 == 1):
                        s_var = scan_stop
                    # Increment i_var
                    elif (i % 3 == 0):
                        i_var += -1
                    else:
                        s_var = scan_start
                    scan_points[i][0] = s_var
                    scan_points[i][1] = i_var

            #Bi-directional
            elif(self.scanType.get() == 0):
                for i in range(0,size):
                    # Toggle s_var
                    if (i % 2):
                        x = 1 if x == 0 else 0
                        s_var = s_toggle[x]
                    # Increment i_var
                    else:
                        i_var += -1
                    scan_points[i][0] = s_var
                    scan_points[i][1] = i_var

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

        self.scanhead_moving = 0
        self.number_scanhead_moves = 0
        self.pusher_moving = 0
        self.number_pusher_moves = 0

        self.movement_start_time = 0
        self.movement_elapsed_time = 0
        self.avg_scanhead_move_time = abs(float(TIMC.scan.e_scanStart.get()) - float(TIMC.scan.e_scanStop.get())) / float(TIMC.scan.scanVelocity.get())
        self.avg_pusher_move_time = abs(float(TIMC.scan.e_indexSize.get())) / float(TIMC.scan.indexVelocity.get())
        print(self.avg_scanhead_move_time, self.avg_pusher_move_time)

    def run(self):
        while(self._is_running):
            time.sleep(SCAN_THREAD_WAIT)

            # Check if the axis have been disabled due to a fault
            if(TIMC.scanhead.state and TIMC.pusher.state and (self._is_paused != 1)):
                # Go to point
                TIMC.acmd("MOVEABS SCANHEAD " + str(self.scan_points[self.index][0]) + " F "+ str(TIMC.scan.scanVelocity.get()))
                TIMC.acmd("MOVEABS PUSHER " + str(self.scan_points[self.index][1]) + " F "+ str(TIMC.scan.indexVelocity.get()))
                if(self.index != 0):
                    self.calc_rem_scan_time()
                # Check if each axis is "in position"
                if ((0b100 & int(TIMC.acmd("AXISSTATUS(SCANHEAD)")) == 4) and (0b100 & int(TIMC.acmd("AXISSTATUS(PUSHER)")) == 4)):
                    if(self.index < (len(self.scan_points)-1)):
                        if(self.index == 0):
                            self.movement_start_time = time.time()
                        else:
                            self.movement_elapsed_time = time.time() - self.movement_start_time + self.movement_elapsed_time
                            # Calculate average move times
                            if(self.scanhead_moving and self.pusher_moving == 0):
                                self.avg_scanhead_move_time = (self.avg_scanhead_move_time*self.number_scanhead_moves + self.movement_elapsed_time)
                                self.number_scanhead_moves += 1
                                self.avg_scanhead_move_time /= self.number_scanhead_moves
                                print("Scan: ", self.avg_scanhead_move_time)
                            elif(self.pusher_moving and self.scanhead_moving == 0):
                                self.avg_pusher_move_time = (
                                            self.avg_pusher_move_time * self.number_pusher_moves + self.movement_elapsed_time)
                                self.number_pusher_moves += 1
                                self.avg_pusher_move_time /= self.number_pusher_moves
                                print("Pusher: ", self.avg_pusher_move_time)
                            # Reset time variables
                            self.movement_start_time = time.time()
                            self.movement_elapsed_time = 0
                        self.index += 1
                    else:
                        messagebox.showinfo("", "Scan is Complete")
                        self.stop()
            # If an axis faults stay in scan mode
            elif(TIMC.scanhead.state == 0 or TIMC.pusher.state == 0):
                self.pause()

    def stop(self):
        self._is_running = 0
        TIMC.acmd("ABORT SCANHEAD")
        TIMC.acmd("ABORT PUSHER")
        TIMC.scanhead.activate_all_btns()
        TIMC.pusher.activate_all_btns()
        TIMC.scan.start.config(state="active")
        TIMC.scan.stop.config(state="disabled")
        TIMC.scan.pause.config(state="disabled")
        TIMC.scan.resume.config(state="disabled")
        TIMC.scan.pause.config(state="active")
        TIMC.scan.e_scanStart.config(state="normal")
        TIMC.scan.e_scanStop.config(state="normal")
        TIMC.scan.e_indexStart.config(state="normal")
        TIMC.scan.e_indexStop.config(state="normal")
        TIMC.scan.e_indexSize.config(state="normal")
        TIMC.scan.radio_0.config(state="normal")
        TIMC.scan.radio_1.config(state="normal")
        TIMC.scan.scanVelocity.config(state="normal")
        TIMC.scan.indexVelocity.config(state="normal")
        TIMC.scan.scanTimeText.set("00:00:00")

    def pause(self):
        self._is_paused = 1
        TIMC.acmd("ABORT SCANHEAD")
        TIMC.acmd("ABORT PUSHER")
        TIMC.scan.pause.config(state="disabled")
        TIMC.scan.resume.config(state="active")
        self.movement_elapsed_time = time.time() - self.movement_start_time

    def resume(self):
        self._is_paused = 0
        TIMC.scan.pause.config(state="active")
        TIMC.scan.resume.config(state="disabled")
        self.movement_start_time = time.time()

    def calc_rem_scan_time(self):
        scanhead_pos = float(TIMC.scanhead.mtr_position.get())
        pusher_pos = float(TIMC.pusher.mtr_position.get())
        scan_time = 0

        # Determine which axis is moving
        self.scanhead_moving = abs(self.scan_points[self.index][0] - self.scan_points[self.index-1][0])
        self.pusher_moving = abs(self.scan_points[self.index][1] - self.scan_points[self.index-1][1])

        # Calculate time to complete move to next scan point
        if(self.scanhead_moving and  self.pusher_moving == 0):
            scan_time = abs(scanhead_pos - self.scan_points[self.index][0]) / TIMC.scan.scanVelocity.get()
        elif(self.pusher_moving and  self.scanhead_moving == 0):
            scan_time = abs(pusher_pos - self.scan_points[self.index][1]) / TIMC.scan.indexVelocity.get()
        # If not on the last move, then calculate remaining scan time
        for i in range(self.index+1, len(self.scan_points)):
            scanhead_move = abs(self.scan_points[i][0] - self.scan_points[i - 1][0])
            pusher_move = abs(self.scan_points[i][1] - self.scan_points[i - 1][1])
            if (scanhead_move and pusher_move == 0):
                scan_time += self.avg_scanhead_move_time
            elif(pusher_move and scanhead_move == 0):
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
        self.button = Button(self.canvas, text="FAULT\nRESET", fg="black", bg="#d3d3d3", height=2, width=5, command=lambda: self.fault_ack())
        #self.label_0 = Label(canvas, text="GE HITACHI", height=2, font=("Helvetica", 10))
        self.entry = Entry(self.canvas, width=59, textvariable = self.status_text)
        self.label_0.grid(row=0, column=0, columnspan=2, sticky=W)
        self.entry.grid(row=1, column=0, columnspan=2, padx=30)
        self.button.grid(row=1,column=2, pady=5, padx=5)

    def update_status(self, text):
            self.canvas.config(bg = "red")
            self.label_0.config(bg = "red")
            self.status_text.set(text)

    def fault_ack(self):
        if(TIMC.online):
            TIMC.acmd("ACKNOWLEDGEALL")
            color = root.cget("bg")
            self.canvas.config(bg=color)
            self.label_0.config(bg=color)
            self.status_text.set("")

def check_faults():
    fault_array = [  "PositionError Fault",  #0
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

    s_fault = int(TIMC.acmd("AXISFAULT (SCANHEAD)"))
    p_fault = int(TIMC.acmd("AXISFAULT (PUSHER)"))

    #If ESTOP fault, else check all other
    if(0b100000000000 & s_fault or 0b100000000000 & p_fault):
        TIMC.scanhead.disable_axis()
        TIMC.pusher.disable_axis()
        TIMC.fault.update_status("ESTOP")
    else:
        faultMask = 1
        if(s_fault != 0):
            TIMC.scanhead.disable_axis()
            for i in range(0, len(fault_array)):
                if((s_fault & (faultMask << i)) != 0):
                    TIMC.fault.update_status("FAULT: Scanhead " + str(fault_array[i]))

        if(p_fault != 0):
            TIMC.pusher.disable_axis()
            for i in range(0, len(fault_array)):
                if((p_fault & (faultMask << i)) != 0):
                    TIMC.fault.update_status("FAULT: Pusher "+ str(fault_array[i]))

    root.after(750, check_faults)

def on_closing():
    TIMC.scanhead.disable_axis()
    TIMC.pusher.disable_axis()
    TIMC.process_serial.stop()
    print(threading.enumerate())
    root.destroy()

# ASCII cmd
def acmd2(text):
    TIMC.write_queue.put(text)
    data = TIMC.read_queue.get()
    #ser = serial.Serial("COM20", 115200)
    #ser.write(text.encode('ascii') + b' \n')
    #data = ser.readline().decode('ascii')
    if "!" in data:
        TIMC.fault.update_status("TIMC: Bad Execution")
        return 0
    elif "#" in data:
        TIMC.fault.update_status("TIMC: Acknowledge but cannot execute command")
        return 0
    elif "$" in data:
        TIMC.fault.update_status("TIMC: Command timed out")
        return 0
    elif data == "":
        TIMC.fault.update_status("TIMC: No data, check serial connection")
        return 0
    else:
        data = data.replace("%", "")
        #TIMC.fault.update_status("Success :"+data)
        return data

def update_fbk():
    #time_start = time.clock()

    pos = TIMC.acmd("PFBKPROG(SCANHEAD)")
    pos = round(float(pos), 2)
    pos = format(pos, '.2f')
    TIMC.scanhead.mtr_position.set(pos)

    cur = TIMC.acmd("IFBK(SCANHEAD)")
    cur = float(cur) * 1000
    cur = round(cur)
    TIMC.scanhead.mtr_current.set(cur)

    err = TIMC.acmd("PERR(SCANHEAD)")
    err = err.replace("\n", "")
    err = float(err)
    TIMC.scanhead.updatePosError(TIMC.scanhead.canvas, err)


    pos = TIMC.acmd("PFBKPROG(PUSHER)")
    pos = round(float(pos), 2)
    pos = format(pos, '.2f')
    TIMC.pusher.mtr_position.set(pos)

    cur = TIMC.acmd("IFBK(PUSHER)")
    cur = float(cur) * 1000
    cur = round(cur)
    TIMC.pusher.mtr_current.set(cur)

    err = TIMC.acmd("PERR(PUSHER)")
    err = err.replace("\n", "")
    err = float(err)
    TIMC.pusher.updatePosError(TIMC.pusher.canvas, err)

    #print(time.clock()-time_start)

    root.after(100,update_fbk)


######################################
#             Main Code              #
######################################

root = Tk()
TIMC = MainWindow(root, SetupMainWindow())

#root.after(100, TIMC.scanhead.update_fbk)
#root.after(200, TIMC.pusher.update_fbk)
if(TIMC.online):
    print(threading.enumerate())
    root.after(100, update_fbk)
    TIMC.scanhead.disable_axis()
    TIMC.pusher.disable_axis()
    root.after(1000, check_faults)

    #TIMC.scan.e_scanStart.insert(END, "0")
    #TIMC.scan.e_scanStop.insert(END, "20")
    #TIMC.scan.e_indexStart.insert(END, "0")
    #TIMC.scan.e_indexStop.insert(END, "-2")
    #TIMC.scan.e_indexSize.insert(END, "1")
    #TIMC.scanhead.enable_axis()
    #TIMC.pusher.enable_axis()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

