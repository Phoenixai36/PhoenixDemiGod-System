import plotly.graph_objects as go

# Data definition
data = [
    {"day": "Day 1", "start": 0, "end": 10, "phase": "Foundation"},
    {"day": "Day 2", "start": 10, "end": 20, "phase": "Integration"},
    {"day": "Day 3", "start": 20, "end": 30, "phase": "OMAS Impl"},
    {"day": "Day 4", "start": 30, "end": 40, "phase": "Test & Opt"}
]

colors = ['#1FB8CD', '#FFC185', '#ECEBD5', '#5D878F']

fig = go.Figure()
for i, item in enumerate(data):
    duration = item['end'] - item['start']
    hovertemplate = f"{item['day']}<br>{item['phase']}<br>{item['start']}-{item['end']}h<extra></extra>"
    fig.add_trace(go.Bar(
        y=[item['phase']],
        x=[duration],
        base=[item['start']],
        orientation='h',
        name=item['day'],
        marker_color=colors[i],
        cliponaxis=False,
        hovertemplate=hovertemplate
    ))

fig.update_layout(
    title="Phoenix DemiGod v8.7 Hackathon Timeline",
    xaxis_title="Hours",
    yaxis_title="Phase",
    barmode='overlay',
    legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5)
)

fig.update_xaxes(range=[0, 40], dtick=10)

# Save image
fig.write_image("hackathon_timeline.png")