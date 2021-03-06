from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pandas.errors import ParserError
from pandastable import Table, TableModel

import matplotlib
import matplotlib.pyplot as plt
import math
import mysql.connector
import os.path
import pandas as pd
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as tkMessageBox
import tkinter.filedialog as tkFileDialog


matplotlib.use("TkAgg")


class DataStore(object):
    host = "localhost"
    user = "root"
    passwd = "2ZombiesEatBrains?"
    data = pd.DataFrame()


class Application (tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        DataStore.data = get_db_data()

        self.fonts = {
            "title": tkfont.Font(family="Lucida Grande", size=24)
        }

        self.tabs = [
            DataFrame,
            StatsFrame
        ]
        self.create_widgets()
        self.set_tab(0)

    def create_widgets(self):
        self.rowconfigure(index=2, weight=1)
        self.columnconfigure(index=0, weight=1)

        # Create title Widget
        self.title_label = tk.Label(
            self, text="DataVault Inc.", font=self.fonts["title"], justify="left", bg="#f0f0f0")
        self.title_label.grid(row=0, column=0, ipady=8,
                              ipadx=12, sticky="NSEW")

        # Create view selection widgets, i.e. tab buttons
        if len(self.tabs) > 1:
            self.subheader_frame = tk.Frame(self, bg="#f0f0f0")
            self.subheader_frame.grid(
                row=1, column=0, ipady="8", sticky="NSEW")

            # Set subheader_frame to have 8 columns.
            for col in range(12):
                self.subheader_frame.columnconfigure(index=col, weight=1)

        # Create container for actual tabs.
        self.tab_container = tk.Frame(self, bg="#fff")
        self.tab_container.grid(row=2, column=0, sticky="NSEW")
        # Set tab_container 0 index row & column to weight of 1
        self.tab_container.rowconfigure(index=0, weight=1)
        self.tab_container.columnconfigure(index=0, weight=1)

        self.tab_buttons = []
        for idx, tab in enumerate(self.tabs):
            if len(self.tabs) > 1:
                # Create tab buttons
                t = tk.Button(self.subheader_frame, text=tab.label, relief="ridge",
                              command=lambda index=idx: self.set_tab(index))

                self.tab_buttons.append(t)
                self.tab_buttons[idx].grid(ipadx=10, ipady=5, sticky="NSEW",
                                           row=0, column=(6 - math.floor(len(self.tabs) / 2) + idx),
                                           columnspan=(len(self.tabs) % 2 + 1))

            # Create tab frames
            self.tabs[idx] = tab(master=self.tab_container)
            self.tabs[idx].grid(row=0, column=0, sticky="NSEW")

    def set_tab(self, frame_idx):
        for idx, _ in enumerate(self.tab_buttons):
            if idx == frame_idx:
                self.tab_buttons[idx]["state"] = "disabled"
                self.tabs[idx].show()
            else:
                self.tab_buttons[idx]["state"] = "normal"


class DataFrame(tk.Frame):
    label = "View Data"

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.columnconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=1)

        self.create_widgets()

    def show(self):
        self.tkraise()

    def create_widgets(self):
        # Create buttons to manage the DB.
        self.toolbar = tk.Frame(self)
        self.toolbar.grid(row=0, column=0, padx=12, pady=3, sticky="NSEW")
        for col in range(12):
            self.toolbar.columnconfigure(index=col, weight=1)

        self.save_button = tk.Button(
            self.toolbar, text="Save Data To DB", command=self.save_to_db)
        self.export_button = tk.Button(
            self.toolbar, text="Export Data to File", command=self.export_data)
        self.import_button = tk.Button(
            self.toolbar, text="Import Data from CSV", command=self.import_csv)
        self.refresh_button = tk.Button(
            self.toolbar, text="Refresh Data from DB", command=self.refresh_table_data)

        self.save_button.grid(row=0, column=12)
        self.export_button.grid(row=0, column=11)
        self.import_button.grid(row=0, column=10)
        self.refresh_button.grid(row=0, column=9)

        self.table_container = tk.Frame(self)
        self.table_container.grid(row=1, column=0, sticky="NSEW")
        # Create table to display data
        data_df = DataStore.data

        self.data_table = Table(self.table_container, dataframe=data_df)
        self.data_table.autoResizeColumns()
        self.data_table.show()

    def refresh_table_data(self):
        res = tkMessageBox.askyesno(title="Are you sure you want to refresh the DB.",
                                    message="Are you sure that you want to refresh the DB.\n"
                                    "This will undo any changes that you made before saving your data. This includes CSV file that you have imported")

        if res == tkMessageBox.NO:
            return

        data_df = get_db_data()

        DataStore.data = data_df
        self.data_table.updateModel(TableModel(data_df))
        self.data_table.redraw()

    def export_data(self):
        output_file = tkFileDialog.askopenfilename()
        if not output_file:
            tkMessageBox.showerror(title="Export Failed",
                                   message="Export failed as no file was selected.")
            return

    def save_to_db(self):
        add_df_to_db(DataStore.data)

    def import_csv(self):
        # Get file to import
        input_file = tkFileDialog.askopenfilename()
        if not input_file.strip():
            tkMessageBox.showerror(title="Import Failed",
                                   message="Import failed as no file was selected.")
            return

        try:
            import_df = pd.read_csv(input_file)
        except ParserError:
            tkMessageBox.showerror(
                "The supplied file is not a valid CSV file, could not import.")

        if len(import_df) > 0:
            # Data was loaded.
            DataStore.data.reset_index(level=["id_product"], inplace=True)
            table_df = DataStore.data.append(import_df, ignore_index=False)
            table_df.set_index("id_product", inplace=True)

            DataStore.data = table_df
            self.data_table.updateModel(TableModel(table_df))
            self.data_table.redraw()

            tkMessageBox.showinfo(title="Import Successful",
                                  message="Import Completed Successfully!")
        else:
            tkMessageBox.showinfo(title="Import Failed",
                                  message="Input file did not have any CSV data so no data was added.")


