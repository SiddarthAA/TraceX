"""Tree-based knowledge graph visualization with system requirements as root nodes."""

import json
from pathlib import Path
from typing import Dict, List, Any, Set


def generate_tree_visualization(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate hierarchical tree visualization with each system requirement as a root node.
    
    Args:
        artifacts: Dictionary of all artifacts by ID
        links: List of all links
        output_path: Path to save the HTML visualization
    """
    
    # Build adjacency list for forward links (parent -> children)
    adjacency = {}
    for link in links:
        source = link['source']
        target = link['target']
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append({
            'id': target,
            'confidence': link['confidence'],
            'relationship': link['relationship']
        })
    
    # Get all system requirements (root nodes)
    system_reqs = [art for art in artifacts.values() if art['type'] == 'SYSTEM_REQ']
    
    # Build tree structure for each system requirement
    trees = []
    for sys_req in system_reqs:
        tree = build_tree_recursive(sys_req['id'], artifacts, adjacency, set())
        trees.append(tree)
    
    # Generate HTML with D3.js tree visualization
    html_content = generate_tree_html(trees)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"    ✓ Tree visualization saved to {Path(output_path).name}")


def build_tree_recursive(
    node_id: str,
    artifacts: Dict[str, Any],
    adjacency: Dict[str, List[Dict]],
    visited: Set[str],
    depth: int = 0
) -> Dict[str, Any]:
    """
    Recursively build tree structure from a node.
    
    Args:
        node_id: Current node ID
        artifacts: All artifacts
        adjacency: Adjacency list of links
        visited: Set of visited nodes (prevent cycles)
        depth: Current depth in tree
    
    Returns:
        Tree node dictionary
    """
    
    if node_id in visited or depth > 10:  # Prevent infinite loops
        return None
    
    visited.add(node_id)
    
    artifact = artifacts.get(node_id)
    if not artifact:
        return None
    
    # Create tree node
    node = {
        'id': node_id,
        'type': artifact['type'],
        'text': artifact.get('text', artifact.get('name', '')),
        'children': []
    }
    
    # Add children recursively
    if node_id in adjacency:
        for child_info in adjacency[node_id]:
            child_tree = build_tree_recursive(
                child_info['id'],
                artifacts,
                adjacency,
                visited.copy(),  # Use copy to allow same node in different branches
                depth + 1
            )
            if child_tree:
                child_tree['confidence'] = child_info['confidence']
                child_tree['relationship'] = child_info['relationship']
                node['children'].append(child_tree)
    
    return node


def generate_tree_html(trees: List[Dict[str, Any]]) -> str:
    """Generate HTML with D3.js tree visualization."""
    
    trees_json = json.dumps(trees, indent=2)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Requirements Traceability Tree</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        h1 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        
        .tree-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        
        .tree {{
            margin-bottom: 40px;
        }}
        
        .node circle {{
            fill: #fff;
            stroke-width: 2px;
            cursor: pointer;
        }}
        
        .node text {{
            font-size: 12px;
            cursor: pointer;
        }}
        
        .node-SYSTEM_REQ circle {{
            stroke: #4A90E2;
            fill: #E3F2FD;
        }}
        
        .node-SYSTEM_REQ_DECOMPOSED circle {{
            stroke: #50C878;
            fill: #E8F5E9;
        }}
        
        .node-HLR circle {{
            stroke: #FFA500;
            fill: #FFF3E0;
        }}
        
        .node-LLR circle {{
            stroke: #9370DB;
            fill: #F3E5F5;
        }}
        
        .node-CODE_VAR circle {{
            stroke: #DC143C;
            fill: #FFEBEE;
        }}
        
        .link {{
            fill: none;
            stroke: #ccc;
            stroke-width: 1.5px;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 400px;
            z-index: 1000;
        }}
        
        .confidence-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 5px;
        }}
        
        .confidence-high {{
            background: #4CAF50;
            color: white;
        }}
        
        .confidence-medium {{
            background: #FF9800;
            color: white;
        }}
        
        .confidence-low {{
            background: #F44336;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌳 Requirements Traceability Tree</h1>
        <div class="subtitle">Hierarchical view with system requirements as root nodes</div>
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #E3F2FD; border: 2px solid #4A90E2;"></div>
            <span>System Requirement</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #E8F5E9; border: 2px solid #50C878;"></div>
            <span>Decomposed Requirement</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FFF3E0; border: 2px solid #FFA500;"></div>
            <span>High-Level Requirement (HLR)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #F3E5F5; border: 2px solid #9370DB;"></div>
            <span>Low-Level Requirement (LLR)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #FFEBEE; border: 2px solid #DC143C;"></div>
            <span>Variable</span>
        </div>
    </div>
    
    <div class="tree-container" id="tree-container"></div>
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        const treesData = {trees_json};
        
        const margin = {{top: 20, right: 120, bottom: 20, left: 120}};
        const width = 1600 - margin.left - margin.right;
        const nodeHeight = 30;
        
        const tooltip = d3.select("#tooltip");
        
        function getConfidenceBadge(confidence) {{
            if (!confidence) return '';
            const value = (confidence * 100).toFixed(0);
            let className = 'confidence-low';
            if (confidence >= 0.65) className = 'confidence-high';
            else if (confidence >= 0.45) className = 'confidence-medium';
            return `<span class="confidence-badge ${{className}}">${{value}}%</span>`;
        }}
        
        function truncateText(text, maxLength = 60) {{
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        }}
        
        treesData.forEach((treeData, index) => {{
            const treeRoot = d3.hierarchy(treeData);
            const descendants = treeRoot.descendants();
            const height = Math.max(500, descendants.length * nodeHeight);
            
            const svg = d3.select("#tree-container")
                .append("svg")
                .attr("class", "tree")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom);
            
            const g = svg.append("g")
                .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
            
            const treeLayout = d3.tree()
                .size([height, width]);
            
            treeLayout(treeRoot);
            
            // Links
            g.selectAll(".link")
                .data(treeRoot.links())
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));
            
            // Nodes
            const node = g.selectAll(".node")
                .data(treeRoot.descendants())
                .enter()
                .append("g")
                .attr("class", d => `node node-${{d.data.type}}`)
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);
            
            node.append("circle")
                .attr("r", 6);
            
            node.append("text")
                .attr("dy", ".31em")
                .attr("x", d => d.children ? -10 : 10)
                .attr("text-anchor", d => d.children ? "end" : "start")
                .text(d => `${{d.data.id}}: ${{truncateText(d.data.text)}}`);
            
            // Tooltips
            node.on("mouseover", function(event, d) {{
                const badge = getConfidenceBadge(d.data.confidence);
                tooltip
                    .style("opacity", 1)
                    .html(`
                        <strong>${{d.data.id}}</strong> (${{d.data.type}}) ${{badge}}<br/>
                        <em>${{d.data.text}}</em>
                    `)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                tooltip.style("opacity", 0);
            }});
        }});
    </script>
</body>
</html>
"""
