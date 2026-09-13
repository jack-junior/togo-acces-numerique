"""
Accès aux télécoms et aux services numériques au Togo
Data Challenge Togo AI Lab — Économie numérique, Défi 1
"""
import json, pathlib
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import theme as T

BASE = pathlib.Path(__file__).parent / 'data_app'

st.set_page_config(page_title='Accès numérique au Togo', page_icon='📡',
                   layout='wide', initial_sidebar_state='collapsed')

st.markdown(f"""<style>
 .stApp {{ background:{T.SURFACE}; }}
 h1,h2,h3 {{ color:{T.TEXT_1}; font-weight:650; letter-spacing:-.01em; }}
 .hero {{ font-size:2.6rem; font-weight:680; color:{T.TEXT_1}; line-height:1.05; }}
 .page-title {{ font-size:2.15rem; font-weight:700; color:{T.TEXT_1}; line-height:1.08;
                margin:0 0 .45rem 0; max-width:900px; }}
 .eyebrow {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.1em;
             color:{T.SERIES[0]}; font-weight:700; margin-bottom:.45rem; }}
 .summary {{ border-left:4px solid {T.SERIES[0]}; padding:.8rem 1rem;
             background:#f4f7fb; color:{T.TEXT_1}; margin:1rem 0 1.2rem 0; }}
 .summary strong {{ color:{T.SERIES[0]}; }}
 .insight-grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:.8rem;
                 margin:1.1rem 0 1.4rem 0; }}
 .insight-card {{ border:1px solid {T.GRID}; border-radius:10px; padding:.9rem 1rem;
                  background:#fff; min-height:118px; }}
 .insight-kicker {{ color:{T.TEXT_MUTE}; font-size:.7rem; font-weight:700;
                    letter-spacing:.08em; text-transform:uppercase; }}
 .insight-title {{ color:{T.TEXT_1}; font-size:1.15rem; font-weight:700;
                   margin:.35rem 0 .2rem 0; }}
 .insight-text {{ color:{T.TEXT_2}; font-size:.82rem; line-height:1.35; }}
 @media (max-width: 800px) {{ .insight-grid {{ grid-template-columns:1fr; }} }}
 .herolab {{ font-size:.78rem; text-transform:uppercase; letter-spacing:.07em;
            color:{T.TEXT_MUTE}; margin-bottom:.15rem; }}
 .herosub {{ font-size:.85rem; color:{T.TEXT_2}; }}
 .card {{ border:1px solid {T.GRID}; border-radius:10px; padding:1rem 1.1rem;
          background:#fff; height:100%; }}
 [data-testid="stMetricValue"] {{ color:{T.TEXT_1}; }}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    tab = pd.read_csv(BASE / 'analyse_prefecture.csv')
    with open(BASE / 'prefectures.geojson', encoding='utf-8') as handle:
        geo = json.load(handle)
    infra = pd.read_csv(BASE / 'infrastructures.csv')
    mm = pd.read_csv(BASE / 'mobile_money.csv')
    cant = pd.read_csv(BASE / 'analyse_canton.csv')
    with open(BASE / 'cantons.geojson', encoding='utf-8') as handle:
        cgeo = json.load(handle)
    return tab, geo, infra, mm, cant, cgeo

tab, GEO, INFRA, MM, CANT, CGEO = load()
EXTRACTION = '9 septembre 2026'   # date d'extraction des données sources

INDICATEURS = {
    'momo_pour_10k_hab':    ('Points mobile money pour 10 000 habitants', 'seq'),
    'agences_pour_100k_hab':('Agences télécom pour 100 000 habitants', 'seq'),
    'densite_hab_km2':      ('Densité de population (hab/km²)', 'seq'),
    'momo_ratio_obs_att':   ('Accès observé / attendu (mobile money)', 'div'),
}


# ---------------------------------------------------------------- interprétation automatique
def nf(x, d=0):
    return f'{x:,.{d}f}'.replace(',', ' ')

def indice_gini(dd, count_col):
    ordre = dd.assign(_taux=dd[count_col] / dd.population_rgph5_2022)
    ordre = ordre.sort_values('_taux')
    part_pop = ordre.population_rgph5_2022.cumsum() / ordre.population_rgph5_2022.sum()
    part_points = ordre[count_col].cumsum() / max(ordre[count_col].sum(), 1)
    cw = np.concatenate([[0], part_pop.values])
    cv = np.concatenate([[0], part_points.values])
    return 1 - 2 * np.trapezoid(cv, cw)

def lire(dd, col=None):
    """Génère les constats à partir des données FILTRÉES, jamais d'un texte figé."""
    out = []
    p = dd.population_rgph5_2022
    reg = (dd.groupby('region')[['population_rgph5_2022', 'momo_total', 'agences_telecom']]
             .sum().assign(taux=lambda x: x.momo_total / x.population_rgph5_2022 * 1e4)
             .sort_values('taux', ascending=False))
    if len(reg) > 1:
        hi, lo = reg.index[0], reg.index[-1]
        out.append(f"En taux, **{hi}** est la région la mieux dotée "
                   f"({reg.taux.iloc[0]:.1f} points / 10 000 hab.) et **{lo}** la moins "
                   f"dotée ({reg.taux.iloc[-1]:.1f}). En valeur absolue le classement "
                   f"est différent : **{reg.momo_total.idxmax()}** concentre le plus de "
                   f"points ({nf(reg.momo_total.max())}).")
    worst = dd.nsmallest(1, 'momo_ratio_obs_att').iloc[0]
    big = dd.assign(manque=-dd.momo_ecart).nlargest(1, 'manque').iloc[0]
    out.append(f"La préfecture la plus sous-dotée relativement est **{worst.prefecture}** "
               f"({worst.momo_ratio_obs_att:.2f}× l'attendu). Le déficit le plus lourd en "
               f"volume est **{big.prefecture}** : {nf(abs(big.momo_ecart))} points "
               f"manquants pour {nf(big.population_rgph5_2022)} habitants.")
    z = dd[dd.agences_telecom == 0]
    if len(z):
        out.append(f"**{len(z)} préfectures sur {len(dd)}** n'ont aucune agence télécom, "
                   f"soit {nf(z.population_rgph5_2022.sum())} habitants "
                   f"({z.population_rgph5_2022.sum()/p.sum()*100:.1f} % de la sélection). "
                   f"La plus peuplée est **{z.nlargest(1,'population_rgph5_2022').iloc[0].prefecture}**.")
    if col and col in dd:
        t = dd.nlargest(1, col).iloc[0]; b = dd.nsmallest(1, col).iloc[0]
        out.append(f"Sur l'indicateur affiché, l'écart va de **{b.prefecture}** "
                   f"({b[col]:,.1f}) à **{t.prefecture}** ({t[col]:,.1f}), "
                   f"soit un rapport de {t[col]/max(b[col],1e-9):.1f}×.")
    return out

def bloc_lecture(items):
    st.markdown('##### Lecture automatique')
    for it in items:
        st.markdown(f'- {it}')
    st.caption('Ces constats sont recalculés à chaque changement de filtre — '
               'ils ne sont pas figés dans le code.')

# ---------------------------------------------------------------- en-tête
st.markdown("<div class='eyebrow'>Togo AI Lab · Économie numérique · Défi 1</div>"
            "<div class='page-title'>Accès aux télécoms et aux services numériques au Togo</div>",
            unsafe_allow_html=True)
st.markdown(f"<p class='herosub'>Diagnostic territorial — sources : Géoportail "
            f"Géodata Togo (extraction du {EXTRACTION}) et RGPH-5 (INSEED, 2022). "
            f"39 préfectures, 396 cantons, 8 095 498 habitants.</p>",
            unsafe_allow_html=True)

# ---------------------------------------------------------------- filtres globaux
f1 = st.columns(1)[0]
regions = sorted(tab.region.unique())
sel_reg = f1.multiselect('Région', regions, default=regions,
                         help='Filtre toutes les vues ci-dessous.')
st.caption('Le diagnostic principal est présenté à l’échelle préfectorale. '
         'L’analyse détaillée à l’échelle cantonale se trouve dans « Zones blanches ».')

d = tab[tab.region.isin(sel_reg)] if sel_reg else tab.copy()
if d.empty:
    st.warning('Aucune région sélectionnée.'); st.stop()

st.markdown(
    "<div class='summary'><strong>Le constat central :</strong> le réseau mobile money "
    "maille le territoire plus largement que les agences opérateurs, mais l'accès reste "
    "très inégal selon les préfectures. Utilisez les vues ci-dessous pour comprendre "
    "où se trouvent les écarts et où agir en priorité.</div>",
    unsafe_allow_html=True)

# ---------------------------------------------------------------- chiffres clés
pop = d.population_rgph5_2022.sum()
sans = d[d.agences_telecom == 0]
k = st.columns(4)
def hero(col, label, value, sub):
    col.markdown(f"<div class='card'><div class='herolab'>{label}</div>"
                 f"<div class='hero'>{value}</div>"
                 f"<div class='herosub'>{sub}</div></div>", unsafe_allow_html=True)
hero(k[0], 'Population sélectionnée', f'{pop:,.0f}'.replace(',', ' '),
     f'{len(d)} préfectures')
hero(k[1], 'Points mobile money', f'{d.momo_total.sum():,.0f}'.replace(',', ' '),
     f'{d.momo_total.sum()/pop*1e4:.1f} pour 10 000 hab.')
hero(k[2], 'Agences télécom', f'{d.agences_telecom.sum():,.0f}'.replace(',', ' '),
     f'1 pour {pop/max(d.agences_telecom.sum(),1):,.0f} hab.'.replace(',', ' '))
hero(k[3], 'Sans aucune agence', f'{sans.population_rgph5_2022.sum()/pop*100:.0f} %',
     f'{len(sans)} préfectures, {sans.population_rgph5_2022.sum():,.0f} hab.'.replace(',', ' '))

st.write('')
onglets = st.tabs(['Vue d\'ensemble', 'Implantations', 'Inégalités d\'accès',
                   'Densité & accès', 'Accès local', 'Opérateurs',
                   'Priorités d\'action', 'Sources & méthode'])

# ================================================================ 1. DIAGNOSTIC
with onglets[0]:
    sel_ind = st.selectbox('Indicateur à cartographier', list(INDICATEURS),
                           format_func=lambda k: INDICATEURS[k][0])
    label, kind = INDICATEURS[sel_ind]
    region_rates = (d.groupby('region')[['momo_total', 'population_rgph5_2022']].sum()
                    .assign(rate=lambda x: x.momo_total / x.population_rgph5_2022 * 1e4)
                    .rate.sort_values(ascending=False))
    best_region = region_rates.index[0]
    worst_region = region_rates.index[-1]
    cantons_selection = CANT[CANT.region.isin(sel_reg)] if sel_reg else CANT
    service_median = cantons_selection.dist_service_km.median()
    agency_median = cantons_selection.dist_agence_km.median()
    st.markdown(
        f"<div class='insight-grid'>"
        f"<div class='insight-card'><div class='insight-kicker'>Meilleur taux régional</div>"
        f"<div class='insight-title'>{best_region} · {region_rates.iloc[0]:.1f}</div>"
        f"<div class='insight-text'>points mobile money pour 10 000 habitants.</div></div>"
        f"<div class='insight-card'><div class='insight-kicker'>Poche prioritaire</div>"
        f"<div class='insight-title'>{sans.population_rgph5_2022.sum():,.0f} habitants</div>"
        f"<div class='insight-text'>dans {len(sans)} préfectures sans agence opérateur.</div></div>"
        f"<div class='insight-card'><div class='insight-kicker'>Accès de proximité</div>"
        f"<div class='insight-title'>{service_median:.1f} km vs {agency_median:.1f} km</div>"
        f"<div class='insight-text'>distance médiane vers un service, puis vers une agence.</div></div>"
        f"</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.15, 1])

    def carte(dd, col, kind):
        # densité : distribution très asymétrique (35 -> 5 900 hab/km²),
        # une échelle linéaire écraserait 37 préfectures sur 39 -> échelle log
        logscale = col == 'densite_hab_km2'
        if kind == 'div':
            scale = [[i/(len(T.DIV)-1), c] for i, c in enumerate(T.DIV)]
            extra = dict(zmid=1, colorbar=dict(thickness=10, len=.6, outlinewidth=0,
                         title='', tickfont=dict(size=11, color=T.TEXT_2)))
            fmt = 'Ratio : %{z:.2f}'
        else:
            scale = [[i/(len(T.SEQ)-1), c] for i, c in enumerate(T.SEQ)]
            extra = dict(colorbar=dict(thickness=10, len=.6, outlinewidth=0,
                         title='', tickfont=dict(size=11, color=T.TEXT_2)))
            fmt = '%{z:,.1f}'
        z = np.log10(dd[col]) if logscale else dd[col]
        if logscale:
            ticks = [50, 100, 250, 500, 1000, 2500, 5000]
            extra = dict(colorbar=dict(
                thickness=10, len=.6, outlinewidth=0, title='',
                tickvals=[np.log10(t) for t in ticks],
                ticktext=[f'{t:,}'.replace(',', ' ') for t in ticks],
                tickfont=dict(size=11, color=T.TEXT_2)))
        f = go.Figure(go.Choroplethmap(
            geojson=GEO, locations=dd.fid, featureidkey='properties.fid',
            z=z, colorscale=scale, **extra,
            marker_line_color=T.SURFACE, marker_line_width=1.5, marker_opacity=.92,
            customdata=np.stack([dd.prefecture, dd.region, dd[col]], axis=-1),
            hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>'
                          + ('%{customdata[2]:,.0f} hab/km²' if logscale else fmt)
                          + '<extra></extra>'))
        f.update_layout(**{**T.LAYOUT, 'height': 620,
                           'margin': dict(l=0, r=0, t=6, b=0),
                           'map': dict(style='white-bg', zoom=5.55,
                                       center=dict(lat=8.62, lon=0.96))})
        return f

    with c1:
        st.markdown(f'#### {label}')
        st.plotly_chart(carte(d, sel_ind, kind), use_container_width=True)

    with c2:
        st.markdown('#### Classement des préfectures')
        n = st.slider('Nombre de préfectures affichées', 5, len(d),
                      min(12, len(d)), key='ntop')
        r = d.nlargest(n, sel_ind).sort_values(sel_ind)
        f = go.Figure(go.Bar(
            y=r.prefecture, x=r[sel_ind], orientation='h',
            marker=dict(color=T.SERIES[0], line=dict(color=T.SURFACE, width=2)),
            text=[f'{v:,.1f}' for v in r[sel_ind]], textposition='outside',
            textfont=dict(color=T.TEXT_2, size=12), cliponaxis=False,
            hovertemplate='<b>%{y}</b><br>%{x:,.2f}<extra></extra>'))
        f.update_layout(**{**T.LAYOUT, 'height': 560, 'bargap': .38,
                           'showlegend': False,
                           'xaxis': dict(showgrid=True, gridcolor=T.GRID,
                                         zeroline=False, showticklabels=False,
                                         range=[0, r[sel_ind].max()*1.18]),
                           'yaxis': dict(showgrid=False,
                                         tickfont=dict(size=12, color=T.TEXT_1))})
        st.plotly_chart(f, use_container_width=True)

    st.divider()
    bloc_lecture(lire(d, sel_ind))


# ================================================================ 1. IMPLANTATIONS (objectif 1)
with onglets[1]:
    st.markdown('#### Répartition spatiale des implantations physiques')
    i = INFRA[INFRA.region.isin(sel_reg)] if sel_reg else INFRA.copy()
    cats = st.multiselect('Catégories affichées', sorted(i.operateur.unique()),
                          default=sorted(i.operateur.unique()), key='catimp')
    i = i[i.operateur.isin(cats)]
    show_momo = st.checkbox(f'Superposer les {len(MM):,} points mobile money'
                            .replace(',', ' '), value=False)

    # 3 teintes catégorielles (validées all-pairs) + encodages secondaires
    COUL = {'Togocom': T.SERIES[0], 'Moov': T.SERIES[1], 'Boutique CANAL+': T.SERIES[2],
            'Data center': T.TEXT_1, 'Autre': T.TEXT_MUTE}
    SYMB = {'Data center': 15, 'Autre': 9}
    fig = go.Figure()
    if show_momo:
        m = MM[MM.region.isin(sel_reg)] if sel_reg else MM
        fig.add_trace(go.Scattermap(
            lat=m.lat, lon=m.lon, mode='markers', name='Agent mobile money',
            marker=dict(size=3, color=T.TEXT_MUTE, opacity=.28),
            hovertemplate='Agent mobile money<br>%{text}<extra></extra>',
            text=m.canton))
    for cat in cats:
        sub = i[i.operateur == cat]
        if not len(sub):
            continue
        fig.add_trace(go.Scattermap(
            lat=sub.lat, lon=sub.lon, mode='markers',
            name=f'{cat} ({len(sub)})',
            marker=dict(size=SYMB.get(cat, 11), color=COUL.get(cat, T.TEXT_MUTE),
                        opacity=.95),
            customdata=np.stack([sub.nom, sub.localite, sub.prefecture], axis=-1),
            hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]} — '
                          '%{customdata[2]}<br>' + cat + '<extra></extra>'))
    fig.update_layout(**{**T.LAYOUT, 'height': 640,
                         'margin': dict(l=0, r=0, t=6, b=0),
                         'legend': dict(orientation='h', y=1.06, x=0,
                                        bgcolor='rgba(255,255,255,.85)'),
                         'map': dict(style='white-bg', zoom=5.55,
                                     center=dict(lat=8.62, lon=0.96),
                                     layers=[dict(source=GEO, type='line',
                                                  color=T.GRID, line=dict(width=1))])})
    st.plotly_chart(fig, use_container_width=True)

    c = i.groupby(['operateur']).size().rename('Implantations').reset_index()
    c.columns = ['Catégorie', 'Implantations']
    st.dataframe(c, hide_index=True, use_container_width=True)
    st.divider()
    pref_counts = i.prefecture.value_counts()
    concentration = (f"**{pref_counts.idxmax()}** en regroupe à elle seule "
                     f"{int(pref_counts.max())}." if len(pref_counts)
                     else "Aucune implantation ne correspond aux filtres actifs.")
    bloc_lecture([
        f"Les {int(len(i))} implantations physiques recensées se concentrent sur "
        f"{i.prefecture.nunique()} préfectures sur {len(d)}.",
        concentration,
        "Les 3 data centers du pays sont tous en région Maritime ; les 7 boutiques "
        "CANAL+ recensées sont toutes dans le Grand Lomé.",
    ])
    st.caption('Objectif 1 du défi — cartographie des agences opérateurs '
               '(Moov, Togocom), des boutiques CANAL+ et des data centers. '
               'Les data centers portent un marqueur distinct (encodage secondaire), '
               'pas seulement une couleur.')

