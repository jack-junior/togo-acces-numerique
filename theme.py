"""Palette validée (six checks CVD/contraste) — voir note_methodologique.md."""
SURFACE   = '#fcfcfb'
TEXT_1    = '#0b0b0b'
TEXT_2    = '#52514e'
TEXT_MUTE = '#8a8880'
GRID      = '#e7e6e1'

# Catégoriel — ordre fixe, jamais recyclé (worst adjacent CVD ΔE 9.1 / normal 22.9)
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']

# Séquentiel — une seule teinte, clair -> foncé (magnitude)
SEQ = ['#eaf1fb', '#c6dbf5', '#93bcec', '#5f9ce2', '#2a78d6', '#1c5299', '#12345f']

# Divergent — deux pôles + gris neutre au milieu (polarité : déficit / excédent)
DIV = ['#8c3a18', '#c25327', '#eb6834', '#f5a983', '#d8d6d0',
       '#93bcec', '#3f8ade', '#2a78d6', '#1c5299']

STATUS = {'critique': '#e34948', 'attention': '#eda100', 'bon': '#1baf7a'}

LAYOUT = dict(
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(family='system-ui, -apple-system, Segoe UI, sans-serif',
              size=13, color=TEXT_2),
    margin=dict(l=8, r=8, t=48, b=8),
    hoverlabel=dict(bgcolor='white', bordercolor=GRID,
                    font=dict(color=TEXT_1, size=13)),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
)
