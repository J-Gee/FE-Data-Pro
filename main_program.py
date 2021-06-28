import datetime
import tkinter as tk
from tkinter import ttk, filedialog
import os
from os.path import isfile, join
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import xlwings as xw
import batch_processor
import glob
import shutil
import holly_webscraper
from natsort import natsorted
import time
from threading import Thread

'''
Author: Jack C. Gee
'''
#########################################################
'''
PARAMETERS
'''

'''finds current working dir and goes up 2 to cover the bayes op'''
for i in range(2):
    path_parent = os.path.dirname(os.getcwd())
    os.chdir(path_parent)

pro_soft_dir = os.getcwd()

template_dir = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Excel Results (Processed)/Template/" \
               "files/"

output_dir = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Excel Results (Processed)/"
default_batch_loc = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Results handling test/Unprocessed"
unprocessed_batch_dir = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Results handling test/Unprocessed"
processed_batch_dir = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/Results handling test/Processed"
optimiser_dir = pro_soft_dir + "/Bayesian Optimiser/fe_optimizer-master/Optimizer/"

view_dump = pro_soft_dir + "/Formulation Engine Data Processing/Output and templates/View Dump"

template_filename = "RESULTS TEMPLATE"
filetype = ".csv"


'''inherent to current catalyst, infrequent changes '''
illu_time = 4 # Illumination time in hours

'''inherent to all sampling, no changes expected'''
every_nth_file = 7  # Which nth file is the one to process
# 4th is default from 2 cup 2 from sample samples

'''hiden relative sensitivity values'''
if every_nth_file == 4:
    rs_dict = {
        "mass 2.00": ["H2", 1.75],
        "mass 28.00": ["N2", 1.00],
        "mass 32.00": ["O2", 0.71475],
        "mass 40.00": ["Ar", 1.21],
        "mass 44.00": ["CO2", 1.4]
    }
if every_nth_file == 7:
    rs_dict = {
        "mass 2.00": ["H2", 1.853],
        "mass 28.00": ["N2", 1.00],
        "mass 32.00": ["O2", 0.7275],
        "mass 40.00": ["Ar", 1.21],
        "mass 44.00": ["CO2", 1.4]
    }

'''values for calc from hiden values'''
headspace_volume = 6.64  # (mL) Correct with more accurate value when possible
pressure = 1  # (bar)
ideal_gas_cons = 0.083145  # (L*bar / K*mol)
temperature = 293  # (K)
molar_vol_gas = (pressure)/(ideal_gas_cons*temperature) # ~24.36


'''param lists for modules
bp: batch processor
hws: holly webscraper'''
bp_params = [template_dir, output_dir, default_batch_loc, template_filename, filetype, every_nth_file, illu_time, molar_vol_gas, headspace_volume, rs_dict]

#########################################################

class listen_thread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.running = True
    def run(self):
        global unprocessed_batch_dir
        print("Starting listening thread")
        while self.running:
            dirlist = glob.glob(unprocessed_batch_dir + "/*")
            try:
                for i in dirlist:
                    batch_id = i.split("\\")[-1]
                    try:
                        if holly_webscraper.holly_complete_check(batch_id):
                            batch_processing(i)
                            time.sleep(5)
                        else:
                            continue
                    except Exception as e:
                        print(e)
            except: # catches no files in dir
                pass
            print("No valid files found - Waiting 10 mins from " + datetime.datetime.now().strftime('%H:%M:%S'))
            time.sleep(5)








