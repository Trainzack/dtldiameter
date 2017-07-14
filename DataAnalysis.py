# DataAnalysis.py
# Written by Eli Zupke, June 2017
# This file takes csv files and turns them into graphs. It's not that well written. Abandon 85% of hope, all ye who
# enter here.


import csv
import numpy
import matplotlib.pyplot as plt
import os
import optparse

def displayListValues(list, name):
    print name + ": "
    if not isinstance(list[0],(int, float)):
        print "(Not Number)"
    else:
        print "\tMin:\t{0}".format(min(list))
        print "\tMax:\t{0}".format(max(list))
        print "\tMedian:\t{0}".format(numpy.median(list))
        print "\tMean:\t{0}".format(numpy.mean(list))
        print ""

def read_file(csv_file, mpr_strip=0, mpr_equals_median_strip=False):

    properties = {}
    column = {}
    ignore_mprs = []
    if mpr_strip > 0:
        ignore_mprs = map(str, range(0, mpr_strip))

    with open(csv_file) as file:
        reader = csv.reader(file)
        header = reader.next()

        MPR_count_column = 0
        median_count_column = 0

        # Get the index of each property to allow us to search that row.
        for i, element in enumerate(header):
            properties[element] = []
            column[i] = element
            if element == "MPR Count":
                MPR_count_column = i
            elif element == "Median Count":
                median_count_column = i

        for row in reader:

            if row[MPR_count_column] not in ignore_mprs and (not mpr_equals_median_strip or row[MPR_count_column] !=
                                                             row[median_count_column]):
                for i, property in enumerate(row):
                    properties[column[i]] += [property]

    length = len(properties[column[0]])
    name_to_row = {v: k for k, v in column.iteritems()}
    return properties, length, name_to_row

def set_label(axis, label, letter, latex):
    if latex:
        axis.set_xlabel(label+"\n"r"{\fontsize{30pt}{3em}\selectfont{}("+letter+")}", linespacing=2.5,
                                 labelpad=20)
    else:
        axis.set_xlabel(label)

