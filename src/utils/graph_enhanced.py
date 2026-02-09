"""Enhanced interactive graph visualization with node filtering and trace path highlighting."""

import json
from typing import Dict, List, Any, Set


def generate_enhanced_trace_graph(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate enhanced interactive graph with:
    - Single unified graph
    - Dropdown to select specific node
    - Highlights selected node and all connected nodes (trace path)
    - Option to show only selected node's subgraph
    """
    
    # Build nodes
    nodes = []
    color_map = {
        'SYSTEM_REQ': '#e74c3c',
        'SYSTEM_REQ_DECOMPOSED': '#e67e22',
        'HLR': '#f39c12',
        'LLR': '#3498db',
        'CODE_VAR': '#2ecc71'
    }
    
    size_map = {
        'SYSTEM_REQ': 20,
        'SYSTEM_REQ_DECOMPOSED': 15,
        'HLR': 12,
        'LLR': 10,
        'CODE_VAR': 8
    }
    
    for art_id, artifact in artifacts.items():
        art_type = artifact['type']
        text = artifact.get('text', artifact.get('name', ''))
        nodes.append({
            'id': art_id,
            'type': art_type,
            'text': text[:100] + '...' if len(text) > 100 else text,
            'full_text': text,
            'color': color_map.get(art_type, '#95a5a6'),
            'size': size_map.get(art_type, 10)
        })
    
    # Build edges
    edges = []
    for link in links:
        edges.append({
            'source': link['source_id'],
            'target': link['target_id'],
            'confidence': link.get('confidence', 0.0),
            'type': link.get('link_type', 'unknown')
        })
    
    # Build adjacency for trace finding
    adjacency = {}
    reverse_adjacency = {}
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src not in adjacency:
            adjacency[src] = []
        adjacency[src].append(tgt)
        
        if tgt not in reverse_adjacency:
            reverse_adjacency[tgt] = []
        reverse_adjacency[tgt].append(src)
    
    # Sort nodes for dropdown (system reqs first)
    sorted_nodes = sorted(nodes, key=lambda n: (
        0 if n['type'] == 'SYSTEM_REQ' else
        1 if n['type'] == 'SYSTEM_REQ_DECOMPOSED' else
        2 if n['type'] == 'HLR' else
        3 if n['type'] == 'LLR' else 4,
        n['id']
    ))
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Requirements Traceability Graph - Interactive</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
        
        .controls {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .control-group {{
            margin-bottom: 15px;
        }}
        
        .control-group label {{
            display: inline-block;
            width: 120px;
            font-weight: bold;
            color: #34495e;
        }}
        
        select {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            min-width: 300px;
        }}
        
        button {{
            padding: 8px 16px;
            margin-right: 10px;
            margin-bottom: 10px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        button:hover {{
            background: #2980b9;
        }}
        
        button.secondary {{
            background: #95a5a6;
        }}
        
        button.secondary:hover {{
            background: #7f8c8d;
        }}
        
        #graph {{
            width: 100%;
            height: 700px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .legend {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        
        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-color {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .tooltip {{
            position: absolute;
            padding: 12px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 6px;
            pointer-events: none;
            opacity: 0;
            font-size: 12px;
            max-width: 400px;
            z-index: 1000;
            transition: opacity 0.2s;
        }}
        
        .stats {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}
        
        .stat-item {{
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        
        .node {{
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .node.highlighted {{
            stroke: #f39c12 !important;
            stroke-width: 4px !important;
        }}
        
        .node.dimmed {{
            opacity: 0.2;
        }}
        
        .link {{
            transition: all 0.3s;
        }}
        
        .link.highlighted {{
            stroke: #f39c12 !important;
            stroke-width: 3px !important;
            opacity: 1 !important;
        }}
        
        .link.dimmed {{
            opacity: 0.1;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛩️ Requirements Traceability Graph</h1>
        <div class="subtitle">Interactive visualization with trace path highlighting</div>
    </div>
    
    <div class="controls">
        <div class="control-group">
            <label for="nodeSelect">Select Node:</label>
            <select id="nodeSelect">
                <option value="">-- Show All Nodes --</option>
                {generate_options(sorted_nodes)}
            </select>
        </div>
        
        <div class="control-group">
            <button onclick="showAllNodes()">Show All</button>
            <button onclick="showOnlyTrace()" class="secondary">Show Only Trace</button>
            <button onclick="resetZoom()">Reset Zoom</button>
            <button onclick="centerGraph()">Center Graph</button>
        </div>
        
        <div class="control-group">
            <label>
                <input type="checkbox" id="showConfidence" checked onchange="updateLinkLabels()">
                Show Link Confidence
            </label>
            <label style="margin-left: 20px;">
                <input type="checkbox" id="showLabels" checked onchange="toggleLabels()">
                Show Node Labels
            </label>
        </div>
    </div>
    
    <div id="graph"></div>
    
    <div class="stats" id="stats">
        <strong>Graph Statistics:</strong>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value" id="totalNodes">{len(nodes)}</div>
                <div class="stat-label">Total Nodes</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="totalLinks">{len(edges)}</div>
                <div class="stat-label">Total Links</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="visibleNodes">{len(nodes)}</div>
                <div class="stat-label">Visible Nodes</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="visibleLinks">{len(edges)}</div>
                <div class="stat-label">Visible Links</div>
            </div>
        </div>
    </div>
    
    <div class="legend">
        <strong>Legend:</strong>
        <div class="legend-grid">
            <div class="legend-item">
                <span class="legend-color" style="background: #e74c3c;"></span>
                <span>System Requirements</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #e67e22;"></span>
                <span>Decomposed Requirements</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #f39c12;"></span>
                <span>High-Level Requirements (HLR)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #3498db;"></span>
                <span>Low-Level Requirements (LLR)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #2ecc71;"></span>
                <span>Code Variables</span>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        const nodesData = {json.dumps(nodes)};
        const edgesData = {json.dumps(edges)};
        const adjacency = {json.dumps(adjacency)};
        const reverseAdjacency = {json.dumps(reverse_adjacency)};
        
        let currentSelection = null;
        let traceNodes = new Set();
        let simulation, node, link, label, linkLabel, g, svg, zoom;
        
        // Initialize graph
        function initGraph() {{
            const width = document.getElementById('graph').clientWidth;
            const height = 700;
            
            svg = d3.select('#graph')
                .append('svg')
                .attr('width', width)
                .attr('height', height);
            
            g = svg.append('g');
            
            zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on('zoom', (event) => {{
                    g.attr('transform', event.transform);
                }});
            
            svg.call(zoom);
            
            simulation = d3.forceSimulation(nodesData)
                .force('link', d3.forceLink(edgesData).id(d => d.id).distance(150))
                .force('charge', d3.forceManyBody().strength(-500))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(d => d.size + 10));
            
            // Create links
            link = g.append('g')
                .selectAll('line')
                .data(edgesData)
                .join('line')
                .attr('class', 'link')
                .attr('stroke', d => getConfidenceColor(d.confidence))
                .attr('stroke-width', d => Math.max(1, (d.confidence || 0.5) * 3))
                .attr('stroke-opacity', 0.6)
                .attr('marker-end', 'url(#arrowhead)');
            
            // Add arrowhead marker
            svg.append('defs').append('marker')
                .attr('id', 'arrowhead')
                .attr('viewBox', '-0 -5 10 10')
                .attr('refX', 20)
                .attr('refY', 0)
                .attr('orient', 'auto')
                .attr('markerWidth', 8)
                .attr('markerHeight', 8)
                .attr('xoverflow', 'visible')
                .append('svg:path')
                .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
                .attr('fill', '#999')
                .style('stroke', 'none');
            
            // Create link labels
            linkLabel = g.append('g')
                .selectAll('text')
                .data(edgesData)
                .join('text')
                .attr('class', 'link-label')
                .attr('font-size', 9)
                .attr('fill', '#666')
                .attr('text-anchor', 'middle')
                .text(d => document.getElementById('showConfidence').checked ? 
                    `${{(d.confidence * 100).toFixed(0)}}%` : '');
            
            // Create nodes
            node = g.append('g')
                .selectAll('circle')
                .data(nodesData)
                .join('circle')
                .attr('class', 'node')
                .attr('r', d => d.size)
                .attr('fill', d => d.color)
                .attr('stroke', '#fff')
                .attr('stroke-width', 2)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('mouseover', showTooltip)
                .on('mouseout', hideTooltip)
                .on('click', (event, d) => {{
                    event.stopPropagation();
                    selectNode(d.id);
                }});
            
            // Create node labels
            label = g.append('g')
                .selectAll('text')
                .data(nodesData)
                .join('text')
                .attr('class', 'node-label')
                .text(d => d.id)
                .attr('font-size', 11)
                .attr('font-weight', 'bold')
                .attr('dx', d => d.size + 5)
                .attr('dy', 4)
                .attr('fill', '#2c3e50');
            
            // Update positions on tick
            simulation.on('tick', () => {{
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                linkLabel
                    .attr('x', d => (d.source.x + d.target.x) / 2)
                    .attr('y', d => (d.source.y + d.target.y) / 2);
                
                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
                
                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            }});
        }}
        
        // Get confidence color
        function getConfidenceColor(conf) {{
            if (conf > 0.65) return '#2ecc71';
            if (conf > 0.45) return '#f39c12';
            return '#e74c3c';
        }}
        
        // Find all connected nodes (forward and backward)
        function findTraceNodes(nodeId) {{
            const visited = new Set();
            const queue = [nodeId];
            
            while (queue.length > 0) {{
                const current = queue.shift();
                if (visited.has(current)) continue;
                visited.add(current);
                
                // Forward links (children)
                if (adjacency[current]) {{
                    for (const child of adjacency[current]) {{
                        if (!visited.has(child)) {{
                            queue.push(child);
                        }}
                    }}
                }}
                
                // Backward links (parents)
                if (reverseAdjacency[current]) {{
                    for (const parent of reverseAdjacency[current]) {{
                        if (!visited.has(parent)) {{
                            queue.push(parent);
                        }}
                    }}
                }}
            }}
            
            return visited;
        }}
        
        // Select node and highlight trace
        function selectNode(nodeId) {{
            currentSelection = nodeId;
            document.getElementById('nodeSelect').value = nodeId;
            
            // Find all connected nodes
            traceNodes = findTraceNodes(nodeId);
            
            // Update stats
            document.getElementById('visibleNodes').textContent = traceNodes.size;
            
            // Count visible links
            const visibleLinksCount = edgesData.filter(e => 
                traceNodes.has(e.source.id || e.source) && 
                traceNodes.has(e.target.id || e.target)
            ).length;
            document.getElementById('visibleLinks').textContent = visibleLinksCount;
            
            // Highlight nodes
            node.classed('highlighted', d => d.id === nodeId)
                .classed('dimmed', d => !traceNodes.has(d.id));
            
            // Highlight links
            link.classed('highlighted', d => 
                    (d.source.id || d.source) === nodeId || 
                    (d.target.id || d.target) === nodeId)
                .classed('dimmed', d => 
                    !traceNodes.has(d.source.id || d.source) || 
                    !traceNodes.has(d.target.id || d.target));
            
            // Dim labels
            label.style('opacity', d => traceNodes.has(d.id) ? 1 : 0.2);
            linkLabel.style('opacity', d => 
                (traceNodes.has(d.source.id || d.source) && 
                 traceNodes.has(d.target.id || d.target)) ? 1 : 0.1);
        }}
        
        // Show all nodes
        function showAllNodes() {{
            currentSelection = null;
            traceNodes = new Set(nodesData.map(n => n.id));
            document.getElementById('nodeSelect').value = '';
            
            // Reset stats
            document.getElementById('visibleNodes').textContent = nodesData.length;
            document.getElementById('visibleLinks').textContent = edgesData.length;
            
            // Remove highlighting
            node.classed('highlighted', false).classed('dimmed', false);
            link.classed('highlighted', false).classed('dimmed', false);
            label.style('opacity', 1);
            linkLabel.style('opacity', 1);
        }}
        
        // Show only trace subgraph
        function showOnlyTrace() {{
            if (!currentSelection) {{
                alert('Please select a node first');
                return;
            }}
            
            // Hide nodes not in trace
            node.style('display', d => traceNodes.has(d.id) ? 'block' : 'none');
            label.style('display', d => traceNodes.has(d.id) ? 'block' : 'none');
            
            // Hide links not in trace
            link.style('display', d => 
                traceNodes.has(d.source.id || d.source) && 
                traceNodes.has(d.target.id || d.target) ? 'block' : 'none');
            linkLabel.style('display', d => 
                traceNodes.has(d.source.id || d.source) && 
                traceNodes.has(d.target.id || d.target) ? 'block' : 'none');
            
            // Remove dimming
            node.classed('dimmed', false);
            link.classed('dimmed', false);
            
            // Restart simulation
            simulation.alpha(0.3).restart();
        }}
        
        // Node selector change
        document.getElementById('nodeSelect').addEventListener('change', function() {{
            const selectedId = this.value;
            if (selectedId) {{
                selectNode(selectedId);
            }} else {{
                showAllNodes();
            }}
        }});
        
        // Reset zoom
        function resetZoom() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }}
        
        // Center graph
        function centerGraph() {{
            const width = document.getElementById('graph').clientWidth;
            const height = 700;
            simulation.force('center', d3.forceCenter(width / 2, height / 2));
            simulation.alpha(0.3).restart();
        }}
        
        // Toggle labels
        function toggleLabels() {{
            const show = document.getElementById('showLabels').checked;
            label.style('display', show ? 'block' : 'none');
        }}
        
        // Update link labels
        function updateLinkLabels() {{
            const show = document.getElementById('showConfidence').checked;
            linkLabel.text(d => show ? `${{(d.confidence * 100).toFixed(0)}}%` : '');
        }}
        
        // Tooltip
        function showTooltip(event, d) {{
            const tooltip = d3.select('#tooltip');
            tooltip.style('opacity', 1)
                .html(`
                    <strong>${{d.id}}</strong><br>
                    <em>Type: ${{d.type}}</em><br>
                    <div style="margin-top: 8px; font-size: 11px;">${{d.text}}</div>
                `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        }}
        
        function hideTooltip() {{
            d3.select('#tooltip').style('opacity', 0);
        }}
        
        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        // Initialize on load
        initGraph();
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"    ✓ Enhanced graph saved to {output_path}")


def generate_options(nodes):
    """Generate HTML options for node selector."""
    options = []
    current_type = None
    
    for node in nodes:
        if node['type'] != current_type:
            if current_type is not None:
                options.append('</optgroup>')
            current_type = node['type']
            type_label = {
                'SYSTEM_REQ': 'System Requirements',
                'SYSTEM_REQ_DECOMPOSED': 'Decomposed Requirements',
                'HLR': 'High-Level Requirements (HLR)',
                'LLR': 'Low-Level Requirements (LLR)',
                'CODE_VAR': 'Code Variables'
            }.get(current_type, current_type)
            options.append(f'<optgroup label="{type_label}">')
        
        text_preview = node['text'][:50] + '...' if len(node['text']) > 50 else node['text']
        options.append(f'<option value="{node["id"]}">{node["id"]}: {text_preview}</option>')
    
    if current_type is not None:
        options.append('</optgroup>')
    
    return '\n'.join(options)
