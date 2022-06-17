import json
import shutil

import numpy as np
import random
import networkx as nx
from tqdm import tqdm
from collections import defaultdict
from cognitive.auto_task.arguments import get_args
from cognitive import task_generator as tg
from cognitive import constants as const
import os
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

# TODO: add select attributes, combine helper with task_generator.task_generation
root_ops = ["GetCategory", "GetLoc", "GetViewAngle", "GetObject", "Exist", "IsSame", "And"]
boolean_ops = ["Exist", "IsSame", "And"]
# uncomment to add ops
# root_ops += ["NotSame", "Or", "Xor"]
# boolean_ops += ["NotSame", "Or", "Xor"]
leaf_op = ["Select"]
mid_op = ["Switch"]

op_dict = {"Select":
               {"n_downstream": 4,
                "downstream": ["GetCategory", "GetLoc", "GetViewAngle", "GetObject", "None"],
                "same_children_op": False
                },
           "GetCategory":
               {"n_downstream": 1,
                "downstream": ["Select"],
                "sample_dist": [1]
                },
           "GetLoc":
               {"n_downstream": 1,
                "downstream": ["Select"],
                "sample_dist": [1]
                },
           "GetViewAngle":
               {"n_downstream": 1,
                "downstream": ["Select"],
                "sample_dist": [1]
                },
           "GetObject":
               {"n_downstream": 1,
                "downstream": ["Select"],
                "sample_dist": [1]
                },
           "Exist":
               {"n_downstream": 1,
                "downstream": ["Select"],
                "sample_dist": [1]
                },
           "IsSame":
               {"n_downstream": 2,
                "downstream": ["GetCategory", "GetLoc", "GetViewAngle", "GetObject"],
                "sample_dist": [1 / 4, 1 / 4, 1 / 4, 1 / 4],
                "same_children_op": True  # same downstream op
                },
           "And":
               {"n_downstream": 2,
                "downstream": ["Exist", "IsSame", "And"],
                "sample_dist": [1 / 2, 1 / 2, 0],
                "same_children_op": False
                },
           # "Or":
           #     {"n_downstream": 2,
           #      "downstream": ["Exist", "IsSame", "NotSame", "And", "Or", "Xor"],
           #      "sample_dist": [1 / 3, 1 / 3, 1 / 3, 0, 0, 0],
           #      "same_children_op": False
           #      },
           # "Xor":
           #     {"n_downstream": 2,
           #      "downstream": ["Exist", "IsSame", "NotSame", "And", "Or", "Xor"],
           #      "sample_dist": [1 / 3, 1 / 3, 1 / 3, 0, 0, 0],
           #      "same_children_op": False
           #      },
           # "NotSame":
           #     {"n_downstream": 2,
           #      "downstream": ["GetCategory", "GetLoc", "GetViewAngle", "GetObject"],
           #      "sample_dist": [1 / 4, 1 / 4, 1 / 4, 1 / 4],
           #      "same_children_op": True,
           #      },
           }
op_dict = defaultdict(dict, **op_dict)


# uncomment to add more ops
# for op in ['And', 'Or', 'Xor']:
#     op_dict[op]['downstream'] = ["Exist", "IsSame", "NotSame", "And", "Or", "Xor"],
#     op_dict[op]['sample_dist'] = "sample_dist": [1 / 3, 1 / 3, 1 / 3, 0, 0, 0]