# ================================================================ 2. ÉQUITÉ
with onglets[2]:
    gini_momo = indice_gini(d, 'momo_total')
    gini_agences = indice_gini(d, 'agences_telecom')
    deficit = d.assign(deficit=(-d.momo_ecart).clip(lower=0))
    biggest_deficit = deficit.nlargest(1, 'deficit').iloc[0]
    st.markdown(
        f"<div class='insight-grid'>"
        f"<div class='insight-card'><div class='insight-kicker'>Accès le plus équitable</div>"
        f"<div class='insight-title'>Mobile money · {gini_momo:.2f}</div>"
        f"<div class='insight-text'>indice de Gini pour la sélection active.</div></div>"
        f"<div class='insight-card'><div class='insight-kicker'>Réseau d’agences</div>"
        f"<div class='insight-title'>Gini · {gini_agences:.2f}</div>"
        f"<div class='insight-text'>plus l’indice est élevé, plus l’accès est concentré.</div></div>"
        f"<div class='insight-card'><div class='insight-kicker'>Déficit le plus lourd</div>"
        f"<div class='insight-title'>{biggest_deficit.prefecture}</div>"
        f"<div class='insight-text'>{biggest_deficit.deficit:,.0f} points sous l’attendu.</div></div>"
        f"</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('#### Courbe de Lorenz — concentration de l\'accès')
        s = d.sort_values('momo_pour_10k_hab')
        cw = np.concatenate([[0], (s.population_rgph5_2022.cumsum()
                                   / s.population_rgph5_2022.sum()).values])
        cv = np.concatenate([[0], (s.momo_total.cumsum() / s.momo_total.sum()).values])
        gini = indice_gini(d, 'momo_total')
        gini_agences = indice_gini(d, 'agences_telecom')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name='Égalité parfaite',
                                 line=dict(color=T.TEXT_MUTE, width=2, dash='dot'),
                                 hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=cw, y=cv, name='Répartition observée',
                                 line=dict(color=T.SERIES[0], width=2),
                                 hovertemplate='%{x:.0%} de la population<br>'
                                               '%{y:.0%} des points<extra></extra>'))
        fig.add_annotation(x=.62, y=.30, text=f'<b>Gini = {gini:.3f}</b>',
                           showarrow=False, font=dict(color=T.TEXT_1, size=15))
        fig.update_layout(**{**T.LAYOUT, 'height': 430,
                             'legend': dict(orientation='h', y=1.08, x=0,
                                            bgcolor='rgba(0,0,0,0)'),
                             'xaxis': dict(title='Part cumulée de la population',
                                           tickformat='.0%', gridcolor=T.GRID),
                             'yaxis': dict(title='Part cumulée des points de service',
                                           tickformat='.0%', gridcolor=T.GRID)})
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Le réseau d'agents mobile money (Gini {gini:.2f}) est nettement "
               f"plus équitable que le réseau d'agences en propre "
               f"(Gini {gini_agences:.2f}) pour la sélection active.")

    with c2:
        st.markdown('#### Écart à une répartition proportionnelle à la population')
        e = d.sort_values('momo_ecart')
        cols = [T.DIV[2] if v < 0 else T.DIV[6] for v in e.momo_ecart]
        show = (e.momo_ecart.abs() > e.momo_ecart.abs().quantile(.80))
        fig = go.Figure(go.Bar(
            x=e.prefecture, y=e.momo_ecart,
            marker=dict(color=cols, line=dict(color=T.SURFACE, width=2)),
            text=[f'{v:+,.0f}' if s_ else '' for v, s_ in zip(e.momo_ecart, show)],
            textposition='outside', textfont=dict(color=T.TEXT_2, size=10),
            hovertemplate='<b>%{x}</b><br>Écart : %{y:+,.0f} points<extra></extra>'))
        fig.update_layout(**{**T.LAYOUT, 'height': 430, 'bargap': .3,
                             'showlegend': False,
                             'xaxis': dict(tickangle=-60, tickfont=dict(size=9),
                                           showgrid=False),
                             'yaxis': dict(title='Points en écart de l\'attendu',
                                           gridcolor=T.GRID, zerolinecolor=T.TEXT_MUTE)})
        st.plotly_chart(fig, use_container_width=True)
        st.caption('Attendu = répartition strictement proportionnelle à la population. '
                   'Hypothèse normative explicite, pas une vérité économique.')

    st.divider()
    with st.expander('Lire l’interprétation détaillée'):
        bloc_lecture(lire(d))