def make_plot(file, y_limits, non_normalized, timings, gene_count_list, diameter_list, diameter_name,
              normalized_diameter, normalized_diameter_name, mpr_list, DP_timings,
              diameter_timings, total_timings, name, latex):
    size = 4
    color = 'black'
    y_range = float(y_limits[1] - y_limits[0])
    y_padding = y_range * 0.05
    diameter_ylim_b = y_limits[0] - y_padding
    diameter_ylim_t = y_limits[1] + y_padding

    gene_xlim = max(gene_count_list) * 1.05

    if non_normalized:

        log_y = False
        y_max = max(diameter_list)
        y_min = min(diameter_list)
        if log_y:
            log_y_min = numpy.floor(numpy.log10(y_min)) - 1
        padding = (y_max - y_min) * 0.05
        y_bottom = y_min - padding
        y_top = y_max + padding
        fig, ax = plt.subplots(ncols=3, nrows=1)
        fig.canvas.set_window_title("{0} Plots {1}".format(file, name))

        diameter = ax[1]
        diameter_hist = ax[0]
        mpr_diameter = ax[2]
        ax[0].set_ylabel(diameter_name)

        diameter.scatter(gene_count_list, diameter_list, c=color, s=size)
        set_label(diameter, "Gene Tree Size", "b", latex)
        diameter.set_xlim(0, gene_xlim)
        diameter.set_title("{0} vs. Gene Count".format(diameter_name))
        diameter.set_ylim(y_bottom, y_top)

        bins = 100
        if log_y:
            bins = numpy.logspace(log_y_min, numpy.log10(y_top), bins)
        diameter_hist.hist(diameter_list, orientation='horizontal', bins=bins)
        # diameter_hist.set_ylabel("Diameter")
        set_label(diameter_hist, "Number of Gene Families", "a", latex)
        diameter_hist.set_title(diameter_name)

        mpr_diameter.scatter(mpr_list, diameter_list, c=color, s=size)
        set_label(mpr_diameter, "MPR Count", "c", latex)
        mpr_diameter.set_title("{0} vs. MPR Count".format(diameter_name))
        mpr_diameter.set_xscale('log')
        mpr_diameter.set_ylim(y_bottom, y_top)

        for a in ax:
            if log_y:
                a.set_yscale('log')
            a.grid()

    fig, ax = plt.subplots(ncols=2, nrows=1)
    fig.canvas.set_window_title("{0} Normalized Plots {1}".format(file, name))
    norm_diameter_hist = ax[0]
    norm_mpr_diameter = ax[2]
    norm_diameter = ax[1]
    ax[0].set_ylabel(normalized_diameter_name)

    norm_diameter.scatter(gene_count_list, normalized_diameter, c=color, s=size)
    set_label(norm_diameter, "Gene Tree Size", "b", latex)
    norm_diameter.set_xlim(0, gene_xlim)
    # norm_diameter.set_ylabel("Diameter (normalized to gene node count)")
    norm_diameter.set_ylim(diameter_ylim_b, diameter_ylim_t)
    norm_diameter.set_title("{0} vs. Gene Tree Size".format(normalized_diameter_name))
    norm_diameter.grid()

    norm_diameter_hist.grid()
    norm_diameter_hist.hist(normalized_diameter, 100, orientation='horizontal')
    # norm_diameter_hist.set_ylabel("Diameter (normalized to gene node count)")
    set_label(norm_diameter_hist, "Number of Gene Families", "a", latex)
    norm_diameter_hist.set_title("{0} Counts".format(normalized_diameter_name))
    norm_diameter_hist.set_ylim(diameter_ylim_b, diameter_ylim_t)

    norm_mpr_diameter.scatter(mpr_list, normalized_diameter, c=color, s=size)
    norm_mpr_diameter.set_ylim(diameter_ylim_b, diameter_ylim_t)
    set_label(norm_mpr_diameter, "MPR Count", "c", latex)
    norm_mpr_diameter.set_title("{0} vs. MPR Count".format(normalized_diameter_name))
    norm_mpr_diameter.grid()
    norm_mpr_diameter.set_xscale('log')

    # plt.show()
    # return
    if timings:
        fig, ax = plt.subplots(ncols=3, nrows=1)
        fig.canvas.set_window_title("{0} Running Times {1}".format(file, name))
        DP_time = ax[0]
        diameter_time = ax[1]
        total_time = ax[2]
        DP_time.scatter(gene_count_list, DP_timings, c=color, s=size)
        set_label(DP_time, "Gene Tree Size", "a", latex)
        DP_time.set_ylabel("Time (seconds)")
        DP_time.set_title("Computing Reconciliation Graph")
        DP_time.grid()
        DP_time.set_yscale('log')
        DP_time.set_xscale('log')
        diameter_time.scatter(gene_count_list, diameter_timings, c=color, s=size)
        set_label(diameter_time, "Gene Tree Size", "b", latex)
        diameter_time.set_ylabel("Time (seconds)")
        diameter_time.set_title("Computing {0}".format(diameter_name))
        diameter_time.grid()
        diameter_time.set_yscale('log')
        diameter_time.set_ylim(0.001,10**4)
        diameter_time.set_xscale('log')
        total_time.scatter(gene_count_list, total_timings, c=color, s=size)
        set_label(total_time, "Gene Tree Size", "c", latex)
        total_time.set_ylabel("Time (seconds)")
        total_time.set_title("Total Running Time")
        total_time.grid()
        total_time.set_yscale('log')
        total_time.set_xscale('log')


