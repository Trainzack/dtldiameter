# DTLMedian.py
# Written July 2017 by Andrew Ramirez and Eli Zupke
# Utilizes previous code to find the "median" reconciliation of a pair of gene and species trees
# and other related information


# -1. DATA STRUCTURE QUICK REFERENCE:
#
#
#   DTL Reconciliation graph:
#       { mapping_node: [event1, event2, ... eventn, number], ...}
#   Event:
#       ('event_type', child_mapping_node1, child_mapping_node2)
#
#   Mapping node (case indicates capitalization standards):
#       ('gene_node', 'SPECIES_NODE')
#   or in loss or contemporary event nodes:
#       (None, None)
#
#
#   (edge) trees:
#       {('R','N'): ('R','N', ('N','C1'), ('N','C2')) ...}
#       aka:
#       {root_edge: (root_edge[0], root_edge[1], child1_edge, child2_edge) ...}
#
#   vertex_trees:
#       {'N':('C1','C2') ...}
#

import sys
import traceback
import time
import random
from operator import itemgetter
import pandas as pd
import DTLReconGraph
import NewDiameter
import RunTests


def mapping_node_sort(ordered_gene_node_list, ordered_species_node_list, mapping_node_list):
    """
    :param ordered_gene_node_list: an ordered dictionary of the gene nodes, where each key is a node
    and the corresponding values are children of that node in the gene tree. Note that the order (pre-
    or post-) in which this tree is passed determines the final order - a preorder gene node list will
    return mapping nodes sorted in preorder. The species and gene orderings must match.
    :param ordered_species_node_list: same as for the gene node list above, except for the species tree
    :param mapping_node_list: a list of all mapping nodes within a given reconciliation graph
    :return: the given mapping nodes except sorted in the order corresponding to the order in which
    the species and gene nodes are passed in (see description of ordered_gene_node_list for more on this).
    The returned mapping node list is sorted first by gene node and then by species node
    """

    # In order to sort the mapping nodes, we need a way to convert them into numbers. These two lookup tables allow
    # us to achieve a lexicographical ordering with gene nodes more significant than species nodes.
    gene_level_lookup = {}
    species_level_lookup = {}

    # By multiplying the gene node keys by the number of species nodes, we can ensure that a mapping node with a later
    # gene node always comes before one with a later species node, because a gene node paired with the last species
    # node will be one level less than the next gene node paired with the first species node.
    gene_multiplier = len(ordered_species_node_list)

    for i, gene_node in enumerate(ordered_gene_node_list):
        gene_level_lookup[gene_node] = i * gene_multiplier

    for i, species_node in enumerate(ordered_species_node_list):
        species_level_lookup[species_node] = i

    # The lambda function looks up the level of both the gene node and the species nodes and adds them together to
    # get a number to give to the sorting algorithm for that mapping node. The gene node is weighted far more heavily
    # than the species node to make sure it is always more significant.
    sorted_list = sorted(mapping_node_list, key=lambda node: gene_level_lookup[node[0]] + species_level_lookup[node[1]])

    return sorted_list


def generate_scores(preorder_mapping_node_list, dtl_recon_graph, gene_root):
    """
    :param preorder_mapping_node_list: A list of all mapping nodes in DTLReconGraph in double preorder
    :param dtl_recon_graph: The DTL reconciliation graph that we are scoring
    :param gene_root: The root of the gene tree
    :return: 0. A file structured like the DTLReconGraph, but with the lists of events replaced
                with dicts, where the keys are the events and the values are the scores of those events, and
             1. The number of MPRs in DTLReconGraph.
    """

    # Initialize the dictionary that will store mapping node and event counts (which also acts as a memoization
    # dictionary)
    counts = dict()

    # Initialize the very start count, for the first call of countMPRs
    count = 0

    # Loop over all given minimum cost reconciliation roots
    for mappingNode in preorder_mapping_node_list:
        if mappingNode[0] == gene_root:
            count += count_mprs(mappingNode, dtl_recon_graph, counts)

    # Initialize the scores dict. This dict contains the frequency score of each
    scores = dict()
    for mappingNode in preorder_mapping_node_list:
        scores[mappingNode] = 0.0

    # This entry is going to be thrown away, but it seems neater to just let calculateScoresOfChildren
    # add scores to an unused entry than to check to see if they are (None, None) in the first place.
    scores[(None, None)] = 0.0

    # The scored graph is like the DTLReconGraph, except instead of individual events being in a list, they are the
    # keys of a dictionary where the values are the frequency scores of those events.
    event_scores = {}

    for mappingNode in preorder_mapping_node_list:

        # If we are at the root of the gene tree, then we need to initialize the score entry
        if mappingNode[0] == geneRoot:
            scores[mappingNode] = counts[mappingNode]# / float(count) Don't do this, this leads to floating-point errors
        calculateScoresForChildren(mappingNode, DTLReconGraph, eventScores, scores, counts)

    for mappingNode in preorderMappingNodeList:
        scores[mappingNode] = scores[mappingNode] / float(count)

    return eventScores, count