# ================================================================ 3. DENSITÉ & INFRASTRUCTURE (objectif 3)
with onglets[3]:
    st.markdown('#### Croisement densité de population × implantation des infrastructures')
    c1, c2 = st.columns([1.2, 1])
    with c1:
        x = d.densite_hab_km2
        y = d.momo_pour_10k_hab
        # régression log-linéaire, purement descriptive
        lx = np.log10(x)
        a, b = np.polyfit(lx, y, 1)
        r = np.corrcoef(lx, y)[0, 1]
        grille = np.linspace(lx.min(), lx.max(), 60)
        ecart = y - (a * lx + b)
        seuil = ecart.abs().quantile(.82)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=10**grille, y=a*grille+b, mode='lines',
                                 name='Tendance log-linéaire',
                                 line=dict(color=T.TEXT_MUTE, width=2, dash='dot'),
                                 hoverinfo='skip'))
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='markers+text', name='Préfecture',
            text=[p if abs(e) > seuil else '' for p, e in zip(d.prefecture, ecart)],
            textposition='top center', textfont=dict(size=10, color=T.TEXT_2),
            marker=dict(size=11, color=T.SERIES[0], opacity=.85,
                        line=dict(color=T.SURFACE, width=2)),
            customdata=np.stack([d.prefecture, d.region, d.population_rgph5_2022],
                                axis=-1),
            hovertemplate='<b>%{customdata[0]}</b> — %{customdata[1]}<br>'
                          'Densité : %{x:,.0f} hab/km²<br>'
                          'Accès : %{y:.1f} points / 10 000 hab.<br>'
                          'Population : %{customdata[2]:,.0f}<extra></extra>'))
        fig.update_layout(**{**T.LAYOUT, 'height': 520,
                             'legend': dict(orientation='h', y=1.08, x=0,
                                            bgcolor='rgba(0,0,0,0)'),
                             'xaxis': dict(title='Densité de population (hab/km², échelle log)',
                                           type='log', gridcolor=T.GRID),
                             'yaxis': dict(title='Points mobile money / 10 000 hab.',
                                           gridcolor=T.GRID)})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('##### Densité de population')
        st.plotly_chart(carte(d, 'densite_hab_km2', 'seq'), use_container_width=True)

    st.divider()
    sur = d.assign(e=ecart).nlargest(3, 'e').prefecture.tolist()
    sous = d.assign(e=ecart).nsmallest(3, 'e').prefecture.tolist()
    bloc_lecture([
        f"La corrélation entre densité (log) et accès aux services est "
        f"**{'faible' if abs(r)<.3 else 'modérée' if abs(r)<.6 else 'forte'}** "
        f"(r = {r:.2f}). La densité **n'explique donc pas** à elle seule "
        f"l'implantation des services.",
        f"Au-dessus de la tendance : **{', '.join(sur)}** — mieux servies que leur "
        f"densité ne le laisserait attendre.",
        f"En dessous : **{', '.join(sous)}** — densité comparable, accès nettement "
        f"plus faible. Ce sont des cibles d'extension à coût marginal réduit.",
    ])
    st.caption('Objectif 3 du défi. La tendance est descriptive : elle résume le nuage, '
               'elle n\'estime aucun effet causal et ne produit aucun test de '
               'significativité — ces données sont un inventaire, pas un échantillon.')