class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        master.title("FE Processing")
        #master.geometry("")
        self.pack()
        container = tk.Frame(master)
        '''
        Builds a TK frame from master, container is the contents of the window (frame), master is the whole application.
        '''
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Make frames to display pages
        self.frames = {}
        #for F in (StartMenu, ExcelView, Output):
        '''blanks 1 and 2 will allow for additional windows if desired in future'''
        for F in (StartMenu, blank1, blank2):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartMenu)

    # Raises desired frame to top
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    # def update_frame(self, cont, data_type, data=None):
    #     frame = self.frames[cont]
    #     if data_type == "listbox_option_update":
    #         frame.excelview_listbox_options_update(data)
    #     if data_type == "listbox_selected_update":
    #         frame.excelview_listbox_selected_update(data)
    #     if data_type == "return_parameters":
    #         r_list = frame.excelview_return_parameters()
    #         return r_list
    #     if data_type == "data_processing":
    #         frame.output_update(data)
    #     if data_type == "update_graph":
    #         frame.output_update_graphs()
    #     if data_type == "update_dropboxes":
    #         frame.output_update_dropboxes(data)
    #     if data_type == "label_update":
    #         frame.label_update(data)

    def update_frame(self, cont, data=None, arg=None):
        frame = self.frames[cont]
        frame_switcher = {
            1: frame.label_update()
        }
        frame_switcher.get(arg, lambda: "invalid request")