def count_mprs(mapping_node, dtl_recon_graph, counts):
    """
    :param mapping_node: an individual mapping node that maps a node
    for the parasite tree onto a node of the host tree, in the format
    (p, h), where p is the parasite node and h is the host node
    :param dtl_recon_graph: A DTL reconciliation graph (see data structure quick reference at top of file)
    :param counts: a dictionary representing the running memo that is passed
    down recursive calls of this function. At first it is just an empty
    dictionary (see above function), but as it gets passed down calls, it collects
    keys of mapping nodes and values of MPR counts. This memo improves runtime
    of the algorithm
    :return: the number of MPRs spawned below the given mapping node in the graph
    """

    # Search the counts dictionary for previously calculated results (this is the memoization)
    if mapping_node in counts:
        return counts[mapping_node]

    # Base case, occurs if being called on a child produced by a loss or contemporary event
    if mapping_node == (None, None):
        return 1

    # Initialize a variable to keep count of the number of MPRs
    count = 0

    # Loop over all event nodes corresponding to the current mapping node
    for eventNode in dtl_recon_graph[mapping_node]:

        # Save the children produced by the current event
        mapping_child1 = eventNode[1]
        mapping_child2 = eventNode[2]

        # Add the product of the counts of both children (over all children) for this event to get the parent's count
        counts[eventNode] = count_mprs(mapping_child1, dtl_recon_graph, counts) * count_mprs(mapping_child2,
                                                                                             dtl_recon_graph, counts)
        count += counts[eventNode]

    # Save the result in the counts
    counts[mapping_node] = count

    return count


def calculate_scores_for_children(mapping_node, dtl_recon_graph, scored_graph, scores, counts):
    """
    This function calculates the frequency score for every mapping node that is a child of an event node that is a
    child of the given mapping node, and stores them in scoredGraph.
    :param mapping_node: The mapping node that is the parent of the two scores we will compute
    :param dtl_recon_graph: The DTL reconciliation graph (see data structure quick reference at top of file)
    :param scored_graph: The scored DTL reconciliation graph (see data structure quick reference at top of file)
    :param scores: The score for each mapping node (which will ultimately be thrown away) that this function helps
    build up
    :param counts: The counts generated in countMPRs
    :return: Nothing, but scoredGraph is built up.
    """
    events = dtl_recon_graph[mapping_node]

    assert scores[mapping_node] != 0
    # This multiplier is arcane magic that we all immediately forgot how it works, but it gets the job done.
    multiplier = float(scores[mapping_node]) / counts[mapping_node]
    # Iterate over every event
    for eventNode in events:

        scored_graph[eventNode] = multiplier * counts[eventNode]

        # Save the children produced by the current event
        mapping_child1 = eventNode[1]
        mapping_child2 = eventNode[2]
        scores[mapping_child1] += scored_graph[eventNode]
        scores[mapping_child2] += scored_graph[eventNode]


