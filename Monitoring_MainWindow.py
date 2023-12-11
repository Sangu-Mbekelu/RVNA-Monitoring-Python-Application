# Imports from python packages
import os

from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, QLineEdit, QLabel, QTabWidget
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtCore import Signal, QThread, QTimer, QPointF, Qt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries, QValueAxis
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from paramiko import SSHClient, AutoAddPolicy
import pandas as pd
import time
from os import getcwd, remove

# Imports from other python files
import User_Pass_Key


class MonitorWindow(QMainWindow):

    def __init__(self, app):    # Main Window Constructor
        super().__init__()
        self.app = app
        self.setWindowTitle("RVNA Measurement Monitor Application")  # Set Window Title
        self.setWindowIcon(QIcon("Resources\\PlotIcon.png"))  # Set Window Icon
        self.resize(1250, 600)  # Setting Window Size

        # Graphing Parameters
        self.time_elapsed_min = 0
        self.time_elapsed_max = 30
        self.inflection_frequency_max = 1500
        self.inflection_frequency_min = 1000
        self.inflection_impedance_max = 100
        self.inflection_impedance_min = 0
        self.smoothing = 1

        # Initializing Timer and File Transfer Thread =============================================
        self.transfer = ServerTransferThread()
        self.transfer.bad_folder.connect(self.bad_folder_name)

        self.transfer_timer = QTimer()
        self.transfer_timer.timeout.connect(self.run_file_transfer)
        self.transfer_timer.setInterval(3000)  # Every 5 seconds, the program will attempt to connect to the server and upload log file
        self.transfer_timer.start()
        # =========================================================================================

        # Button for Folder Input =================================================================
        self.folder_window = ServerFolderWidget()
        self.folder_window.folder_name.connect(self.set_folder_name)
        # Adding Push Button to Start Graphing (User Must Input Folder Name)
        self.graph_start = QPushButton("Enter Folder Name")
        self.graph_start.setFixedWidth(300)
        self.graph_start.setFixedHeight(40)
        self.graph_start.clicked.connect(self.folder_window.show)
        # =========================================================================================

        # Entries for Graph Axis Changes ==========================================================
        # Line Edits to change graph axis ranges
        self.set_time_elapsed_min = QLineEdit()
        self.set_time_elapsed_min.setFixedWidth(100)
        self.set_time_elapsed_min.returnPressed.connect(self.enter_time_elapsed)
        self.time_elapsed_min_label = QLabel()
        self.time_elapsed_min_label.setText("Time Elapsed (min): ")
        self.time_elapsed_min_label.setFixedWidth(105)
        self.set_time_elapsed_max = QLineEdit()
        self.set_time_elapsed_max.setFixedWidth(100)
        self.set_time_elapsed_max.returnPressed.connect(self.enter_time_elapsed)
        self.time_elapsed_max_label = QLabel()
        self.time_elapsed_max_label.setText("Time Elapsed (max): ")
        self.time_elapsed_max_label.setFixedWidth(105)
        self.set_inflection_frequency_min = QLineEdit()
        self.set_inflection_frequency_min.setFixedWidth(100)
        self.set_inflection_frequency_min.returnPressed.connect(self.enter_inflection_frequency)
        self.inflection_frequency_min_label = QLabel()
        self.inflection_frequency_min_label.setText("Inflection Frequency (min): ")
        self.inflection_frequency_min_label.setFixedWidth(142)
        self.set_inflection_frequency_max = QLineEdit()
        self.set_inflection_frequency_max.setFixedWidth(100)
        self.set_inflection_frequency_max.returnPressed.connect(self.enter_inflection_frequency)
        self.inflection_frequency_max_label = QLabel()
        self.inflection_frequency_max_label.setText("Inflection Frequency (max): ")
        self.inflection_frequency_max_label.setFixedWidth(142)
        self.set_inflection_impedance_min = QLineEdit()
        self.set_inflection_impedance_min.setFixedWidth(100)
        self.set_inflection_impedance_min.returnPressed.connect(self.enter_inflection_impedance)
        self.inflection_impedance_min_label = QLabel()
        self.inflection_impedance_min_label.setText("Inflection Impedance (min): ")
        self.inflection_impedance_min_label.setFixedWidth(145)
        self.set_inflection_impedance_max = QLineEdit()
        self.set_inflection_impedance_max.setFixedWidth(100)
        self.set_inflection_impedance_max.returnPressed.connect(self.enter_inflection_impedance)
        self.inflection_impedance_max_label = QLabel()
        self.inflection_impedance_max_label.setText("Inflection Impedance (max): ")
        self.inflection_impedance_max_label.setFixedWidth(145)
        # Line Edit for Smoothing
        self.set_smoothing = QLineEdit()
        self.set_smoothing.setFixedWidth(100)
        self.set_smoothing.returnPressed.connect(self.enter_smoothing)
        self.smoothing_label = QLabel()
        self.smoothing_label.setFixedWidth(60)
        self.smoothing_label.setText("Smoothing: ")
        # =========================================================================================

        # Graph Properties ========================================================================
        # X-axis used for S11 graph
        self.frequency_axis = QValueAxis()
        self.frequency_axis.setRange(0.85, 4)  # Sets graph from 0.85-4 GHz
        self.frequency_axis.setLabelFormat("%0.2f")
        self.frequency_axis.setTickType(QValueAxis.TickType.TicksFixed)
        self.frequency_axis.setTickCount(21)
        self.frequency_axis.setTitleText("Frequency [GHz]")
        # Y-axis used for S11 graph
        self.s11_mag_axis = QValueAxis()
        self.s11_mag_axis.setRange(-50, 0)
        self.s11_mag_axis.setLabelFormat("%0.1f")
        self.s11_mag_axis.setTickType(QValueAxis.TickType.TicksFixed)
        self.s11_mag_axis.setTickCount(13)
        self.s11_mag_axis.setTitleText("S11 [dB]")

        self.s11_series = QLineSeries()

        # Elapsed Time Axis 1
        self.time_elapsed_axis_1 = QValueAxis()
        self.time_elapsed_axis_1.setRange(self.time_elapsed_min, self.time_elapsed_max)
        self.time_elapsed_axis_1.setLabelFormat("%0.1f")
        self.time_elapsed_axis_1.setTickType(QValueAxis.TickType.TicksFixed)
        self.time_elapsed_axis_1.setTickCount(21)
        self.time_elapsed_axis_1.setTitleText("Time Elapsed [min]")

        # Elapsed Time Axis 2
        self.time_elapsed_axis_2 = QValueAxis()
        self.time_elapsed_axis_2.setRange(self.time_elapsed_min, self.time_elapsed_max)
        self.time_elapsed_axis_2.setLabelFormat("%0.1f")
        self.time_elapsed_axis_2.setTickType(QValueAxis.TickType.TicksFixed)
        self.time_elapsed_axis_2.setTickCount(21)
        self.time_elapsed_axis_2.setTitleText("Time Elapsed [min]")

        # Inflection Frequency Axis
        self.inflection_frequency_axis = QValueAxis()
        self.inflection_frequency_axis.setLabelFormat("%0.1f")
        self.inflection_frequency_axis.setTickType(QValueAxis.TickType.TicksFixed)
        self.inflection_frequency_axis.setTickCount(11)
        self.inflection_frequency_axis.setTitleText("Inflection Frequency [MHz]")
        self.inflection_frequency_axis.setRange(self.inflection_frequency_min, self.inflection_frequency_max)

        # Inflection Impedance Axis
        self.inflection_impedance_axis = QValueAxis()
        self.inflection_impedance_axis.setLabelFormat("%0.1f")
        self.inflection_impedance_axis.setTickType(QValueAxis.TickType.TicksFixed)
        self.inflection_impedance_axis.setTickCount(11)
        self.inflection_impedance_axis.setTitleText("Inflection Impedance [RE ohm]")
        self.inflection_impedance_axis.setRange(self.inflection_impedance_min, self.inflection_impedance_max)

        # Y-axis used for inflection impedance graph
        self.s11_min_axis = QValueAxis()
        self.s11_min_axis.setRange(-40, 0)
        self.s11_min_axis.setLabelFormat("%d")
        self.s11_min_axis.setTickType(QValueAxis.TickType.TicksFixed)
        self.s11_min_axis.setTickCount(11)
        self.s11_min_axis.setTitleText("S11 @ Inflection Frequency [dB]")

        self.inflection_frequency_series = QLineSeries()
        self.inflection_frequency_series.setName("Infection Frequency")
        self.s11_min_series = QScatterSeries()
        self.s11_min_series.setName("Minimum S11")
        self.s11_min_series.setMarkerSize(2)
        self.s11_min_series.setBorderColor(Qt.GlobalColor.transparent)

        self.inflection_impedance_series = QLineSeries()

        self.Plotting_Graph = QTimer()
        self.Plotting_Graph.timeout.connect(self.graphing_plots)
        self.Plotting_Graph.setInterval(2000)  # Every 2 second, the program will update graphs
        self.Plotting_Graph.start()
        # =========================================================================================

        # Graphs for Tabs =========================================================================
        self.Inflection_Frequency_Graph = QChart()
        self.Inflection_Frequency_Graph.setTitle('Inflection Frequency Over Time')
        self.Inflection_Frequency_Graph.addAxis(self.s11_min_axis, Qt.AlignmentFlag.AlignRight)
        self.Inflection_Frequency_Graph.addAxis(self.time_elapsed_axis_1, Qt.AlignmentFlag.AlignBottom)
        self.Inflection_Frequency_Graph.addAxis(self.inflection_frequency_axis, Qt.AlignmentFlag.AlignLeft)

        self.Inflection_Frequency_Graph_View = QChartView(self.Inflection_Frequency_Graph)
        self.Inflection_Frequency_Graph_View.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.Inflection_Impedance_Graph = QChart()
        self.Inflection_Impedance_Graph.setTitle('Inflection Impedance Over Time')
        self.Inflection_Impedance_Graph.legend().hide()
        self.Inflection_Impedance_Graph.addAxis(self.time_elapsed_axis_2, Qt.AlignmentFlag.AlignBottom)
        self.Inflection_Impedance_Graph.addAxis(self.inflection_impedance_axis, Qt.AlignmentFlag.AlignLeft)

        self.Inflection_Impedance_Graph_View = QChartView(self.Inflection_Impedance_Graph)
        self.Inflection_Impedance_Graph_View.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.S11_Graph = QChart()
        self.S11_Graph.setTitle('Lateset S11')
        self.S11_Graph.legend().hide()
        self.S11_Graph.addAxis(self.frequency_axis, Qt.AlignmentFlag.AlignBottom)
        self.S11_Graph.addAxis(self.s11_mag_axis, Qt.AlignmentFlag.AlignLeft)

        self.S11_Graph_View = QChartView(self.S11_Graph)
        self.S11_Graph_View.setRenderHint(QPainter.RenderHint.Antialiasing)

        # =========================================================================================

        # Tabs for Different Graphs ===============================================================
        self.tab_menu = QTabWidget()
        self.tab_menu.addTab(self.Inflection_Frequency_Graph_View, "Inflection Frequency vs Time")
        self.tab_menu.addTab(self.Inflection_Impedance_Graph_View, "Inflection Impedance vs Time")
        self.tab_menu.addTab(self.S11_Graph_View, "Latest S11")
        # =========================================================================================

        # Layout Configuration ====================================================================
        main_widget = QWidget()  # Define a main widget
        self.setCentralWidget(main_widget)  # The Central Widget includes text editor and start button

        # Two Horizontal Layouts, combined with a Vertical Layout for the graph changing Line Edits
        graph_changes_first_layout = QHBoxLayout()
        graph_changes_first_layout.addWidget(self.time_elapsed_min_label)
        graph_changes_first_layout.addWidget(self.set_time_elapsed_min)
        graph_changes_first_layout.addWidget(self.inflection_frequency_min_label)
        graph_changes_first_layout.addWidget(self.set_inflection_frequency_min)
        graph_changes_first_layout.addWidget(self.inflection_impedance_min_label)
        graph_changes_first_layout.addWidget(self.set_inflection_impedance_min)
        graph_changes_second_layout = QHBoxLayout()
        graph_changes_second_layout.addWidget(self.time_elapsed_max_label)
        graph_changes_second_layout.addWidget(self.set_time_elapsed_max)
        graph_changes_second_layout.addWidget(self.inflection_frequency_max_label)
        graph_changes_second_layout.addWidget(self.set_inflection_frequency_max)
        graph_changes_second_layout.addWidget(self.inflection_impedance_max_label)
        graph_changes_second_layout.addWidget(self.set_inflection_impedance_max)
        graph_changes_layout = QVBoxLayout()
        graph_changes_layout.addLayout(graph_changes_first_layout)
        graph_changes_layout.addLayout(graph_changes_second_layout)

        smoothing_layout = QHBoxLayout()
        smoothing_layout.addWidget(self.smoothing_label)
        smoothing_layout.addWidget(self.set_smoothing)

        above_tabs_layout = QHBoxLayout()   # Combines Button and Line Edits
        above_tabs_layout.addWidget(self.graph_start)
        above_tabs_layout.addLayout(smoothing_layout)
        above_tabs_layout.addLayout(graph_changes_layout)

        window_layout = QVBoxLayout(main_widget)    # Combines top combination of widgets with the tabs
        window_layout.addLayout(above_tabs_layout)
        window_layout.addWidget(self.tab_menu)
        # =========================================================================================

        # Menubar =================================================================================
        self.menu_bar = self.menuBar()
        # Help Menu (Used to help users)
        help_menu = self.menu_bar.addMenu("Help")
        pdf_help_action = help_menu.addAction("Help Document")
        self.pdf_view_window = HelpWidget()
        pdf_help_action.triggered.connect(self.pdf_view_window.show)

    def run_file_transfer(self):
        self.transfer.start()

    @staticmethod
    def set_folder_name(folder_name):
        ServerTransferThread.measurements_directory = folder_name

    @staticmethod
    def bad_folder_name():
        ServerTransferThread.measurements_directory = None
        # User Alert MessageBox to notify user that the folder name does not exist on the server
        user_alert = QMessageBox()
        user_alert.setWindowTitle("Attention")
        user_alert.setText("Folder Name does not exist on Server")
        user_alert.setInformativeText("Please Change the Folder Name")
        user_alert.setIcon(QMessageBox.Icon.Warning)
        user_alert.addButton(QMessageBox.StandardButton.Ok)
        user_alert.exec()

    def enter_inflection_impedance(self):
        min_imp = self.set_inflection_impedance_min.text()
        max_imp = self.set_inflection_impedance_max.text()
        if min_imp != "" and max_imp == "":
            try:
                if float(min_imp) < float(self.inflection_impedance_max):
                    self.inflection_impedance_min = float(min_imp)
                    self.inflection_impedance_axis.setRange(self.inflection_impedance_min, self.inflection_impedance_max)
                else:
                    pass
            except ValueError:
                pass
        elif min_imp == "" and max_imp != "":
            try:
                if float(max_imp) > float(self.inflection_impedance_min):
                    self.inflection_impedance_max = float(max_imp)
                    self.inflection_impedance_axis.setRange(self.inflection_impedance_min, self.inflection_impedance_max)
                else:
                    pass
            except ValueError:
                pass
        else:
            try:
                if float(max_imp) > float(min_imp):
                    self.inflection_impedance_max = float(max_imp)
                    self.inflection_impedance_min = float(min_imp)
                    self.inflection_impedance_axis.setRange(self.inflection_impedance_min, self.inflection_impedance_max)
                else:
                    pass
            except ValueError:
                pass

    def enter_time_elapsed(self):
        min_time = self.set_time_elapsed_min.text()
        max_time = self.set_time_elapsed_max.text()
        if min_time != "" and max_time == "":
            try:
                if float(min_time) < float(self.time_elapsed_max):
                    self.time_elapsed_min = float(min_time)
                    self.time_elapsed_axis_1.setRange(self.time_elapsed_min, self.time_elapsed_max)
                    self.time_elapsed_axis_2.setRange(self.time_elapsed_min, self.time_elapsed_max)
                else:
                    pass
            except ValueError:
                pass
        elif min_time == "" and max_time != "":
            try:
                if float(max_time) > float(self.time_elapsed_min):
                    self.time_elapsed_max = float(max_time)
                    self.time_elapsed_axis_1.setRange(self.time_elapsed_min, self.time_elapsed_max)
                    self.time_elapsed_axis_2.setRange(self.time_elapsed_min, self.time_elapsed_max)
                else:
                    pass
            except ValueError:
                pass
        else:
            try:
                if float(max_time) > float(min_time):
                    self.time_elapsed_max = float(max_time)
                    self.time_elapsed_min = float(min_time)
                    self.time_elapsed_axis_1.setRange(self.time_elapsed_min, self.time_elapsed_max)
                    self.time_elapsed_axis_2.setRange(self.time_elapsed_min, self.time_elapsed_max)
                else:
                    pass
            except ValueError:
                pass

    def enter_inflection_frequency(self):
        min_freq = self.set_inflection_frequency_min.text()
        max_freq = self.set_inflection_frequency_max.text()
        if min_freq != "" and max_freq == "":
            try:
                if float(min_freq) < float(self.inflection_frequency_max):
                    self.inflection_frequency_min = float(min_freq)
                    self.inflection_frequency_axis.setRange(self.inflection_frequency_min, self.inflection_frequency_max)
                else:
                    pass
            except ValueError:
                pass
        elif min_freq == "" and max_freq != "":
            try:
                if float(max_freq) > float(self.inflection_frequency_min):
                    self.inflection_frequency_max = float(max_freq)
                    self.inflection_frequency_axis.setRange(self.inflection_frequency_min, self.inflection_frequency_max)
                else:
                    pass
            except ValueError:
                pass
        else:
            try:
                if float(max_freq) > float(min_freq):
                    self.inflection_frequency_max = float(max_freq)
                    self.inflection_frequency_min = float(min_freq)
                    self.inflection_frequency_axis.setRange(self.inflection_frequency_min, self.inflection_frequency_max)
                else:
                    pass
            except ValueError:
                pass

    def graphing_plots(self):
        try:
            log_file_contents = pd.read_csv(getcwd() + '\\MonitorFiles\\Datalog.txt')  # Reads data log file as dataframe
        except:
            return
        # Inflection Frequency Graph
        self.inflection_frequency_series.clear()  # Clears data from series
        self.s11_min_series.clear()  # Clears data from series
        self.Inflection_Frequency_Graph.removeSeries(self.inflection_frequency_series)
        self.Inflection_Frequency_Graph.removeSeries(self.s11_min_series)
        inflection_frequency = log_file_contents['Inflection Frequency [Hz]'].rolling(self.smoothing).mean().tolist()  # Creates inflection frequency list
        inflection_frequency = inflection_frequency[(self.smoothing - 1):]
        elapsed_time_seconds = log_file_contents['Elapsed Times [s]'].tolist()  # Creates elapsed time list
        min_s11 = log_file_contents['S11 at Inflection Frequency [dB]'].tolist()  # Creates minimum S11 list

        for i in range(len(inflection_frequency)):
            self.inflection_frequency_series.append(QPointF((elapsed_time_seconds[i + (self.smoothing - 1)] / 60), (inflection_frequency[i]) / 1e6))  # Appends all points to series

        for i in range(len(elapsed_time_seconds)):
            self.s11_min_series.append(QPointF((elapsed_time_seconds[i] / 60), min_s11[i]))

        self.Inflection_Frequency_Graph.addSeries(self.inflection_frequency_series)  # Adds series to graph
        self.Inflection_Frequency_Graph.addSeries(self.s11_min_series)
        self.inflection_frequency_series.attachAxis(self.inflection_frequency_axis)  # Attaches both axis to the inflection frequency series
        self.inflection_frequency_series.attachAxis(self.time_elapsed_axis_1)
        self.s11_min_series.attachAxis(self.s11_min_axis)  # Attaches both axis to the minimum S11 series
        self.s11_min_series.attachAxis(self.time_elapsed_axis_1)

        # Inflection Impedance Graph
        self.inflection_impedance_series.clear()  # Clears data from series
        self.Inflection_Impedance_Graph.removeSeries(self.inflection_impedance_series)

        inflection_impedance = log_file_contents['Inflection Impedance [RE ohm]'].rolling(self.smoothing).mean().tolist()  # Creates inflection frequency list
        inflection_impedance = inflection_impedance[(self.smoothing - 1):]
        elapsed_time_seconds = log_file_contents['Elapsed Times [s]'].tolist()  # Creates elapsed time list

        for i in range(len(inflection_impedance)):
            self.inflection_impedance_series.append(QPointF((elapsed_time_seconds[i + (self.smoothing - 1)] / 60), (inflection_impedance[i])))  # Appends all points to series

        self.Inflection_Impedance_Graph.addSeries(self.inflection_impedance_series)  # Adds series to graph
        self.inflection_impedance_series.attachAxis(self.inflection_impedance_axis)  # Attaches both axis to the inflection frequency series
        self.inflection_impedance_series.attachAxis(self.time_elapsed_axis_2)

        try:
            sparam_file_contents = pd.read_csv(getcwd() + '\\MonitorFiles\\Latest_Sparams.txt')  # Reads s-parameter file as dataframe
        except:
            return
        self.s11_series.clear()  # Clears data from series
        self.S11_Graph.removeSeries(self.s11_series)  # Removes series from graph
        frequency = sparam_file_contents['Frequency [Hz]'].tolist()  # Creates frequency list
        s11_mag = sparam_file_contents['S11 [dB]'].tolist()  # Creates S11 magnitude list

        for i in range(len(frequency)):
            self.s11_series.append(QPointF(frequency[i] / 1e9, s11_mag[i]))  # Appends all points to series

        self.S11_Graph.addSeries(self.s11_series)  # Adds series to graph
        self.s11_series.attachAxis(self.frequency_axis)  # Attaches both axis to the series
        self.s11_series.attachAxis(self.s11_mag_axis)
        self.S11_Graph.setTitle(f'Antenna Reflection Data: Time Measurement was taken: {sparam_file_contents["Current Hour"][0]}:{sparam_file_contents["Current Minute"][0]}:{sparam_file_contents["Current Second"][0]}')  # Changes title based on recent inflection impedance value

    def enter_smoothing(self):
        smoothing = self.set_smoothing.text()
        try:
            int(smoothing)
            self.smoothing = int(smoothing)
        except ValueError:
            pass


