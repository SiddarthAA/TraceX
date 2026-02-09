"""Visualization utilities for traceability analysis."""

import json
from pathlib import Path
from typing import Dict, List, Any
import html


def generate_trace_graph_html(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    output_file: str
) -> None:
    """
    Generate interactive HTML visualization of trace graph using D3.js.
    """
    
    # Build nodes and edges for D3
    nodes = []
    edges = []
    
    # Color mapping by type
    color_map = {
        'SYSTEM_REQ': '#e74c3c',           # Red
        'SYSTEM_REQ_DECOMPOSED': '#e67e22', # Orange
        'HLR': '#f39c12',                   # Yellow
        'LLR': '#3498db',                   # Blue
        'CODE_VAR': '#2ecc71'               # Green
    }
    
    # Size mapping by type
    size_map = {
        'SYSTEM_REQ': 20,
        'SYSTEM_REQ_DECOMPOSED': 15,
        'HLR': 12,
        'LLR': 10,
        'CODE_VAR': 8
    }
    
    # Create nodes
    for art_id, artifact in artifacts.items():
        art_type = artifact['type']
        nodes.append({
            'id': art_id,
            'type': art_type,
            'text': artifact['text'][:100] + '...' if len(artifact['text']) > 100 else artifact['text'],
            'color': color_map.get(art_type, '#95a5a6'),
            'size': size_map.get(art_type, 10)
        })
    
    # Create edges
    for link in links:
        edges.append({
            'source': link['source_id'],
            'target': link['target_id'],
            'confidence': link.get('confidence', 0.0),
            'type': link.get('link_type', 'unknown')
        })
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Requirements Traceability Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
        }}
        #graph {{
            width: 100%;
            height: 800px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
        }}
        .controls {{
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }}
        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 5px;
            pointer-events: none;
            opacity: 0;
            font-size: 12px;
            max-width: 300px;
        }}
        h1 {{
            margin: 0 0 20px 0;
        }}
        button {{
            padding: 8px 16px;
            margin-right: 10px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background: #2980b9;
        }}
    </style>