def compute_median(dtl_recon_graph, event_scores, postorder_mapping_nodes, mpr_roots):
    """
    :param dtl_recon_graph: A dictionary representing a DTL Recon Graph.
    :param event_scores: A dictionary with event nodes as keys and values corresponding to the frequency of
    that events in MPR space for the recon graph
    :param postorder_mapping_nodes: A list of the mapping nodes in a possible MPR, except sorted first in
    postorder by species node and postorder by gene node
    :param mpr_roots: A list of mapping nodes that could act as roots to an MPR for the species and
    gene trees in question, output from the findBestRoots function in DTLReconGraph.py
    :return: A new dictionary which is has the same form as a DTL reconciliation graph except every
    mapping node only has one event node, along with the number of median reconciliations for the given DTL
    reconciliation graph, as well as the root of the median MPR for the given graph. Thus, this graph will
    represent a single reconciliation: the median reconciliation.
    """

    # Note that for symmetric median reconciliation, each frequency must have 0.5 subtracted from it

    # Initialize a dict that will store the running total frequency sum incurred up to the given mapping node,
    # and the event node that directly gave it that frequency sum. Keys are mapping nodes, values are tuples
    # consisting of a list of event nodes that maximize the frequency - 0.5 sum score for the lower level,
    # and the corresponding running total frequency - 0.5 sum up to that mapping node
    sum_freqs = dict()

    # Loop over all mapping nodes for the gene tree
    for map_node in postorder_mapping_nodes:

        # Contemporaneous events need to be caught from the get-go
        if dtl_recon_graph[map_node] == [('C', (None, None), (None, None))]:
            sum_freqs[map_node] = ([('C', (None, None), (None, None))], 0.5)  # C events have freq 1, so 1 - 0.5 = 0.5
            continue

        # Get the events for the current mapping node and their running frequency sums, in a list
        events = list()
        for event in dtl_recon_graph[map_node]:
            if event[0] == 'L':  # Losses produce only one child, so we only need to look to one lower mapping node
                events.append((event, sum_freqs[event[1]][1] + event_scores[event] - 0.5))
            else:  # Only other options are T, S, and D, which produce two children
                events.append((event, sum_freqs[event[1]][1] + sum_freqs[event[2]][1] + event_scores[event] - 0.5))

        # Find and save the max frequency - 0.5 sum
        max_sum = max(events, key=itemgetter(1))[1]

        # Initialize list to find all events that gives the current mapping node the best freq - 0.5 sum
        best_events = list()

        # Check to see which event(s) produce the max (frequency - 0.5) sum
        for event in events:
            if event[1] == max_sum:
                best_events.append(event[0])

        # Help out the garage collector by discarding the now-useless events list
        del events

        # Save the result for this mapping node so it can be used in higher mapping nodes in the graph
        sum_freqs[map_node] = (best_events[:], max_sum)

    # Get all possible roots of the graph, and their running frequency scores, in a list, for later use
    possible_root_combos = [(root, sum_freqs[root][1]) for root in mpr_roots]

    # Find the best frequency - 0.5 sum in the entire graph based at the roots and the corresponding roots
    best_sum = None
    best_roots = list()
    for root_combo in possible_root_combos:

        # This case occurs at the very first iteration and sets initial states of variables for comparison
        if best_sum is None:
            best_sum = root_combo[1]
            best_roots.append(root_combo[0])
            continue

        # This case requires us add roots to the best roots list
        if root_combo[1] == best_sum:
            best_roots.append(root_combo[0])

        # This case requires we make a new list and best_sum because we've found a better sum
        elif root_combo[1] > best_sum:
            best_sum = root_combo[1]
            best_roots = [root_combo[0]]

        # We just ignore the less than case since it's not a better result

    # Adjust the sum_freqs dictionary so we can use it with the buildDTLReconGraph function from DTLReconGraph.py
    for map_node in sum_freqs:

        # We place the event tuples into lists so they work well with the diameter algorithm
        sum_freqs[map_node] = sum_freqs[map_node][0]  # Only use the event, no longer the associated frequency sum

    # Use the buildDTLReconGraph function from DTLReconGraph.py to find the median recon graph
    med_recon_graph = DTLReconGraph.build_dtl_recon_graph(best_roots, sum_freqs, {})

    # Check to make sure the median is a subgraph of the DTL reconciliation
    assert check_subgraph(dtl_recon_graph, med_recon_graph), 'Median is not a subgraph of the recon graph!'

    # We can use this function to find the number of medians once we've got the final median recon graph
    n_med_recons = DTLReconGraph.count_mprs_wrapper(best_roots, med_recon_graph)

    return med_recon_graph, n_med_recons, best_roots