# def switch_generator(conditional, do_if, do_else):
#     nl1, cm1 = conditional
#     nl2, cm2 = do_if
#     nl3, cm3 = do_else
#     l1 = len(nl1)
#     l2 = len(nl2)
#     l3 = len(nl3)
#     node_list = nl1 + nl2 + ["switch"] + nl3
#     conn_mtx = np.zeros((l1 + l2 + l3 + 1, l1 + l2 + l3 + 1))
#     conn_mtx[:l1, :l1] = cm1
#     conn_mtx[l1:l1 + l2, l1:l1 + l2] = cm2
#     conn_mtx[l1 - 1, l1 + l2] = 1
#     conn_mtx[l1 + l2 - 1, l1 + l2] = 1
#     conn_mtx[l1 + l2 + 1:, l1 + l2 + 1:] = cm3
#     conn_mtx[l1 + l2, l1 + l2 + 1] = 1
#     return [node_list, conn_mtx]
#
#
# def subTask_Generator(max_op=32, ):
#     conn_mtx = np.zeros((3 ** max_op, 3 ** max_op))
#     node_list = []
#     root_node = random.choice(root_ops)
#     node_list.append(root_node)
#     curr_node = root_node
#     curr_node_idx = 0
#     pos_node_idx = 0
#     done = False
#
#     while not done:  ## how to constraint the number of operators?
#         curr_node = node_list[curr_node_idx]
#         if op_dict[curr_node]["n_downstream"] == 1:
#             if pos_node_idx > max_op:  # select operators based on sample_dist to limit the depth of the tree
#                 curr_node = random.choices(op_dict[curr_node]["downstream"], op_dict[curr_node]["sample_dist"])[0]
#             else:
#                 curr_node = random.choice(op_dict[curr_node]["downstream"])
#             node_list.append(curr_node)
#             conn_mtx[curr_node_idx, pos_node_idx + 1] = 1
#             curr_node_idx += 1
#             pos_node_idx += 1
#         elif op_dict[curr_node]["n_downstream"] == 2:
#             if pos_node_idx > max_op:
#                 curr_node = random.choices(op_dict[curr_node]["downstream"], op_dict[curr_node]["sample_dist"])[0]
#             else:
#                 curr_node = random.choice(op_dict[curr_node]["downstream"])
#             node_list.append(curr_node)
#             node_list.append(curr_node)
#             conn_mtx[curr_node_idx, pos_node_idx + 1] = 1
#             conn_mtx[curr_node_idx, pos_node_idx + 2] = 1
#             curr_node_idx += 1
#             pos_node_idx += 2
#         elif op_dict[curr_node]["n_downstream"] == 0:
#             if all([op == "Select" for op in node_list[curr_node_idx:pos_node_idx + 1]]):
#                 done = True
#             else:
#                 curr_node_idx += 1
#
#     conn_mtx = conn_mtx[:pos_node_idx + 1, :pos_node_idx + 1]
#     return node_list, conn_mtx

def sample_children_helper(op_name, op_count, max_op, depth, max_depth):
    if depth + 1 > max_depth or op_count + 1 > max_op:
        return np.random.choice(op_dict[op_name]["downstream"], p=op_dict[op_name]["sample_dist"])
    else:
        return np.random.choice(op_dict[op_name]["downstream"])


def sample_children_op(op_name, op_count, max_op, depth, max_depth, select_op, select_downstream):
    n_downstream = op_dict[op_name]["n_downstream"]

    if n_downstream == 1:
        return [random.choice(op_dict[op_name]["downstream"])]
    elif op_name == 'Select':
        ops = list()

        if select_downstream is None:
            select_downstream = op_dict['Select']['downstream']

        if select_op:  # if select at least one op for select attribute
            get = random.choice(["GetCategory", "GetLoc", "GetViewAngle", "GetObject"])
            ops.append(get)

            if get in select_downstream:
                select_downstream.remove(get)
            n_downstream -= 1
        elif depth + 1 > max_depth or op_count + 1 > max_op:
            return ['None' for _ in range(n_downstream)]

        for _ in range(n_downstream):
            if np.random.random() < 0.8:
                ops.append('None')
            else:
                if select_downstream:
                    ops.append(select_downstream.pop(random.randrange(len(select_downstream))))
                else:
                    ops.append('None')
        return ops
    else:
        if op_dict[op_name]["same_children_op"]:
            child = sample_children_helper(op_name, op_count, max_op, depth, max_depth)
            return [child for _ in range(n_downstream)]
        else:
            return [sample_children_helper(op_name, op_count, max_op, depth, max_depth) for _ in range(n_downstream)]