</head>
<body>
    <h1>🛩️ Requirements Traceability Graph</h1>
    
    <div class="controls">
        <button onclick="resetZoom()">Reset Zoom</button>
        <button onclick="toggleLabels()">Toggle Labels</button>
        <button onclick="centerGraph()">Center Graph</button>
        <label>
            <input type="checkbox" id="showConfidence" checked> Show Link Confidence
        </label>
    </div>
    
    <div id="graph"></div>
    
    <div class="legend">
        <strong>Legend:</strong><br>
        <div class="legend-item">
            <span class="legend-color" style="background: #e74c3c;"></span>
            System Requirements
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #e67e22;"></span>
            Decomposed Requirements
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #f39c12;"></span>
            High-Level Requirements (HLR)
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #3498db;"></span>
            Low-Level Requirements (LLR)
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #2ecc71;"></span>
            Code Variables
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        const nodes = {json.dumps(nodes)};
        const edges = {json.dumps(edges)};
        
        const width = document.getElementById('graph').clientWidth;
        const height = 800;
        
        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        const g = svg.append('g');
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }});
        
        svg.call(zoom);
        
        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => d.size + 5));
        
        // Create links
        const link = g.append('g')
            .selectAll('line')
            .data(edges)
            .join('line')
            .attr('stroke', d => {{
                const conf = d.confidence || 0;
                if (conf > 0.7) return '#2ecc71';
                if (conf > 0.5) return '#f39c12';
                return '#e74c3c';
            }})
            .attr('stroke-width', d => Math.max(1, (d.confidence || 0.5) * 3))
            .attr('stroke-opacity', 0.6);
        
        // Create link labels
        const linkLabel = g.append('g')
            .selectAll('text')
            .data(edges)
            .join('text')
            .attr('font-size', 8)
            .attr('fill', '#666')
            .text(d => document.getElementById('showConfidence').checked ? 
                `${{(d.confidence * 100).toFixed(0)}}%` : '');
        
        // Create nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .join('circle')
            .attr('r', d => d.size)
            .attr('fill', d => d.color)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended))
            .on('mouseover', showTooltip)
            .on('mouseout', hideTooltip);
        
        // Create node labels
        const label = g.append('g')
            .selectAll('text')
            .data(nodes)
            .join('text')
            .text(d => d.id)
            .attr('font-size', 10)
            .attr('dx', d => d.size + 5)
            .attr('dy', 4);
        
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
        
        // Tooltip functions
        function showTooltip(event, d) {{
            const tooltip = d3.select('#tooltip');
            tooltip.style('opacity', 1)
                .html(`<strong>${{d.id}}</strong><br>Type: ${{d.type}}<br>${{d.text}}`)
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
        
        // Control functions
        function resetZoom() {{
            svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
        }}
        
        function toggleLabels() {{
            const currentOpacity = label.style('opacity');
            label.style('opacity', currentOpacity === '0' ? '1' : '0');
        }}
        
        function centerGraph() {{
            simulation.alpha(1).restart();
        }}
        
        document.getElementById('showConfidence').addEventListener('change', (e) => {{
            linkLabel.text(d => e.target.checked ? `${{(d.confidence * 100).toFixed(0)}}%` : '');
        }});
    </script>
</body>
</html>"""
    
    # Write to file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"📊 Interactive graph saved to: {output_file}")


def generate_trace_table_html(
    artifacts: Dict[str, Any],
    links: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    output_file: str
) -> None:
    """Generate interactive HTML table of trace chains."""
    
    from src.analyze.analyzer import build_trace_graph, trace_chain_forward, classify_chain
    
    graph = build_trace_graph(artifacts, links)
    
    # Get all system requirements and their chains
    sys_reqs = [a for a in artifacts.values() if a['type'] == 'SYSTEM_REQ']
    
    rows = []
    for sys_req in sys_reqs:
        chains = trace_chain_forward(graph, sys_req['id'])
        
        if not chains:
            rows.append({
                'sys_req': sys_req['id'],
                'decomposed': '-',
                'hlr': '-',
                'llr': '-',
                'variable': '-',
                'status': 'INCOMPLETE',
                'status_class': 'status-incomplete'
            })
            continue
        
        for chain in chains:
            classification = classify_chain(chain, graph)
            status_class = {
                'COMPLETE': 'status-complete',
                'PARTIAL': 'status-partial',
                'INCOMPLETE': 'status-incomplete',
                'BROKEN': 'status-broken'
            }.get(classification, 'status-unknown')
            
            row = {
                'sys_req': sys_req['id'],
                'decomposed': '',
                'hlr': '',
                'llr': '',
                'variable': '',
                'status': classification,
                'status_class': status_class,
                'chain': ' → '.join(chain)
            }
            
            for node_id in chain[1:]:
                node = artifacts[node_id]
                node_type = node['type']
                
                if node_type == 'SYSTEM_REQ_DECOMPOSED':
                    row['decomposed'] = node_id
                elif node_type == 'HLR':
                    row['hlr'] = node_id
                elif node_type == 'LLR':
                    row['llr'] = node_id
                elif node_type == 'CODE_VAR':
                    row['variable'] = node_id
            
            rows.append(row)
    
    # Extract coverage metrics (support both formats)
    if 'coverage_metrics' in analysis:
        # Legacy format
        complete = analysis['coverage_metrics']['end_to_end'].get('complete', 0)
        partial = analysis['coverage_metrics']['end_to_end'].get('partial', 0)
        incomplete = analysis['coverage_metrics']['end_to_end'].get('incomplete', 0)
        coverage_pct = analysis['coverage_metrics']['end_to_end'].get('complete_percentage', 0)
    elif 'chains' in analysis:
        # Hierarchical format
        complete = analysis['chains'].get('complete', {}).get('count', 0)
        partial = analysis['chains'].get('partial', {}).get('count', 0)
        incomplete = analysis['chains'].get('broken', {}).get('count', 0)
        coverage_pct = analysis['chains'].get('complete', {}).get('percentage', 0)
    else:
        complete = partial = incomplete = coverage_pct = 0
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Requirements Traceability Table</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            padding: 15px;
            background: #ecf0f1;
            border-radius: 4px;
            text-align: center;
        }}
        .summary-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .summary-label {{
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .status-complete {{
            background: #d5f4e6;
            color: #27ae60;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-partial {{
            background: #ffeaa7;
            color: #f39c12;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-incomplete {{
            background: #ffcccc;
            color: #e74c3c;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-broken {{
            background: #ffcccc;
            color: #c0392b;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .filter {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }}
        .filter input {{
            padding: 8px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .chain-tooltip {{
            display: none;
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <h1>📋 Requirements Traceability Table</h1>
    
    <div class="summary">
        <h2>Coverage Summary</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-value">{complete}</div>
                <div class="summary-label">Complete Chains</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{partial}</div>
                <div class="summary-label">Partial Chains</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{incomplete}</div>
                <div class="summary-label">Incomplete Chains</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{coverage_pct:.1f}%</div>
                <div class="summary-label">Coverage</div>
            </div>
        </div>
    </div>
    
    <div class="filter">
        <input type="text" id="searchBox" placeholder="Search by ID or status..." onkeyup="filterTable()">
    </div>
    
    <table id="traceTable">
        <thead>
            <tr>
                <th>System Req</th>
                <th>Decomposed</th>
                <th>HLR</th>
                <th>LLR</th>
                <th>Variable</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for row in rows:
        html_content += f"""            <tr data-chain="{html.escape(row.get('chain', ''))}">
                <td>{row['sys_req']}</td>
                <td>{row['decomposed']}</td>
                <td>{row['hlr']}</td>
                <td>{row['llr']}</td>
                <td>{row['variable']}</td>
                <td><span class="{row['status_class']}">{row['status']}</span></td>
            </tr>
"""
    
    html_content += """        </tbody>
    </table>
    
    <div class="chain-tooltip" id="chainTooltip"></div>
    
    <script>
        function filterTable() {
            const input = document.getElementById('searchBox');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('traceTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent || row.innerText;
                
                if (text.toUpperCase().indexOf(filter) > -1) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        }
        
        // Show chain on hover
        const rows = document.querySelectorAll('tr[data-chain]');
        const tooltip = document.getElementById('chainTooltip');
        
        rows.forEach(row => {
            row.addEventListener('mouseenter', (e) => {
                const chain = row.getAttribute('data-chain');
                if (chain) {
                    tooltip.textContent = chain;
                    tooltip.style.display = 'block';
                }
            });
            
            row.addEventListener('mousemove', (e) => {
                tooltip.style.left = (e.pageX + 10) + 'px';
                tooltip.style.top = (e.pageY + 10) + 'px';
            });
            
            row.addEventListener('mouseleave', () => {
                tooltip.style.display = 'none';
            });
        });
    </script>
</body>
</html>"""
    
    # Write to file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"📊 Interactive table saved to: {output_file}")