def check_subgraph(recon_graph, subrecon):
    """
    :param recon_graph: A reconciliation graph
    :param subrecon: Another reconciliation graph, the one which is supposed to be a subgraph of "recon_graph"
    :return: a boolean value: True if the "subrecon" is really a subgraph of "recon_graph",
    False otherwise
    """

    # Loop over all mapping nodes contained in the median reconciliation graph
    for map_node in subrecon:

        # Loop over mapping nodes
        if map_node not in recon_graph:
            return False
        else:

            # Now events for a given mapping node
            for event in subrecon[map_node]:
                if event not in recon_graph[map_node]:
                    return False
    return True


def build_median_recon_graph(event_dict, root):
    """
    :param event_dict: a dictionary with mapping nodes for keys and values which are the single event that mapping
    node may have in a median reconciliation, as a tuple but each of these tuples are the single event in a list.
    :param root: the mapping node at which the median reconciliation or a subgraph of the median
    is starting at
    :return: a DTL Reconciliation Graph in the form returned in DTLReconGraph.py, except here the only
    reconciliation represented is the median - i.e., only events and mapping nodes valid in the median are
    represented. Thus, this function returns the median reconciliation graph. Note, however, that the
    notation and naming conventions for variables are kept general enough to be applied to other types
    of reconciliations, if need be.
    """

    # Initialize the dict to be returned for this subgraph
    subgraph_recon_dict = dict()

    # From the get go, we need to save the current subgraph root and its event
    subgraph_recon_dict.update({root: event_dict[root]})

    # Check for a loss
    if event_dict[root][0][0] == 'L':
        subgraph_recon_dict.update(build_median_recon_graph(event_dict, event_dict[root][0][1]))

    # Check for events that produce two children
    elif event_dict[root][0][0] in ['T', 'S', 'D']:
        subgraph_recon_dict.update(build_median_recon_graph(event_dict, event_dict[root][0][1]))
        subgraph_recon_dict.update(build_median_recon_graph(event_dict, event_dict[root][0][2]))

    return subgraph_recon_dict


def choose_random_median(median_recon, map_node):
    """
    :param median_recon: the full median reconciliation graph, as returned by compute_median
    :param map_node: the current mapping node in the median reconciliation that we're trying
    to find a path from. In the first call, this mapping node will be one of the root mapping
    nodes for the median reconciliation graph, randomly selected
    :return: a single-path reconciliation graph that is a sub-graph of the median
    """

    # Initialize the dictionary that will store the final single-path median that we choose
    random_submedian = dict()

    # From the get go, we need to save the current subgraph root and its event
    next_event = random.choice(median_recon[map_node])  # First, get the next event we'll use
    random_submedian.update({map_node: [next_event]})

    # Check for a loss
    if next_event[0] == 'L':
        random_submedian.update(choose_random_median(median_recon, next_event[1]))

    # Check for events that produce two children
    elif next_event[0] in ['T', 'S', 'D']:
        random_submedian.update(choose_random_median(median_recon, next_event[1]))
        random_submedian.update(choose_random_median(median_recon, next_event[2]))

    # Make sure our single path median is indeed a subgraph of the median
    assert check_subgraph(median_recon, random_submedian), 'Median is not a subgraph of the recon graph!'

    return random_submedian


def compute_median_from_file(filename='le1', dup=2, transfer=3, loss=1):

    species_tree, gene_tree, dtl_recon_graph, mpr_count, best_roots = DTLReconGraph.reconcile(filename, dup, transfer,
                                                                                              loss)

    # Reformat gene tree and get info on it, as well as for the species tree in the following line
    postorder_gene_tree, gene_tree_root, gene_node_count = NewDiameter.reformat_tree(gene_tree, "pTop")
    postorder_species_tree, species_tree_root, species_node_count = NewDiameter.reformat_tree(species_tree,
                                                                                              "hTop")

    # Get a list of the mapping nodes in preorder
    preorder_mapping_node_list = mapping_node_sort(postorder_gene_tree, postorder_species_tree,
                                                   dtl_recon_graph.keys())

    # Find the dictionary for frequency scores for the given mapping nodes and graph, as well as the given gene root
    scores_dict = generate_scores(list(reversed(preorder_mapping_node_list)), dtl_recon_graph, gene_tree_root)

    # Now find the median and related info
    median_reconciliation, n_meds, med_roots = compute_median(dtl_recon_graph, scores_dict[0], preorder_mapping_node_list,
                                                      best_roots)

    # In case we may want it, here we calculate a random single-path median from the median
    random_median = choose_random_median(median_reconciliation, random.choice(med_roots))

    return random_median#median_reconciliation


