# safety_check.py

unsafe_nodes = set()  # Initially, no nodes are unsafe

def is_safe(node):
    """
    Check if the given node is safe.
    """
    return node not in unsafe_nodes

def mark_unsafe(node):
    """
    Mark a node as unsafe.
    """
    unsafe_nodes.add(node)

def mark_safe(node):
    """
    Mark a node as safe.
    """
    unsafe_nodes.discard(node)