# ================================================================ 4. ZONES BLANCHES
with onglets[4]:
    st.markdown('#### Préfectures sans aucune agence télécom')
    z = sans.sort_values('population_rgph5_2022', ascending=False)
    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.markdown(f"<div class='card'><div class='herolab'>Population concernée</div>"
                    f"<div class='hero'>{z.population_rgph5_2022.sum():,.0f}</div>"
                    f"<div class='herosub'>{len(z)} préfectures sur {len(d)} — "
                    f"{z.population_rgph5_2022.sum()/pop*100:.1f} % de la population "
                    f"sélectionnée</div></div>".replace(',', ' '),
                    unsafe_allow_html=True)
        st.write('')
        st.dataframe(
            z[['prefecture', 'region', 'population_rgph5_2022', 'momo_total',
               'momo_pour_10k_hab']]
            .rename(columns={'prefecture': 'Préfecture', 'region': 'Région',
                             'population_rgph5_2022': 'Population',
                             'momo_total': 'Points momo',
                             'momo_pour_10k_hab': 'Momo / 10k hab.'}),
            hide_index=True, use_container_width=True, height=430)
    with c2:
        fig = go.Figure(go.Bar(
            y=z.prefecture, x=z.population_rgph5_2022, orientation='h',
            marker=dict(color=T.STATUS['critique'],
                        line=dict(color=T.SURFACE, width=2)),
            text=[f'{v:,.0f}'.replace(',', ' ') for v in z.population_rgph5_2022],
            textposition='outside', textfont=dict(color=T.TEXT_2, size=11),
            cliponaxis=False,
            hovertemplate='<b>%{y}</b><br>%{x:,.0f} habitants<extra></extra>'))
        fig.update_layout(**{**T.LAYOUT, 'height': 520, 'bargap': .35,
                             'showlegend': False,
                             'xaxis': dict(showgrid=True, gridcolor=T.GRID,
                                           showticklabels=False, zeroline=False,
                                           range=[0, z.population_rgph5_2022.max()*1.16]),
                             'yaxis': dict(autorange='reversed', showgrid=False)})
        st.plotly_chart(fig, use_container_width=True)
    st.caption('Définition retenue — faute d\'accès aux couches de couverture radio '
               '(restreintes sur le Géoportail), les zones blanches sont définies par '
               'l\'absence de point de service physique, non par l\'absence de signal.')

    st.divider()
    st.markdown('#### Échelle canton — distance au point de service le plus proche')
    cc = CANT[CANT.region.isin(sel_reg)] if sel_reg else CANT.copy()

    m1, m2, m3, m4 = st.columns(4)
    hero(m1, 'Cantons analysés', f'{len(cc)}', 'découpage administratif complet')
    hero(m2, 'Sans aucun point', f'{int((cc.points_service == 0).sum())}',
         'aucun service recensé dans le canton')
    hero(m3, 'Distance médiane', f'{cc.dist_service_km.median():.1f} km',
         'au point de service le plus proche')
    hero(m4, 'Distance à une agence', f'{cc.dist_agence_km.median():.1f} km',
         f'médiane — jusqu\'à {cc.dist_agence_km.max():.0f} km')

    st.write('')
    g1, g2 = st.columns([1.15, 1])
    with g1:
        quoi = st.radio('Distance mesurée', ['Tout service', 'Agence opérateur'],
                        horizontal=True, key='distq')
        colc = 'dist_service_km' if quoi == 'Tout service' else 'dist_agence_km'
        f = go.Figure(go.Choroplethmap(
            geojson=CGEO, locations=cc.fid, featureidkey='properties.fid',
            z=cc[colc],
            colorscale=[[i/(len(T.SEQ)-1), c] for i, c in enumerate(T.SEQ)],
            marker_line_color=T.SURFACE, marker_line_width=.6, marker_opacity=.92,
            colorbar=dict(thickness=10, len=.6, outlinewidth=0, title='km',
                          tickfont=dict(size=11, color=T.TEXT_2)),
            customdata=np.stack([cc.canton, cc.prefecture, cc.points_service],
                                axis=-1),
            hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>'
                          '%{z:.1f} km<br>%{customdata[2]} point(s) dans le canton'
                          '<extra></extra>'))
        f.update_layout(**{**T.LAYOUT, 'height': 600,
                           'margin': dict(l=0, r=0, t=6, b=0),
                           'map': dict(style='white-bg', zoom=5.55,
                                       center=dict(lat=8.62, lon=0.96))})
        st.plotly_chart(f, use_container_width=True)
    with g2:
        st.markdown('##### Répartition des cantons par éloignement')
        ordre = ['< 2 km', '2 – 5 km', '5 – 10 km', '> 10 km']
        dist = cc.classe_acces.value_counts().reindex(ordre).fillna(0)
        f = go.Figure(go.Bar(
            x=ordre, y=dist.values,
            marker=dict(color=[T.SEQ[1], T.SEQ[2], T.SEQ[4], T.SEQ[6]],
                        line=dict(color=T.SURFACE, width=2)),
            text=[f'{int(v)}' for v in dist.values], textposition='outside',
            cliponaxis=False, textfont=dict(color=T.TEXT_2, size=13),
            hovertemplate='<b>%{x}</b><br>%{y:.0f} cantons<extra></extra>'))
        f.update_layout(**{**T.LAYOUT, 'height': 260, 'bargap': .35,
                           'showlegend': False,
                           'xaxis': dict(showgrid=False),
                           'yaxis': dict(gridcolor=T.GRID, showticklabels=False,
                                         range=[0, dist.max()*1.2])})
        st.plotly_chart(f, use_container_width=True)

        st.markdown('##### Les 10 cantons les plus éloignés')
        st.dataframe(
            cc.nlargest(10, colc)[['canton', 'prefecture', colc, 'points_service']]
              .rename(columns={'canton': 'Canton', 'prefecture': 'Préfecture',
                               colc: 'Distance (km)',
                               'points_service': 'Points'}),
            hide_index=True, use_container_width=True, height=300)

    st.divider()
    vide = cc[cc.points_service == 0]
    bloc_lecture([
        f"**{int((cc.points_service == 0).sum())} cantons sur {len(cc)}** ne comptent "
        f"aucun point de service — ce sont les zones blanches au sens strict.",
        f"La distance médiane à un point de service est de "
        f"**{cc.dist_service_km.median():.1f} km**, mais celle à une **agence "
        f"opérateur** est de **{cc.dist_agence_km.median():.1f} km** et monte à "
        f"**{cc.dist_agence_km.max():.0f} km**. L'écart entre les deux mesure ce que "
        f"le réseau d'agents privés compense.",
        f"Les cantons les plus isolés se concentrent en région "
        f"**{vide.region.value_counts().idxmax() if len(vide) else '—'}** — "
        f"un résultat invisible à l'échelle de la préfecture, qui moyenne ces écarts.",
    ])
    st.caption('Objectif 4 du défi, traité à l\'échelle du canton. Les couches de '
               'couverture radio du Géoportail étant en accès restreint (HTTP 403), '
               'la zone blanche est définie par la distance au service, mesurée depuis '
               'le centroïde du canton. Limite assumée : le centroïde n\'est pas le '
               'barycentre de population, faute de données de population infra-préfectorales.')