class blank1(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

class blank2(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


class StartMenu(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.startmenu_label_vars()
        self.startmenu_create_widgets()
        self.pack()
    def startmenu_label_vars(self):
        self.queue_var = tk.StringVar()
        self.running_var = tk.StringVar()
        self.unprocessed_var = tk.StringVar()
        self.completed_var = tk.StringVar()

        self.label_update()


    def label_update(self):
        self.queue_var.set(str(len(glob.glob(optimiser_dir + "runqueue/*"))) + " batches in queue")
        self.running_var.set(str(len(glob.glob(optimiser_dir + "running/*")))+ " batches running")
        self.unprocessed_var.set(str(len(glob.glob(unprocessed_batch_dir + "/*")))+ " batches for processing")
        self.completed_var.set(str(len(glob.glob(optimiser_dir + "completed/*")))+ " batches completed")

    def startmenu_create_widgets(self):
        self.start_menu_frame = tk.LabelFrame(self, text="Select an option")
        self.start_menu_frame.grid(padx=20, pady=20)

        # labels
        batch_gen_label = tk.Label(self.start_menu_frame, text="Batch Generator")
        batch_process_label = tk.Label(self.start_menu_frame, text="Batch Processing")
        result_view = tk.Label(self.start_menu_frame, text="Result Viewer")

        # pad labels
        col0_pad = tk.Label(self.start_menu_frame, text="")
        col1_pad = tk.Label(self.start_menu_frame, text="")
        col2_pad = tk.Label(self.start_menu_frame, text="")
        col3_pad = tk.Label(self.start_menu_frame, text="")
        col4_pad = tk.Label(self.start_menu_frame, text="")

        row0_pad = tk.Label(self.start_menu_frame, text="")
        row1_pad = tk.Label(self.start_menu_frame, text="")
        row2_pad = tk.Label(self.start_menu_frame, text="")

        # var labels
        queue_label_var = tk.Label(self.start_menu_frame, textvariable=self.queue_var)
        running_label_var = tk.Label(self.start_menu_frame, textvariable=self.running_var)
        unprocessed_label_var = tk.Label(self.start_menu_frame, textvariable=self.unprocessed_var)
        complete_label_var = tk.Label(self.start_menu_frame, textvariable=self.completed_var)

        #buttons
        config_button = ttk.Button(self.start_menu_frame, text="Config", command=button_temp)
        new_batch_button = ttk.Button(self.start_menu_frame, text="New batch(es)", command=lambda: run_bayes_op(new_batch_tbox.get()))
        register_button = ttk.Button(self.start_menu_frame, text="Recover batch", command=batch_recovery)
        process_select_button = ttk.Button(self.start_menu_frame, text="Process select", command=select_batch_processing)
        process_all_button = ttk.Button(self.start_menu_frame, text="Process all", command=all_batch_processing)
        view_select_button = ttk.Button(self.start_menu_frame, text="View select", command=button_temp)
        view_all_button = ttk.Button(self.start_menu_frame, text="View all", command=view_all_excel)
        open_process_button = ttk.Button(self.start_menu_frame, text="Open Process File", command=button_temp)
        open_comp_button = ttk.Button(self.start_menu_frame, text="Open Comp File", command=view_comp_file)
        start_auto_button = ttk.Button(self.start_menu_frame, text="Auto", command=listening_thread)

        #text box
        new_batch_tbox = tk.Entry(self.start_menu_frame, width=2)

        #packing
        col0_pad.grid(row=1,column=0,padx=20)
        col1_pad.grid(row=1,column=1,padx=20)
        col2_pad.grid(row=1,column=2,padx=20)
        col3_pad.grid(row=1,column=3,padx=20)
        col4_pad.grid(row=1,column=4,padx=20)

        row0_pad.grid(row=6,column=0,pady=5)
        row1_pad.grid(row=10,column=0,pady=5)

        batch_gen_label.grid(row=1, column=1, sticky="")
        config_button.grid(row=1, column=4, rowspan=1,  sticky="")
        new_batch_tbox.grid(row=2, column=1, rowspan=1, sticky="w", padx=20)
        new_batch_button.grid(row=2, column=1, columnspan=2, sticky="")
        start_auto_button.grid(row=2, column=4, columnspan=2, sticky="")
        register_button.grid(row=3, column=1, columnspan=2, sticky="")
        queue_label_var.grid(row=4, column=1, rowspan=1, sticky="w")
        running_label_var.grid(row=5, column=1, rowspan=1,  sticky="w")

        batch_process_label.grid(row=7, column=1, rowspan=1, sticky="w")
        process_select_button.grid(row=8, column=1, rowspan=1,  sticky="w")
        process_all_button.grid(row=8, column=2, rowspan=1,  sticky="w")
        open_process_button.grid(row=8, column=3, rowspan=1,  sticky="w")
        unprocessed_label_var.grid(row=9, column=1, rowspan=1,  sticky="w")
        result_view.grid(row=11, column=1, rowspan=1,  sticky="w")
        view_select_button.grid(row=12, column=1, rowspan=1,  sticky="w")
        view_all_button.grid(row=12, column=2, rowspan=1,  sticky="w")
        open_comp_button.grid(row=12, column=3, rowspan=1,  sticky="w")
        complete_label_var.grid(row=13, column=1, rowspan=1, sticky="w")

        ## read and set label vars









        # view_all_label = tk.Label(self.start_menu_frame, text="View all by:")
        #
        # view_all_label.grid(row=3, column=1, rowspan=1, padx=0, sticky="ew")
        #
        # # buttons
        # process_new_batch_button = ttk.Button(self.start_menu_frame, text="Process new batch", command=data_processing)
        # view_by_access_button = ttk.Button(self.start_menu_frame, text="Access", command=view_by_access)
        # view_by_excel_button = ttk.Button(self.start_menu_frame, text="Excel", command=view_by_excel)
        #
        # process_new_batch_button.grid(row=2, column=3, rowspan=1, padx=0, sticky="ew")
        # view_by_access_button.grid(row=3, column=2, rowspan=1, padx=0, sticky="ew")
        # view_by_excel_button.grid(row=3, column=3, rowspan=1, padx=0, sticky="ew")


class ExcelView(tk.Frame):
    # self is own self, parent is container and controller is master
    '''For use with view_select
    To pick and choose which exps you want to view at one time'''

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.excelview_create_widgets()
        # self.update_label()

    def excelview_create_widgets(self):

        # Submit needs to start processing

        self.LHframe = tk.LabelFrame(self)
        self.RHframe = tk.LabelFrame(self)
        self.LHframe.grid(row=0, column=0, sticky="w", padx=10, rowspan=2)
        self.RHframe.grid(row=1, column=1, sticky="wn", padx=50)

        # Listbox - Options
        self.listbox_options = tk.Listbox(self.LHframe, width=60, height=40, borderwidth=2)
        self.listbox_options.grid(row=2, rowspan=2, column=0, padx=10)
        scrollbar_options = tk.Scrollbar(self.LHframe, orient="vertical")
        scrollbar_options.config(command=self.listbox_options.yview)
        self.listbox_options.config(yscrollcommand=scrollbar_options.set)
        scrollbar_options.grid(row=2, rowspan=2, column=0, sticky="ens")

        # Listbox - Selected
        self.listbox_selected = tk.Listbox(self.LHframe, width=60, height=40, borderwidth=2)
        self.listbox_selected.grid(row=2, rowspan=2, column=4, padx=10)
        scrollbar_selected = tk.Scrollbar(self.LHframe, orient="vertical")
        scrollbar_selected.config(command=self.listbox_selected.yview)
        self.listbox_selected.config(yscrollcommand=scrollbar_selected.set)
        scrollbar_selected.grid(row=2, rowspan=2, column=4, sticky="ens")

        # Labels
        select_directory_label = tk.Label(self.LHframe, text="Processed Batches")
        select_directory_label.grid(row=0, column=0, rowspan=2, padx=30, sticky="w")
        selected_label = tk.Label(self.LHframe, text="Selected Batches:")
        selected_label.grid(row=0, column=4, sticky="w", ipadx=10)

        # Buttons
        remove_choice_button = tk.Button(self.LHframe, text="<", command=listbox_remove_choice)
        remove_choice_button.grid(row=2, column=2, sticky="wes", ipadx=10)
        select_choice_button = tk.Button(self.LHframe, text=">", command=listbox_select_choice)
        select_choice_button.grid(row=2, column=3, sticky="wes", ipadx=10)
        remove_all_button = tk.Button(self.LHframe, text="<<", command=listbox_remove_all)
        remove_all_button.grid(row=3, column=2, sticky="wen", ipadx=10, pady=5)
        select_all_button = tk.Button(self.LHframe, text=">>", command=listbox_select_all)
        select_all_button.grid(row=3, column=3, sticky="wen", ipadx=10, pady=5)

        submit_nav_output = tk.Button(self.RHframe, text="View Selected",
                                      command=view_selected_batches)
        submit_nav_output.grid(sticky="es", row=6,
                               column=1,
                               ipadx=10)  # get(0, END) to get whole list, get(ACTIVE) for highlighted, delete(Active)

    def excelview_listbox_options_update(self, data):
        self.listbox_options.delete(0, "end")
        for i in data:
            self.listbox_options.insert("end", i)

    def excelview_listbox_selected_update(self, data):
        if data == 0:  # remove
            self.listbox_options.insert("end", self.listbox_selected.get("active"))
            self.listbox_selected.delete("active")
        if data == 1:  # add
            self.listbox_selected.insert("end", self.listbox_options.get(
                "active"))  # adds active to selected and removes from options
            self.listbox_options.delete("active")
        if data == 2:  # remove all
            list = self.listbox_selected.get(0, "end")
            self.listbox_selected.delete(0, "end")
            for i in list:
                self.listbox_options.insert("end", i)
            self.listbox_selected.delete(0, "end")
        if data == 3:  # add all
            list = self.listbox_options.get(0, "end")
            self.listbox_options.delete(0, "end")
            for i in list:
                self.listbox_selected.insert("end", i)

    def excelview_return_parameters(self):
        if self.listbox_selected.get(0) == "":
            return "Error - Please select files to process"
        '''
        .get() returns int value for state, 0 = unselected, if total = 0 then nothing selected, throw error
        '''
        s_list = self.listbox_selected.get(0, "end")  # selected list
        return s_list


class Output(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

    def output_update(self, data):
        '''
        Checks saving directory,
        Generates output filename,
        reads in CSV,
        process data to get avg, 2sd and gas mol,
        adds this data to dataframe,
        moves to next csv; iterates through all in batch,
        output to single CSV
        '''

        # Generates output file using template
        global template_filename, template_dir, output_dir, filetype
        print(data[2])
        self.output_filename = (data[2]) + "_" + str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        # batch_id + yyyy-mm-dd_HH-MM-SS

        global headspace_volume, molar_vol_gas, every_nth_file
        nth_counter = 1
        processed_output_dict = {}
        for i in data[0]:
            i2 = (i.split("_"))[2]  # takes file name, splits for FormulationIdxxxxxx
            if nth_counter != every_nth_file:  # skips through scans until desired is reached
                nth_counter += 1
                continue
            nth_counter = 1  # resets counter as desired has been reached
            form_datetime = i.split("_")[3]  # takes the datetime from formulation filename
            form_datetime = form_datetime.split(".")[0:2]  # cuts off .csv extension
            form_datetime = "20" + form_datetime[0] + form_datetime[1]
            # adds 20 to start of date to give date format e.g 20200314
            if processed_output_dict == {}:  # If nothing in dict, first should be an n2_sample
                pass
                # processed_output_dict.setdefault("N2_samp", []).append((True))

            elif i2.split("Id")[1] not in processed_output_dict["form_id"]:
                # processed_output_dict.setdefault("N2_samp", []).append((True))
                '''If nothing in dict, add this first formID as add. sampling
                If this formID not in dict, mark this as the add. sampling (As this occurs first, 
                if the list is ordered then this should be the first entering the dict)'''

            else:
                pass
                # processed_output_dict.setdefault("N2_samp", []).append((False))

            processed_output_dict.setdefault("form_id", []).append((i2.split("Id"))[1])  # takes the xxxxxxx from formID
            processed_output_dict.setdefault("form_datetime", []).append(form_datetime)
            to_skip = list(range(0, 32)) + [33, 34]  # reads to line 33 in csv (headers), then skips first 2 scans
            current_file_df = pd.read_csv((data[1] + "/" + i), skiprows=to_skip)
            # Reads the formatted output sheet into a dataframe
            current_file_df = current_file_df.dropna(1)
            # removes empty space / NaNs to the right
            current_file_df.rename_axis()

            for col in current_file_df.columns:
                if "%" in col or "Baratron" in col:
                    processed_output_dict.setdefault(("{} Avg").format(col), []).append(
                        current_file_df[("{}").format(col)].mean())

                    processed_output_dict.setdefault(("{} 2STD").format(col), []).append(
                        current_file_df[("{}").format(col)].std() * 2)
                if col == "% H2" or col == "% O2":
                    # if "H2" in col or "O2" in col:
                    avg_gas_per = current_file_df[("{}").format(col)].mean()  # per = %
                    avg_gas_vol_mL = avg_gas_per * headspace_volume
                    if avg_gas_vol_mL == 0:  # incase no desired gas in vial
                        avg_gas_umol = 0
                    else:
                        avg_gas_umol = ((avg_gas_vol_mL / 1000) / molar_vol_gas) * 10 ** 6
                    # Finds gas mol, flips and divides for umol

                    processed_output_dict.setdefault("{} umol".format(col), []).append(avg_gas_umol)

        processed_output_df = pd.DataFrame.from_dict(data=processed_output_dict)
        # Converts the dictionary to a Pandas Dataframe

        processed_output_df["form_id"] = pd.to_numeric(processed_output_df["form_id"])
        processed_output_df["form_datetime"] = pd.to_datetime(processed_output_df["form_datetime"],
                                                              format="%Y%m%d%H%M%S")

        processed_output_df.set_index("form_id", inplace=True)
        self.processed_output_df = processed_output_df

        Output.output_csv_processing(self)

        #self.output_create_widgets()
        #app.show_frame(Output)
        print("Processing Complete")

    def output_csv_processing(self):
        global template_filename, template_dir, output_dir, filetype

        self.processed_output_df.to_csv(output_dir + self.output_filename + ".csv")
        print(str(len(self.processed_output_df.index)) + " files processed")
        print(self.output_filename + " complete")


def label_update():
    app.update_frame(cont=StartMenu, arg=1)
    #arg is the frame switch



def select_batch_processing():
    global default_batch_loc
    dirname = filedialog.askdirectory(initialdir=default_batch_loc, title="Select batch to process")

    batch_processing(dirname)


    #app.update_frame(cont=Output, data_type="data_processing", data=r_list)
def all_batch_processing():
    global unprocessed_batch_dir
    #dirlist = [f for f in os.listdir(default_batch_loc) if isfile(join(default_batch_loc, f))]
    #dirlist = os.walk(default_batch_loc)
    dirlist = glob.glob(unprocessed_batch_dir + "/*")
    # for i in dirlist:
    #     i = i.split("/")[-1]
    #     i = i.split("\\")[-1]
    #     print(i)
    for i in dirlist:
        dirname = i
        batch_processing(dirname)
    '''
    Hopefully this doesn't get stuck looping too long, should help to do one exp at a time to reduce impact of errors
    '''

def listening_thread():
    t1 = listen_thread()
    t1.start()




def batch_processing(dirname):
    # app.update_frame(cont=StartMenu, data_type="label_update", data=dirname)
    #''' Cont = desired page, inputType= will be label, listbox, etc; input= filename/dir'''

    try:
        dir_contents = [f for f in os.listdir(dirname) if isfile(join(dirname, f))]
        dirname = os.path.normpath(dirname)
        batch_id = (dirname.split("\\"))[-1]
        print("Processing: {}".format(batch_id))

        r_list = dir_contents, dirname, batch_id
        # sends dir and files names to be processed - should go through all csvs in file. - returns df that will need collating with HOLLY
        check = holly_webscraper.holly_complete_check(batch_id)
        processed_output_df = batch_processor.batch_processor(bp_params, r_list)
        processed_output_df.sort_index(axis=0, inplace=True)

       #starts catch loop as web scraping most likely to give errors
        while True:
            try:
                #batch_id -> expNum
                dispense_df = holly_webscraper.holly_webscaper(batch_id)
                collated_df = pd.concat([dispense_df, processed_output_df], axis=1)
                collated_df.reindex()
                #post batch file handling - moves unprocessed hiden csv to processed folder
                collated_df.to_csv(optimiser_dir+"temp_completed/{}.csv".format(batch_id))
                print("File collated and dumped")
                shutil.move(dirname, processed_batch_dir + "\\" + str(batch_id))
                label_update()

                break
            except Exception as e:
                print(e)
                while True:
                    print("Scraping Error - try again? Y/N")
                    x = input().upper().strip()
                    if x =="Y" or x == "N":
                        break
                    else:
                        print("Invalid response")
                if x == "Y":
                    continue
                if x =="N":
                    print("Process stopped")
                    break
    except:
        print("File selection closed by user")

def batch_recovery():
    '''
    User needs to pick the hiden data exp (from unproccessed dir) and provide the HOLLY dispense exp
    Largely the same as batch processing but does not pass Exp# from HIDEN to HOLLY
    Not joined by primary key as =/=
    Joined by time/date sort of holly results and plate#vial# of hiden
    ONLY WORKS IF PLATES USED IN ACSENDING ORDER ie 1 to 4
    '''
    global default_batch_loc
    dirname = filedialog.askdirectory(initialdir=default_batch_loc, title="Hiden batch to recover")
    dir_contents = [f for f in os.listdir(dirname) if isfile(join(dirname, f))]
    dirname = os.path.normpath(dirname)
    holly_exp = input("Enter HOLLY Exp# (eg 685) \n")
    batch_id = (dirname.split("\\"))[-1]
    print("Processing: {}".format(batch_id))

    r_list = dir_contents, dirname, batch_id
    # sends dir and files names to be processed - should go through all csvs in file. - returns df that will need collating with HOLLY
    processed_output_df = batch_processor.batch_processor(bp_params, r_list)
    processed_output_df.reset_index(inplace=True)
    processed_output_df.drop(columns="form_id", axis=1, inplace=True)
    processed_output_df.set_index("sample_name", inplace=True)
    processed_output_df = processed_output_df.reindex(index=natsorted(processed_output_df.index)) # quick way to sort AN strings so A2 comes before A11
    processed_output_df.reset_index(inplace=True)

    dispense_df = holly_webscraper.holly_webscaper(holly_exp)
    dispense_df.reset_index(inplace=True)

    '''
    Both dispense and hiden dataframes made using semi-normal process
    Primary keys (form_id) removed, hiden data must be named as such that it gives correct order to form_id
    ie if plates are only ever used in ascending order then ag1 to ag4 will work
    hiden data sorted to plate name - vial num and bolted onto dispense data
    '''


    #collated_df = pd.concat([dispense_df, processed_output_df], axis=1)
    collated_df = pd.merge(dispense_df, processed_output_df, left_index=True, right_index=True, how="outer")
    collated_df.set_index("form_id", inplace=True)
    #print(collated_df)
    # post batch file handling - moves unprocessed hiden csv to processed folder
    collated_df.to_csv(optimiser_dir + "temp_completed/{}.csv".format(batch_id))
    print("File collated and dumped")
    #shutil.move(dirname, processed_batch_dir + "\\" + str(batch_id))
    label_update()




def button_temp():
    print("not implemented")

def listbox_remove_choice():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=0)


def listbox_select_choice():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=1)


def listbox_remove_all():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=2)


def listbox_select_all():
    app.update_frame(cont=ExcelView, data_type="listbox_selected_update", data=3)


def view_by_excel():
    global output_dir
    dir_contents = [f for f in os.listdir(output_dir) if isfile(join(output_dir, f)) and f.split(".")[1] == "csv"]
    # checks if isfile and isCSV == true
    app.update_frame(cont=ExcelView, data_type="listbox_option_update", data=dir_contents)
    app.show_frame(ExcelView)

def view_all_excel():
    dir_contents = [f for f in os.listdir(optimiser_dir+"completed/") if isfile(join(optimiser_dir+"completed/", f))]
    csv_list = []
    for f in dir_contents:
        df = pd.read_csv(optimiser_dir+"completed/"+f, index_col="form_id", header=0)
        csv_list.append(df)
    csv_df = pd.concat(csv_list, axis=0, ignore_index=False)
    csv_df.to_csv(view_dump + "/{}.csv".format("temp"))
def view_comp_file():
    os.startfile(optimiser_dir+"completed/")

def view_selected_batches():
    global output_dir
    return_batches = app.update_frame(cont=ExcelView, data_type="return_parameters")
    li = []
    for filename in return_batches:
        df = pd.read_csv(output_dir + filename, index_col=None, header=0)
        li.append(df)
    all_batches_df = pd.concat(li, axis=1, ignore_index=True)

    wb = xw.Book()
    sheet = wb.sheets["Sheet1"]
    sheet.range("A1").value = all_batches_df

def run_bayes_op(xbatches):
    '''
    runs bayes op - didn't incorp to main as I didn't make it (also it has a license?)
    '''
    if not xbatches == "":
        xbatches = int(xbatches)
        if xbatches > 0:
            os.chdir(optimiser_dir)
            os.system("py experiment.py {}".format(xbatches))
            label_update()
        else:
            print("Error: batch# invalid")
    else:
        print("Error: batch# blank")

# Maintains tkinter interface
app = Application(master=tk.Tk())
app.mainloop()