class ServerFolderWidget(QWidget):
    folder_name = Signal(str)
    sftp_session = None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Change Folder Name")  # Set Window Title
        self.setWindowIcon(QIcon("Resources\\FileExplorerIcon.png"))
        self.resize(400, 100)  # Set Window Size

        # Text editor for folder name input
        self.line_edit = QLineEdit()

        # Initial Form layout used to add label to text editor
        text_edit_layout = QFormLayout()
        text_edit_layout.addRow("Fodler Name: ", self.line_edit)

        # Adding the button to receive the data input by user
        set_folder_button = QPushButton("Enter")
        set_folder_button.clicked.connect(self.set_folder_name)

        # Vertical layout used to place button below text editor
        full_layout = QVBoxLayout()
        full_layout.addLayout(text_edit_layout)
        full_layout.addWidget(set_folder_button)

        # Sets window layout
        self.setLayout(full_layout)

    def set_folder_name(self):
        if self.line_edit.text() != "":
            self.folder_name.emit(self.line_edit.text())  # Signal is emitted to Main Window
            self.close()
        else:
            pass


class ServerTransferThread(QThread):
    bad_folder = Signal()
    measurements_directory = None

    def __init__(self):
        super().__init__()
        # Setting Constant Variables for SSH
        self.ssh = SSHClient()  # Defines SSH client
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())  # Adds host key if missing
        self.sftp_session = None

        # Server Access Information
        self.server_host = User_Pass_Key.hostname
        self.server_user = User_Pass_Key.user
        self.server_password = User_Pass_Key.password
        self.server_root_directory = User_Pass_Key.remote_path

        self.connection_var = 0
        self.init_err = 0
        # Used to increment through list
        self.numb_file = 1

    def run(self):
        if ServerTransferThread.measurements_directory is not None:
            start_time = time.time()
            if self.connection_var == 0:
                try:
                    self.ssh.connect(self.server_host, username=self.server_user, password=self.server_password)  # Establishes SSH connection
                    self.sftp_session = self.ssh.open_sftp()  # Opens SFTP session
                    self.connection_var = 1
                except:
                    print("Disconnected and can't Connect Again")
                    return
            else:
                pass

            try:
                self.sftp_session.chdir(User_Pass_Key.remote_path + ServerTransferThread.measurements_directory)  # Changes directory to specified folder on the server
            except IOError:
                self.bad_folder.emit()
                return

            try:
                self.sftp_session.get(User_Pass_Key.remote_path + ServerTransferThread.measurements_directory + '/' + '0_data_log.txt', getcwd()+'\\'+'MonitorFiles'+'\\'+'Datalog.txt')
                self.sftp_session.get(User_Pass_Key.remote_path + ServerTransferThread.measurements_directory + '/' + 'Latest_Sparams.txt', getcwd()+'\\'+'MonitorFiles'+'\\'+'Latest_Sparams.txt')
            except:
                self.connection_var = 0
                pass
            end_time = time.time()
            print(f"Time elapsed connecting, transferring, and disconnecting to RIT server: {end_time - start_time} seconds")
        else:
            pass


class HelpWidget(QPdfView):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help Document")  # Set Window Title
        self.setWindowIcon(QIcon("HelpIcon.png"))
        self.resize(850, 500)
        self.help_pdf = QPdfDocument()
        self.help_pdf.load("Resources\\GlucoseMonitoringHelp.pdf")  # Loads path of help document
        self.setPageMode(QPdfView.PageMode.MultiPage)
        self.setDocument(self.help_pdf)