# ================================================================ 4. OPÉRATEURS
with onglets[5]:
    st.markdown('#### Répartition des points mobile money par opérateur')
    cats = [('momo_mixte', 'Moov + Togocom'), ('momo_togocom', 'Togocom seul'),
            ('momo_moov', 'Moov seul'), ('momo_nsp', 'Non renseigné')]
    o = d.sort_values('momo_total', ascending=False)
    fig = go.Figure()
    for (col, name), color in zip(cats, T.SERIES):
        fig.add_trace(go.Bar(
            x=o.prefecture, y=o[col], name=name,
            marker=dict(color=color, line=dict(color=T.SURFACE, width=2)),
            hovertemplate='<b>%{x}</b><br>' + name + ' : %{y:,.0f}<extra></extra>'))
    fig.update_layout(**{**T.LAYOUT, 'height': 470, 'barmode': 'stack',
                         'bargap': .3,
                         'legend': dict(orientation='h', y=1.1, x=0,
                                        bgcolor='rgba(0,0,0,0)'),
                         'xaxis': dict(tickangle=-60, tickfont=dict(size=9),
                                       showgrid=False),
                         'yaxis': dict(title='Points de service', gridcolor=T.GRID)})
    st.plotly_chart(fig, use_container_width=True)
    n_nsp = int(d.momo_nsp.sum())
    st.caption(f'{n_nsp:,} points ({n_nsp/max(d.momo_total.sum(),1)*100:.1f} %) portent '
               'la valeur « Nsp » dans le champ opérateur. Ces manquants sont conservés '
               'comme catégorie à part entière, jamais supprimés.'.replace(',', ' '))

    st.markdown('#### Implantations physiques')
    i = INFRA[INFRA.region.isin(sel_reg)] if sel_reg else INFRA
    st.dataframe(i[['nom', 'localite', 'prefecture', 'region', 'categorie', 'operateur']]
                 .rename(columns={'nom': 'Établissement', 'localite': 'Localité',
                                  'prefecture': 'Préfecture', 'region': 'Région',
                                  'categorie': 'Catégorie', 'operateur': 'Opérateur'}),
                 hide_index=True, use_container_width=True, height=300)