class StatsFrame(tk.Frame):
    label = "View Stats"

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.rowconfigure(index=0, weight=1)
        self.columnconfigure(index=0, weight=1)

        f = self.get_plot_data()
        self.plt_show(f)

    def show(self):
        f = self.get_plot_data()
        self.plt_show(f)

        self.tkraise()

    def plt_show(self, f):
        """Method to add the matplotlib graph onto a tkinter window."""
        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()

        for ax in f.get_axes():
            for tick in ax.get_xticklabels():
                tick.set_rotation(35)

        self.plot_widget = canvas.get_tk_widget()
        self.plot_widget.grid(row=0, column=0, sticky="NSEW")

    def get_plot_data(self):
        # Get a data from DB and import into pandas.DataFrame
        # DataStore.data = get_db_data()
        products_df = DataStore.data

        # Create the matplotlib figure and axes that will be used to display the graphs for the statistics.
        fig = Figure(figsize=(15, 5), dpi=100)

        ax1 = fig.add_subplot(1, 3, 1)
        ax2 = fig.add_subplot(1, 3, 2)
        ax3 = fig.add_subplot(1, 3, 3)

        fig.subplots_adjust(bottom=.25)

        # Create different statistics and plot them the figure previously defined.
        products_df.groupby(["category"]).size().plot(ax=ax1, y="stock_available", kind="bar", grid=True,
                                                      title="Number of Items per Category")
        products_df.groupby(["category"]).sum().plot(ax=ax2, y="stock_available", kind="bar", grid=True,
                                                     title="Total Number of Products per Category")
        products_df.groupby(["category"]).mean().plot(ax=ax3, y="stock_available", kind="bar", grid=True,
                                                      title="Average Price of Products in Category")

        return fig


def get_db_data():
    """ Method to get the data from the database and return it as a tuple consisting
    of a list of the names of the columns and a list of the actualy data in tuple format."""
    con = mysql.connector.connect(host=DataStore.host, user=DataStore.user,
                          passwd=DataStore.passwd, database="sprint_datavault")
    cursor = con.cursor()

    cols = [
        "id_product", "name", "category", "stock_available", "selling_price"
    ]

    # Create the table if it doesn't already exist. This will allow it to work in any DB.
    cursor.execute("""CREATE TABLE IF NOT EXISTS `products` (
        id_product VARCHAR(12) NOT NULL PRIMARY KEY,
        name VARCHAR(60) NOT NULL,
        category VARCHAR(60) NOT NULL,
        stock_available INT UNSIGNED NOT NULL DEFAULT 0,
        selling_price DECIMAL(13,2) UNSIGNED NOT NULL DEFAULT 0.00
    ) ENGINE=InnoDB""")

    cursor.execute(
        f"SELECT {','.join(cols)} FROM products")
    data = cursor.fetchall()
    con.close()

    data_df = pd.DataFrame(data, columns=cols).set_index(
        "id_product")
    return data_df


def add_df_to_db(df):
    con = mysql.connector.connect(host=DataStore.host, user=DataStore.user,
                          passwd=DataStore.passwd, database="sprint_datavault")
    cursor = con.cursor()

    # Firstly, get original dataframe, using get_db_data()
    left_df = get_db_data()

    df = df.reset_index(level=["id_product"])
    left_df = left_df.reset_index(level=["id_product"])

    # Then, compare the the two and only take the ones that have differences
    out_df = left_df.merge(df, how="outer", indicator="shared")
    out_df = out_df[out_df["shared"] != "both"]

    out_df.drop(["shared"], axis=1, inplace=True)
    # out_df.reset_index(level=0, inplace=True)

    if len(out_df) == 0:
        tkMessageBox.showinfo(title="DataBase Update Complete",
                              message="Nothing was added to the DB as no changes were detected between the different datasets.")
        return

    cols = "`,`".join([str(i) for i in out_df.columns.tolist()])
    # for _, row in out_df.iterrows():
    sql = "INSERT INTO `products` (`" + cols + \
        "`) VALUES (" + "%s," * (len(out_df.columns)-1) + "%s)"

    # try:
    print(out_df)
    sql_data = []
    for _, row in out_df.iterrows():
        print(list(row))
        sql_data.append(tuple(row))

    cursor.executemany(sql, tuple(sql_data))
    con.commit()
    tkMessageBox.showinfo(title="Save Successful",
                          message="Save Completed Successfully!")
    # except:
    #     con.rollback()
    #     tkMessageBox.showerror(title="Save Failed",
    #                             message="The data was not saved to the DB.")

    con.close()


app = Application()
app.mainloop()
