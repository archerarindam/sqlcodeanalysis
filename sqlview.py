import sqlglot
from sqlglot import parse_one, exp
from graphviz import Digraph
import sys
import argparse
import os

def visualize_ast(expression, graph=None, parent=None, cluster_id=0):
    if graph is None:
        graph = Digraph(comment='SQL AST', format='png')
        graph.attr(rankdir='LR')  # Left to Right layout
        graph.attr('node', shape='box', style='filled', color='lightblue', fontname='Helvetica')
        graph.attr('edge', color='gray', fontname='Helvetica')

    node_id = str(id(expression))

    # Define cluster labels based on expression type
    cluster_labels = {
        'With': 'CTE',
        'Select': 'SELECT',
        'From': 'FROM',
        'Join': 'JOIN',
        'Where': 'WHERE',
        'Order': 'ORDER BY',
        'Limit': 'LIMIT',
        # Add more mappings as needed
    }

    # Determine if the current expression should be in a cluster
    cluster_key = expression.key
    if cluster_key in cluster_labels:
        with graph.subgraph(name=f'cluster_{node_id}') as c:
            c.attr(label=cluster_labels.get(cluster_key, cluster_key))
            c.attr(style='filled', color='lightgrey')
            # Add the current node to the cluster
            c.node(node_id, label=cluster_labels.get(cluster_key, cluster_key), shape='box',
                   style='filled', color='lightgrey', fontname='Helvetica')
            if parent:
                graph.edge(parent, node_id)
            # Recurse into children with the current cluster
            for child in expression.args.values():
                if isinstance(child, list):
                    for item in child:
                        if isinstance(item, exp.Expression):
                            visualize_ast(item, graph, parent=node_id, cluster_id=cluster_id+1)
                elif isinstance(child, exp.Expression):
                    visualize_ast(child, graph, parent=node_id, cluster_id=cluster_id+1)
            return graph

    # Regular node without clustering
    this_arg = expression.args.get('this', '')
    label = f"{expression.key}\n{this_arg}"
    graph.node(node_id, label=label)

    if parent:
        graph.edge(parent, node_id)

    # Recurse into children
    for child in expression.args.values():
        if isinstance(child, list):
            for item in child:
                if isinstance(item, exp.Expression):
                    visualize_ast(item, graph, parent=node_id, cluster_id=cluster_id+1)
        elif isinstance(child, exp.Expression):
            visualize_ast(child, graph, parent=node_id, cluster_id=cluster_id+1)

    return graph

def parse_and_visualize(sql, output_filename='sql_ast'):
    try:
        tree = parse_one(sql)
        graph = visualize_ast(tree)
        graph.attr(rankdir='LR')  # Left to Right layout
        graph.attr('node', shape='ellipse', color='lightblue', style='filled')
        graph.render(output_filename, view=True, format='png', cleanup=True)
        print(f"AST visualization saved as {output_filename}.png")
    except Exception as e:
        print(f"Error: {e}")

def read_sql_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            sql_query = f.read()
        return sql_query
    except Exception as e:
        print(f"Failed to read file '{file_path}': {e}")
        sys.exit(1)

# Example Usage with Command-Line Arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse and visualize SQL AST.")
    parser.add_argument('file', help="Path to the SQL file to visualize.")
    parser.add_argument('-o', '--output', default='sql_ast', help="Output filename without extension.")

    args = parser.parse_args()

    # Check if file exists
    if not os.path.isfile(args.file):
        print(f"The file '{args.file}' does not exist. Exiting.")
        sys.exit(1)

    sql_query = read_sql_from_file(args.file)
    if not sql_query.strip():
        print("The SQL file is empty. Exiting.")
    else:
        parse_and_visualize(sql_query, output_filename=args.output)