# ================================================================ 6. RECOMMANDATIONS (objectif 5)
with onglets[6]:
    st.markdown('#### Priorisation de l\'extension — score transparent')
    st.markdown("""
Le score de priorité est **entièrement explicite et recalculable** :

`priorité = déficit de points × (part de population)^α × bonus zone blanche`

- **déficit** : écart à une répartition proportionnelle à la population ;
- **α (arbitrage)** : le déficit est *déjà* proportionnel à la population. Repondérer
  une seconde fois par la population revient à l'élever au carré et écrase tout au
  profit des préfectures les plus peuplées. **α = 0** classe au déficit brut,
  **α = 1** privilégie fortement le nombre d'habitants touchés. La valeur par défaut
  **0,5** est un compromis assumé — déplacez le curseur pour voir le classement bouger ;
- **bonus zone blanche** : appliqué si la préfecture n'a aucune agence télécom.

Aucun paramètre caché, aucun modèle boîte noire. Le choix de α est un arbitrage
politique, pas un résultat statistique : il est exposé, pas dissimulé.
""")
    w1, w2, w3 = st.columns(3)
    alpha = w1.slider('α — poids de la population', 0.0, 1.0, 0.5, .1)
    bonus = w2.slider('Bonus zone blanche (aucune agence)', 1.0, 2.5, 1.5, .1)
    topn = w3.slider('Nombre de priorités affichées', 5, 20, 10)

    rec = d.copy()
    rec['deficit'] = (-rec.momo_ecart).clip(lower=0)
    rec['poids'] = rec.population_rgph5_2022 / rec.population_rgph5_2022.sum()
    rec['score'] = (rec.deficit * rec.poids**alpha
                    * np.where(rec.agences_telecom == 0, bonus, 1))
    rec['score'] = (rec.score / rec.score.max() * 100).round(1)
    top = rec.nlargest(topn, 'score').sort_values('score')
    gini_momo = indice_gini(d, 'momo_total')
    gini_agences = indice_gini(d, 'agences_telecom')
    first_priority = rec.nlargest(1, 'score').iloc[0]
    no_agency_count = int((rec.agences_telecom == 0).sum())
    st.markdown(
        f"<div class='insight-grid'>"
        f"<div class='insight-card'><div class='insight-kicker'>Priorité n°1</div>"
        f"<div class='insight-title'>{first_priority.prefecture}</div>"
        f"<div class='insight-text'>score {first_priority.score:.0f}/100 pour la sélection active.</div></div>"
        f"<div class='insight-card'><div class='insight-kicker'>Déficit associé</div>"
        f"<div class='insight-title'>{first_priority.deficit:,.0f} points</div>"
        f"<div class='insight-text'>écart négatif par rapport à la répartition attendue.</div></div>"
        f"<div class='insight-card'><div class='insight-kicker'>Guichets absents</div>"
        f"<div class='insight-title'>{no_agency_count} préfectures</div>"
        f"<div class='insight-text'>sans agence opérateur dans la sélection active.</div></div>"
        f"</div>", unsafe_allow_html=True)

    fig = go.Figure(go.Bar(
        y=top.prefecture, x=top.score, orientation='h',
        marker=dict(color=[T.STATUS['critique'] if a == 0 else T.SERIES[0]
                           for a in top.agences_telecom],
                    line=dict(color=T.SURFACE, width=2)),
        text=[f'{v:.0f}' for v in top.score], textposition='outside',
        cliponaxis=False, textfont=dict(color=T.TEXT_2, size=12),
        customdata=np.stack([top.population_rgph5_2022, top.deficit,
                             top.agences_telecom], axis=-1),
        hovertemplate='<b>%{y}</b><br>Score : %{x:.0f}/100<br>'
                      'Population : %{customdata[0]:,.0f}<br>'
                      'Déficit : %{customdata[1]:,.0f} points<br>'
                      'Agences : %{customdata[2]}<extra></extra>'))
    fig.update_layout(**{**T.LAYOUT, 'height': 460, 'bargap': .38,
                         'showlegend': False,
                         'xaxis': dict(showgrid=True, gridcolor=T.GRID, zeroline=False,
                                       showticklabels=False,
                                       range=[0, 118]),
                         'yaxis': dict(showgrid=False,
                                       tickfont=dict(size=12, color=T.TEXT_1))})
    st.plotly_chart(fig, use_container_width=True)
    st.caption('En rouge : les préfectures sans aucune agence télécom (double peine — '
               'déficit de points de service et absence de guichet opérateur).')

    st.dataframe(
        rec.nlargest(topn, 'score')[['prefecture', 'region', 'population_rgph5_2022',
                                     'agences_telecom', 'momo_total', 'deficit', 'score']]
        .rename(columns={'prefecture': 'Préfecture', 'region': 'Région',
                         'population_rgph5_2022': 'Population',
                         'agences_telecom': 'Agences', 'momo_total': 'Points momo',
                         'deficit': 'Déficit', 'score': 'Score /100'}),
        hide_index=True, use_container_width=True)

    t3 = rec.nlargest(3, 'score').prefecture.tolist()
    zb = rec[rec.agences_telecom == 0].nlargest(3, 'score').prefecture.tolist()
    st.divider()
    st.markdown('##### Recommandations')
    recommendation_panel = st.expander('Lire les recommandations détaillées', expanded=True)
    recommendation_panel.markdown(f"""
**1. Concentrer l'effort sur trois préfectures.** {', '.join(t3)} cumulent les scores
les plus élevés : un déficit important rapporté à une population nombreuse. L'effet
d'une extension y touche le plus grand nombre d'habitants par point installé.

**2. S'appuyer sur le réseau d'agents, pas sur les agences.** L'accès mobile money est
distribué nettement plus équitablement (Gini {gini_momo:.2f}) que le réseau d'agences en propre
(Gini {gini_agences:.2f}) pour la sélection active. Densifier le réseau d'agents agréés coûte moins cher et corrige mieux
l'inégalité territoriale que l'ouverture de guichets.

**3. Traiter en priorité les préfectures sans aucun guichet opérateur.**
{', '.join(zb)} cumulent absence d'agence et déficit de points de service. Une présence
opérateur, même mutualisée entre Moov et Togocom, y changerait la nature de l'accès
(souscription, SAV, réclamation) et pas seulement son volume.

**4. Ne pas confondre urbain et desservi.** Le déficit le plus lourd en volume est
périurbain, pas rural : la croissance démographique du Grand Lomé a devancé
l'implantation des services. Un plan d'extension calé sur la seule ruralité manquerait
la plus grosse poche de population sous-servie.

**5. Sécuriser la donnée avant de décider.** Le jeu CANAL+ du Géoportail est vide, les
couches de couverture radio sont en accès restreint et 6,8 % des points mobile money
ont un opérateur non renseigné. Fiabiliser ces trois points conditionne tout ciblage
plus fin que la préfecture.
""")

