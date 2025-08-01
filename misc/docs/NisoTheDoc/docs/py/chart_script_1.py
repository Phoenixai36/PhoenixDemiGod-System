import plotly.graph_objects as go
import numpy as np

# ----------------------
# Data setup
# ----------------------

data_layers = {
    "Core": [
        {"name": "Windsurf IDE", "connections": ["Jan.ai", "Kilo Code", "MCP Servers"]}
    ],
    "LLM": [
        {"name": "Jan.ai", "port": "1337", "connections": ["Mamba Models", "MAP-E Chatbot"]},
        {"name": "Mamba Models", "connections": ["Jan.ai"]},
        {"name": "MAP-E Chatbot", "connections": ["Jan.ai", "OMAS System"]}
    ],
    "Tools": [
        {"name": "Kilo Code", "connections": ["Windsurf IDE", "Ollama"]},
        {"name": "Roo Code", "connections": ["Windsurf IDE"]},
        {"name": "Cline", "connections": ["Windsurf IDE"]},
        {"name": "Gemini CLI", "connections": ["Terminal", "MCP Servers"]}
    ],
    "Orchestration": [
        {"name": "n8n Workflows", "connections": ["MCP Servers", "APIs"]},
        {"name": "Windmill", "connections": ["Python Scripts", "TypeScript"]}
    ],
    "Infrastructure": [
        {"name": "Terraform", "connections": ["Cloud Resource"]},
        {"name": "MCP Servers", "connections": ["Windsurf IDE", "Jan.ai", "Kilo Code", "Gemini CLI", "n8n Workflows"]}
    ],
    "Agents": [
        {"name": "OMAS System", "connections": ["MAP-E Chatbot", "Rasa Agents", "Ontologies"]},
        {"name": "Rasa Agents", "connections": ["OMAS System"]},
        {"name": "Ontologies", "connections": ["OMAS System"]}
    ],
    "External": [
        {"name": "Terminal", "connections": []},
        {"name": "Python Scripts", "connections": []},
        {"name": "TypeScript", "connections": []},
        {"name": "Cloud Resource", "connections": []},
        {"name": "APIs", "connections": []},
        {"name": "Ollama", "connections": []}
    ]
}

layer_order = list(data_layers.keys())
layer_ypos = {layer: idx for idx, layer in enumerate(layer_order)}

brand_cols = ["#1FB8CD", "#FFC185", "#ECEBD5", "#5D878F", "#D2BA4C", "#B4413C", "#964325"]
layer_colors = {layer: brand_cols[i % len(brand_cols)] for i, layer in enumerate(layer_order)}

# ----------------------
# Node positions
# ----------------------
nodes = {}
node_hover = {}
for layer in layer_order:
    comps = data_layers[layer]
    n = len(comps)
    xs = [0] if n == 1 else np.linspace(-2, 2, n)
    for i, comp in enumerate(comps):
        name = comp["name"]
        nodes[name] = (xs[i], layer_ypos[layer])
        # Hover content within 15 chars
        hv = name[:15]
        if comp.get("port"):
            hv = f"{name[:11]}:{comp['port']}"[:15]
        node_hover[name] = hv

# ----------------------
# Edge aggregation by style
# ----------------------
styles = {
    "api1337": {"xs": [], "ys": [], "dash": "dash", "color": "#1FB8CD", "name": "API 1337"},
    "mcp": {"xs": [], "ys": [], "dash": "dot", "color": "#B4413C", "name": "MCP prot"},
    "default": {"xs": [], "ys": [], "dash": "solid", "color": "rgba(70,70,70,0.6)", "name": None},
}

for layer, comps in data_layers.items():
    for comp in comps:
        src = comp["name"]
        for tgt in comp.get("connections", []):
            if tgt not in nodes:
                continue
            x0, y0 = nodes[src]
            x1, y1 = nodes[tgt]
            key = "default"
            if "Jan.ai" in (src, tgt):
                key = "api1337"
            elif "MCP Servers" in (src, tgt):
                key = "mcp"
            styles[key]["xs"].extend([x0, x1, None])
            styles[key]["ys"].extend([y0, y1, None])

# ----------------------
# Build figure
# ----------------------
fig = go.Figure()

# Add edges
for key, val in styles.items():
    if not val["xs"]:
        continue
    fig.add_trace(go.Scatter(
        x=val["xs"],
        y=val["ys"],
        mode="lines",
        line=dict(color=val["color"], width=2, dash=val["dash"]),
        hoverinfo="skip",
        showlegend=val["name"] is not None,
        name=val["name"] if val["name"] else "",
        cliponaxis=False
    ))

# Add nodes per layer for legend grouping
for layer in layer_order:
    xs, ys, hovers = [], [], []
    for comp in data_layers[layer]:
        name = comp["name"]
        x, y = nodes[name]
        xs.append(x)
        ys.append(y)
        hovers.append(node_hover[name])
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        marker=dict(symbol="square", size=28, color=layer_colors[layer], line=dict(width=2, color="white")),
        hoverinfo="text",
        hovertext=hovers,
        name=layer,
        cliponaxis=False
    ))

# Layout
fig.update_layout(
    title="Phoenix v8.7 Stack",
    xaxis=dict(visible=False, range=[-3, 3]),
    yaxis=dict(visible=False, range=[-0.5, len(layer_order)-0.5]),
    showlegend=True
)

fig.write_image("phoenix_final.png")