def calc_med_diameter(filename='TreeLifeData/COG0195.newick', log=None, dup=2, transfer=3, loss=1):

    start_time = time.clock()
    species_tree, gene_tree, dtl_recon_graph, mpr_count, best_roots = DTLReconGraph.reconcile(filename, dup, transfer,
                                                                                              loss)
    dtl_recon_graph_time = time.clock()-start_time

    start_time = time.clock()
    # Reformat gene tree and get info on it, as well as for the species tree in the following line
    postorder_gene_tree, gene_tree_root, gene_node_count = NewDiameter.reformat_tree(gene_tree, "pTop")
    postorder_species_tree, species_tree_root, species_node_count = NewDiameter.reformat_tree(species_tree,
                                                                                              "hTop")

    # Get a list of the mapping nodes in preorder
    preorder_mapping_node_list = mapping_node_sort(postorder_gene_tree, postorder_species_tree,
                                                   dtl_recon_graph.keys())

    # Find the dictionary for frequency scores for the given mapping nodes and graph, as well as the given gene root
    scores_dict = generate_scores(list(reversed(preorder_mapping_node_list)), dtl_recon_graph, gene_tree_root)
    median_reconciliation, n_meds, _ = compute_median(dtl_recon_graph, scores_dict[0], preorder_mapping_node_list,
                                                      best_roots)

    median_time = time.clock() - start_time
    start_time = time.clock()

    # Clean up the reconciliation graph
    NewDiameter.clean_graph(dtl_recon_graph, gene_tree_root)

    # Use the diameter algorithm to find the diameter between the recon graph and its median
    diameter = NewDiameter.new_diameter_algorithm(postorder_species_tree, postorder_gene_tree, gene_tree_root,
                                                  median_reconciliation, dtl_recon_graph, False, False)
    print("Median diameter found: {0}".format(diameter))
    diameter_time = time.clock()-start_time
    if log is not None:
        costs = "D:{0} T:{1} L:{2}".format(dup, transfer, loss)
        RunTests.write_to_csv(log + "_med.csv", costs, filename, mpr_count, gene_node_count, species_node_count,
                              dtl_recon_graph_time, [("Median Count", n_meds, median_time), ("Selected Median Diameter",
                                                                                             diameter, diameter_time)])


def n_med_test():

    n_meds = list()

    for i in range(1, 5666):

        filenum = str(i).zfill(4)
        filename = "TreeLifeData/COG{0}.newick".format(filenum)

        print("Calculating {0} now!".format(filename))

        try:
            n_median_recons = compute_median_from_file(filename)
            n_meds.append(n_median_recons)
        except IOError:
            print('File %s does not exist' % filename)
        except KeyboardInterrupt:
            raise
        except:
            print('File {0} failed!'.format(filename))
            print traceback.print_exc(sys.exc_traceback)

    pd.DataFrame(n_meds, columns=['Number of medians']).to_csv('n_meds_log.csv')


def rep_calc_med_diameter(minimum=1, maximum=5666, log="COG_Median_2", dup=2, transfer=3, loss=1):
    
    # Loop through all the files in TreeLifeData
    for i in range(minimum, maximum):

        # Start building the number of the tree of life data file
        filenum = str(i).zfill(4)
        filename = "TreeLifeData/COG{0}.newick".format(filenum)
        print("Calculating {0} now!".format(filename))
        
        try:
            calc_med_diameter(filename, log, dup, transfer, loss)
        except IOError:
            print('File %s does not exist' % filename)
        except KeyboardInterrupt:
            raise
        except:
            print('File {0} failed!'.format(filename))
            print traceback.print_exc(sys.exc_traceback)