def analyse_data(csv_file, given_properties, non_normalized, timings, plot, latex, strip_mprs, strip_equal):
    """
    This function analyses a provided csv_file of data returned from RunTests.py. The analysis will include a list of
     the mins, maxes, medians, and modes of several specified properties, and might also include plots.
    :param csv_file:        The logfile we will be analysing
    :param given_properties:      A list containing strings, each one being the name of a column in the csv file that we want
                             to inspect (or plot). All properties must have associated timing data (named as
                             '[prop_name] Computation Time'.
    :param non_normalized:  A boolean value representing whether we also want to include plots that are not normalized
                             in some way.
    :param timings:         A boolean value representing whether we also want to include plots of the associated timing
                             data.
    :param plot:            A boolean value representing whether we want to include any plots at all.
    :param latex:           A boolean value representing whether we want to use LaTeX for typsetting (and also include
                             figure numbers ((a), (b), (c)) under the plots.
    :param strip_mprs:      A number representing a number of MPRs which is the lower limit of families we will include
                             in our analysis
    :param strip_equal:     A boolean value representing whether we want to include families in which every
                             reconciliation is a median
    """

    if plot:
        plt.rc('text', usetex=latex)
        if latex:
            plt.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
            plt.rcParams['text.latex.preamble'] = [r"\usepackage{amsmath}"]

    mpr_list = []

    diameter_present = False
    zero_loss_present = False

    properties_that_exist_in_file, length, _ = read_file(csv_file, strip_mprs, strip_equal)


    for prop in given_properties:
        assert prop in properties_that_exist_in_file, "Property '{0}' passed to analyse_data was not found in log file '{1}'!".format(prop, csv_file)
        assert prop + " Computation Time" in properties_that_exist_in_file or not timings, \
            "Property '{0}' passed to analyse_data did not have associated " \
            "timing information in log file '{1}'!".format(prop, csv_file)
    for prop in ["Costs", "MPR Count", "Gene Node Count", "Species Node Count", "DTLReconGraph Computation Time"]:
        assert prop in properties_that_exist_in_file, "Required property '{0}' was not found in log file '{1}'!".format(prop, csv_file)

    DTL = properties_that_exist_in_file["Costs"][0]
    mpr_list = properties_that_exist_in_file["MPR Count"]
    mpr_list = map(lambda e: float(e), mpr_list)
    gene_count_list = properties_that_exist_in_file["Gene Node Count"]
    gene_count_list= map(lambda e: float(e), gene_count_list)
    species_count_list = properties_that_exist_in_file["Species Node Count"]
    species_count_list = map(lambda e: float(e), species_count_list)
    DP_timings = properties_that_exist_in_file["DTLReconGraph Computation Time"]
    DP_timings = map(lambda e: float(e), DP_timings)
    prop_list_dict = {}
    timing_list_dict = {}

    for property in given_properties:
        prop_list_dict[property] = properties_that_exist_in_file[property]
        # This is kind of janky. We only turn properties with these names into floats
        if "Diameter" in property or "Count" in property or "Number" in property:
            prop_list_dict[property] = map(lambda e: float(e), prop_list_dict[property])
            if timings:
                timing_list_dict[property + " Computation Time"] = properties_that_exist_in_file[property + " Computation Time"]

    # We assign to the total timings variable even if we are not using timings, because other functions
    # want it, even if they are unused.
    total_timings = DP_timings[:]
    if timings:
        for timing_list in timing_list_dict:
            timing_list_dict[timing_list] = map(lambda e: float(e), timing_list_dict[timing_list])
            cur_list = timing_list_dict[timing_list]
            for i, time in enumerate(cur_list):
                total_timings[i] += time


    displayListValues(mpr_list, "MPR Count")
    displayListValues(gene_count_list, "Gene Tree Size")
    displayListValues(gene_count_list, "Species Tree Size")
    #displayListValues(mpr_over_d_list, "MPR Count/Diameter")
    #displayListValues(mpr_over_normalized_d_list, "MPR Count/(Diameter/Gene Count)")
    if timings:
        displayListValues(DP_timings, "Reconciliation Running Time (seconds)")
        displayListValues(total_timings, "Total Running Time (seconds)")

    for property_list in prop_list_dict:
        displayListValues(prop_list_dict[property_list], property_list)

    filepath, extension = os.path.splitext(csv_file)
    if plot:

        name_postfix = ""
        if strip_mprs == 2:
            name_postfix += " >1 MPR"
        elif strip_mprs > 2:
            name_postfix += " >{0} MPRs".format(strip_mprs - 1)

        if strip_equal:
            name_postfix += " MPR != Median"

        # plot_info_list is a list of tuples with the format ("NAME", normalizing_list, "Normalized Name", (bottom_lim,
        # top_lim), data_list). data_list is the list of values we are plotting, and normalizing_list is the list of
        # values we will normalize against.

        # To make a property something that we try to plot if possible, add another if statement here.

        plot_info_list = []

        # check to see if something we reocognize is in
        if "Diameter" in prop_list_dict:
            data_list = prop_list_dict["Diameter"]
            plot_info_list += [("Diameter", gene_count_list, "Normalized Diameter", (0,2), data_list)]

        if "Zero Loss Diameter" in prop_list_dict:
            data_list = prop_list_dict["Zero Loss Diameter"]
            plot_info_list += [("Zero Loss Diameter", gene_count_list, "Normalized Zero Loss Diameter", (0,1), data_list)]

        if "Median Count" in prop_list_dict:
            data_list = prop_list_dict["Median Count"]
            plot_info_list += [("Median Count", mpr_list, "Normalized Median Count", (0,1), data_list)]

        if "Worst Median Diameter" in prop_list_dict:
            data_list = prop_list_dict["Worst Median Diameter"]
            plot_info_list += [("Worst Median Diameter", gene_count_list, "Normalized Worst Median Diameter", (0,2), data_list)]

        if "Random Median Average Diameter" in prop_list_dict:
            data_list = prop_list_dict["Random Median Average Diameter"]
            plot_info_list += [("Random Median Average Diameter", prop_list_dict["Diameter"], "Average Normalized Median Distance", (0.5,1), data_list)]

        if "Random Median Diameter Standard Deviation" in prop_list_dict:
            data_list = prop_list_dict["Random Median Diameter Standard Deviation"]
            plot_info_list += [("Random Median Diameter Standard Deviation", [1] * len(prop_list_dict["Diameter"]), "Random Median Diameter Standard Deviation", (0,4), data_list)]


        for prop in plot_info_list:
            prop_name = prop[0]
            prop_normalized_against = prop[1]
            normalized_prop_name = prop[2]
            y_limits = prop[3]
            prop_data = prop[4]
            prop_normalized = map(lambda i: prop_data[i[0]] / prop_normalized_against[i[0]],
                             enumerate(prop_data))
            if timings:
                timing_data = timing_list_dict[prop_name + " Computation Time"]
            else:
                timing_data = data_list
            make_plot(csv_file, y_limits, non_normalized, timings, gene_count_list, data_list,
                      prop_name, prop_normalized, normalized_prop_name, mpr_list, DP_timings,
                      timing_data, total_timings, prop_name + " " + name_postfix, latex)