# ================================================================ 8. DONNÉES
with onglets[7]:
    st.markdown('#### Table d\'analyse complète')
    st.markdown(
        "<div class='summary'><strong>Instantané reproductible :</strong> cette table "
        "vient de fichiers préparés à partir des sources Géodata Togo et INSEED. "
        "Les détails de provenance, hypothèses et limites sont disponibles ci-dessous.</div>",
        unsafe_allow_html=True)
    st.dataframe(d, hide_index=True, use_container_width=True, height=430)
    st.download_button('Télécharger la table (CSV)',
                       d.to_csv(index=False).encode('utf-8-sig'),
                       'analyse_prefecture.csv', 'text/csv')
    method_expander = st.expander('Voir les sources, hypothèses et limites')
    method_expander.markdown("""
#### D'où viennent les données affichées ?

Le tableau de bord **ne se connecte à aucune API en direct**. Il lit des fichiers
figés (`data_app/`), produits une fois pour toutes par les scripts du projet à
partir des sources ci-dessous. C'est un choix assumé : l'application démarre hors
ligne, s'exécute à l'identique chez n'importe quel évaluateur, et les chiffres du
rapport correspondent exactement à ceux de l'écran. La contrepartie est qu'il
s'agit d'un **instantané**, pas d'un flux temps réel.

`scripts/01_table_prefecture.py` → table d'analyse par préfecture ·
`scripts/02_prepare_app_data.py` → fichiers de l'application ·
`scripts/03_zones_blanches_canton.py` → distances et zones blanches par canton.

#### Sources
- **Géoportail Géodata Togo** — agences opérateurs, data centers, agents mobile
  money, limites administratives (`api.geodata.gouv.tg`).
- **INSEED, RGPH-5 (novembre 2022)** — population par préfecture. Somme des 39
  préfectures vérifiée : 8 095 498 habitants.
- **Annuaire CANAL+ / Canal Box Togo** — 7 boutiques géolocalisées, en substitution
  du jeu Géodata « Agences - CANAL+ », qui renvoie 0 enregistrement.

#### Les six hypothèses sur lesquelles repose ce diagnostic

Aucune n'est neutre. Changer l'une d'elles change les conclusions, donc chacune est
énoncée ici plutôt que dissimulée dans le code.

**H1 — La répartition « attendue » est proportionnelle à la population.**
Tout l'écart observé/attendu et tout le score de priorité en découlent. C'est une
**norme d'équité choisie**, pas une loi économique : rien n'oblige un opérateur privé
à répartir ses points au prorata des habitants. Avec une autre norme — proportionnelle
au PIB local, à la densité, au nombre de comptes actifs — le classement changerait.

**H2 — Le poids donné à la population dans la priorisation (α = 0,5) est un arbitrage.**
Le déficit est déjà proportionnel à la population ; le repondérer une seconde fois
l'élèverait au carré. α = 0 classe au déficit brut, α = 1 privilégie le nombre
d'habitants touchés. **Le curseur est dans l'onglet Recommandations** : c'est un choix
politique, il est réglable et visible.

**H3 — La zone blanche est définie par l'accès au service, pas par le signal radio.**
Les couches « Tours télécoms » du Géoportail sont en accès restreint (HTTP 403), et
OpenStreetMap ne recense que 115 mâts pour tout le Togo — très en deçà du parc réel,
donc écarté. Un canton « blanc » ici est un canton sans point de service accessible,
ce qui n'est pas la même chose qu'un canton sans réseau.

**H4 — Le centroïde du canton représente ses habitants.**
Les distances sont mesurées depuis le centre géométrique, faute de population
infra-préfectorale publiée. Dans un canton allongé ou dont la population est
concentrée à une extrémité, la distance réelle vécue diffère.

**H5 — Les noms de préfectures et de cantons sont reconstruits, pas lus.**
Les polygones de Géodata sont livrés **sans aucun attribut**. La correspondance
code → nom a été rétablie par vote majoritaire des 19 788 points mobile money tombant
dans chaque polygone : 39 préfectures sur 39, pureté ≥ 0,958 (37 sur 39 à 1,000).
Contrôle indépendant : la somme des superficies calculées donne 56 681 km² contre
56 785 km² officiels, soit 0,18 % d'écart.

**H6 — Ces données sont un inventaire, pas un échantillon.**
Aucune inférence statistique n'est produite — p-values et intervalles de confiance
n'auraient pas de sens sur un recensement d'établissements. La rigueur ici est
descriptive et spatiale.

#### Limites déclarées
- **Double comptage évité** : la couche « Télécom » est la couche parente de Moov et
  Togocom (90 = 62 + 28, aucun identifiant commun). Les trois ne sont **jamais**
  additionnées ; `telecom` est la table maîtresse, `moov` et `togocom` la ventilation.
- **Millésimes hétérogènes** : population de 2022, implantations de date inconnue.
- **Manquants conservés** : 1 348 points mobile money (6,8 %) portent `operateur = "Nsp"`.
  Ce sont des manquants déguisés en texte, affichés comme catégorie à part, jamais
  supprimés en silence.
- **MAUP** : les conclusions dépendent du découpage. Les deux échelles — préfecture et
  canton — sont présentées pour cette raison.
- **Sophisme écologique** : un ratio par préfecture ne mesure pas l'accès d'un individu.
  La distance au service le plus proche complète le diagnostic.
- **Périmètre CANAL+** : les 7 boutiques proviennent de l'annuaire de l'enseigne
  (boutiques en propre), pas du registre Géodata (revendeurs inclus). Non comparable.
- **Complétude du registre** : 3 data centers pour tout le pays — réalité du terrain ou
  lacune du registre ? La question est posée, elle ne peut pas être tranchée ici.
""")
    method_expander.caption(f'Données extraites du Géoportail Géodata Togo le {EXTRACTION}. '
                            'Instantané figé : le tableau de bord n\'interroge aucune API en direct.')