def branch_generator(G, node, local_count, op_count, max_op, depth, max_depth, select_op=False, select_downstream=None):
    if node == 'None':
        return None
    elif node == 'CONST':
        return op_count
    else:
        select_op = True if node == 'Exist' else select_op
        children = sample_children_op(node, local_count, max_op, depth, max_depth, select_op, select_downstream)
        if node == 'Select' and any('Get' in c for c in children):
            select_downstream = ['None'] * 4
            select_op = False

        depth += 1
        parent = op_count
        for op in children:
            if op != 'None':
                child = op_count + 1
                local_count += 1
                op_count = branch_generator(G, op, local_count, op_count + 1, max_op, depth, max_depth, select_op,
                                            select_downstream)

                G.add_node(child, label=op)
                G.add_edge(parent, child)
        return op_count


def subtask_graph_generator(count=0, max_op=20, max_depth=10, select_limit=False, root_op=None):
    G = nx.DiGraph()
    root = count

    op_count = count
    root_op = root_op if root_op else random.choice(root_ops)
    G.add_node(op_count, label=root_op)
    select_downstream = ['None'] * 4 if select_limit else None
    local_count = 1
    op_count = branch_generator(G, root_op, local_count, op_count, max_op, 1, max_depth,
                                select_downstream=select_downstream)

    return G, root, op_count


def switch_generator(conditional, do_if, do_else):
    do_if_graph, do_if_root, do_if_node = do_if
    do_else_graph, do_else_root, do_else_node = do_else
    conditional_graph, conditional_root, conditional_node = conditional

    G: nx.DiGraph = nx.compose_all([do_if_graph, do_else_graph, conditional_graph])
    switch_count = conditional_node + 1
    G.add_node(switch_count, label='Switch')
    G.add_edge(do_if_node, switch_count)
    G.add_edge(do_else_node, switch_count)
    G.add_edge(switch_count, conditional_root)
    return G, switch_count, switch_count


def write_instance(G_tuple, task, fp):
    G, _, _ = G_tuple
    G = G.reverse()
    A = nx.nx_agraph.to_agraph(G)
    A.draw(os.path.join(fp, "operator_graph.png"), prog="dot")
    operators = {node[0]: node[1]['label'] for node in G.nodes(data=True)}

    with open(os.path.join(fp, 'node_labels'), 'w') as f:
        json.dump(operators, f, indent=4)
    with open(os.path.join(fp, 'adj_dict'), 'w') as f:
        json.dump(nx.to_dict_of_dicts(G), f, indent=4)
    with open(os.path.join(fp, 'instruction'), 'w') as f:
        json.dump(str(task), f, indent=4)
    return


if __name__ == '__main__':
    const.DATA = const.Data()
    args = get_args()
    print(args)

    boolean_tasks = [
        subtask_graph_generator(max_op=args.max_op, max_depth=args.max_depth, select_limit=args.select_limit,
                                root_op=random.choice(boolean_ops)) for _ in range(args.n_tasks)]
    tasks = [subtask_graph_generator(max_op=args.max_op, max_depth=args.max_depth, select_limit=args.select_limit) for _
             in range(args.n_tasks)]

    for i in range(args.n_tasks):
        fp = os.path.join(args.output_dir, f'{i}')
        if os.path.exists(fp):
            shutil.rmtree(fp)
        os.makedirs(fp)

        G, task = None, None
        for _ in range(args.max_switch):
            if random.random() < args.switch_threshold:
                conditional = random.choice(boolean_tasks)
                if G and task:
                    if random.random() < 0.5:
                        do_if, do_else = G, random.choice(tasks)
                        do_if_task, do_else_task = task, tg.subtask_generation(do_else)
                    else:
                        do_if, do_else = random.choice(tasks), G
                        do_if_task, do_else_task = tg.subtask_generation(do_if), task
                else:
                    do_if, do_else = random.choice(tasks), random.choice(tasks)
                    do_if_task, do_else_task = tg.subtask_generation(do_if), tg.subtask_generation(do_else)

                G = switch_generator(conditional, do_if, do_else)
                task = tg.switch_generation(do_if_task[0], do_if_task[0], do_else_task[0])
            else:
                if not G and not task:
                    G = random.choice(tasks)
                    task = tg.subtask_generation(G)
        write_instance(G, task[0], fp)