def find_specific(csv_file="COG_Median_13.csv"):
    file_props, length, column_lookup = read_file(csv_file, False, False)

    mprs_1 = 0
    mprs_2 = 0
    mprs_gt_2 = 0
    mprs_gt_2_not = 0
    mprs_gt_2_eq = 0
    mpr_eq_med = 0
    mpr_not_med = 0
    mpr_lt = [0]*13
    mpr_gt = 0

    for i in range(0, length):
        mpr_count = file_props["MPR Count"][i]
        median = file_props["Median Count"][i]
        if mpr_count == "1":
            mprs_1 += 1
        elif mpr_count == "2":
            mprs_2 += 1
        else:
            mprs_gt_2 += 1
            if mpr_count == median:
                mprs_gt_2_not += 1
            else:
                mprs_gt_2_eq += 1
        if mpr_count == median:
            mpr_eq_med += 1
        else:
            mpr_not_med += 1


    print "{0} families observed.".format(length)
    print "MPR count == 1: {0}".format(mprs_1)
    print "MPR count == 2: {0}".format(mprs_2)
    print "MPR count > 2: {0}".format(mprs_gt_2)
    print "MPR == median count: {0}".format(mpr_eq_med)
    print "MPR != median count: {0}".format(mpr_not_med)
    print "MPR count > 2 & MPR == median count: {0}".format(mprs_gt_2_not)
    print "MPR count > 2 & MPR != median count: {0}".format(mprs_gt_2_eq)


def check_files(log, path):
    if path[-1] != "/":
        path = path + "/"

    data_files = map(lambda x: path + x, os.listdir(path))
    duplicates = []
    with open(log) as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] not in data_files:
                duplicates += [row[0]]
            else:
                data_files.remove(row[0])
        print "Duplicates ({0}):\t {1}".format(len(duplicates[1:]), duplicates[1:])
        print "Missing ({0}):\t {1}".format(len(data_files), data_files)


def compare_logs(log1="New_COG_01.csv", log2="New_COG_02_zl.csv"):
    """"""
    log1_diams = []
    log2_diams = []
    filenames = []
    mismatches = 0
    difference = 0.0
    count = 0
    with open(log1) as file:
        reader = csv.reader(file)
        for row in reader:
            filenames += [row[0]]
            log1_diams += [row[3]]
    with open(log2) as file:
        reader = csv.reader(file)
        for row in reader:
            log2_diams += [row[3]]
    for i in range(0, len(log1_diams)):
        count += 1
        if log1_diams[i] != log2_diams[i]:
            difference += (float(log1_diams[i]) - int(log2_diams[i]))/int(log2_diams[i])
            print "Mismatch in {0}: {1} vs. {2}".format(filenames[i], log1_diams[i], log2_diams[i])
            mismatches += 1
        #else:
            #print "Match in {0}: {1} vs. {2}".format(filenames[i], log1_diams[i], log2_diams[i])
    print "{0} mismatches, or {0}/{2} = {1}%".format(mismatches,mismatches/(float(count))*100,count)


def main():
    """Processes command line arguments"""
    usage = "usage: %prog [options] file"
    p = optparse.OptionParser(usage=usage)
    p.add_option("-p", "--plot", dest="plot", action="store_true", default=False,
                 help="outputs some plots!")
    p.add_option("-z", "--zero-loss", dest="zero_loss", action="store_true", default=False ,
                 help="plot the diameter when losses are not included")
    p.add_option("-D", "--no-diameter", dest="diameter", action="store_false", default=True,
                 help="don't plot the diameter")
    p.add_option("-l", "--use-latex", dest="use_latex", action="store_true", default=False,
                 help="use LaTeX for plot text rendering (you must have LaTeX installed on your system!)")
    p.add_option("-t", "--timings", dest="timings", action="store_true", default=False,
                 help="for every plot, include a complimentary timing plot")
    p.add_option("-n", "--non-normalized", dest="non_normalized", action="store_true", default=False,
                 help="includes plot with non-normalized y-axes")
    p.add_option("-m", "--median-count", dest="median_count", action="store_true", default=False,
                 help="plot the number of medians")
    p.add_option("-M", "--worst-median", dest="worst_median", action="store_true", default=False,
                 help="plot the worst medians")
    p.add_option("-r", "--random-median-average", dest="average_median", action="store_true", default=False,
                 help="plot the worst medians")
    p.add_option("-s", "--strip-mprs", dest="strip_mprs", help="ignore any file with fewer mprs than this number",
                 metavar="MPR-MIN", default="0")
    p.add_option("-e", "--strip-equal", dest="strip_equal", help="ignore any file where mprs == median",
                 action="store_true", default=False)
    p.add_option("-c", "--compare", dest="compare_file", help="compare the diameters of this logfile to another, "
                                                              "and report any mismatches between the two",

                 metavar="COMPARE_FILE")
    p.add_option("-k", "--check-files", dest="check_path", help="Compare the files in the logfile with the files in the"
                                                                "directory, and report any duplicate files in the log,"
                                                                "and any files in the directory but not in the log.",
                 metavar="CHECK_PATH")


    (options, args) = p.parse_args()
    if len(args) != 1:
        p.error("1 argument must be provided: file")
    file = args[0]
    zero_loss = options.zero_loss
    latex = options.use_latex
    plot = options.plot
    compare_file = options.compare_file
    check = options.check_path
    timings = options.timings
    non_normalized = options.non_normalized
    strip_mprs = int(options.strip_mprs)
    diameter = options.diameter
    median_count = options.median_count
    worst_median = options.worst_median
    average_median = options.average_median
    strip_equal = options.strip_equal

    # List of the names of the things we will try to plot
    plot_types = []

    if diameter:
        plot_types += ["Diameter"]
    if zero_loss:
        plot_types += ["Zero Loss Diameter"]
    if median_count:
        plot_types += ["Median Count"]
    if worst_median:
        plot_types += ["Worst Median Diameter"]
    if average_median:
        plot_types += ["Random Median Average Diameter",
                       "Random Median Diameter Standard Deviation"]


    if latex and not plot:
        print "Warning: option '-l' (--use-latex) has no effect without option '-p' (--plot)!"
    if not os.path.isfile(file):
        p.error("File not found, '{0}'. Please be sure you typed the name correctly!".format(file))
    else:
        analyse_data(file, plot_types, non_normalized, timings, plot, latex, strip_mprs, strip_equal)
        if compare_file is not None:
            compare_logs(file, compare_file)
        if check is not None:
            check_files(file, check)
        if plot:
            plt.show()


if __name__ == "__main__":
    main()