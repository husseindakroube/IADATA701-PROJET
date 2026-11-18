"""Explorateur cartographique mensuel RailInsight (HTML interactif).

Exécuter depuis la racine du projet :
    uv run python scripts/reporting/interactive_network_dashboard.py

Puis servir le HTML en HTTP local :
    uv run python -m http.server 8000
"""

import json
from pathlib import Path

import pandas as pd
from plotly.offline import get_plotlyjs

from sncf_rail_insight.graph.centrality import compute_all_graph_features
from sncf_rail_insight.graph.network import build_weighted_railway_graph
from sncf_rail_insight.graph.routes import compute_edge_features
from sncf_rail_insight.preprocessing import prepare_graph_data

DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.csv")
COORDS_PATH = Path("data/reference/station_coordinates.csv")
OUTPUT_PATH = Path("outputs/reporting/interactive_network_dashboard.html")


def build_monthly_networks(data: pd.DataFrame, coords: pd.DataFrame) -> dict:
    """Construit les métriques mensuelles sans mélanger les périodes."""
    coords = coords[["station", "lat", "lon"]].copy()
    coords["station"] = coords["station"].str.strip().str.upper()
    coords = coords.drop_duplicates("station", keep=False)
    coordinate_lookup = coords.set_index("station")[["lat", "lon"]].to_dict("index")

    months = {}
    for month, subset in data.groupby(data["date"].dt.strftime("%Y-%m"), sort=True):
        graph = build_weighted_railway_graph(subset)
        node_features = compute_all_graph_features(graph)
        edge_features = compute_edge_features(graph)

        missing = set(node_features["station"]) - set(coordinate_lookup)
        if missing:
            raise ValueError(f"Coordonnées manquantes ({month}) : {sorted(missing)}")

        nodes = []
        for row in node_features.to_dict("records"):
            coord = coordinate_lookup[row["station"]]
            nodes.append({
                **row,
                "lat": float(coord["lat"]),
                "lon": float(coord["lon"]),
            })

        edges = []
        for row in edge_features.to_dict("records"):
            a, b = coordinate_lookup[row["departure"]], coordinate_lookup[row["arrival"]]
            edges.append({
                **row,
                "a_lat": float(a["lat"]),
                "a_lon": float(a["lon"]),
                "b_lat": float(b["lat"]),
                "b_lon": float(b["lon"]),
            })

        months[month] = {"nodes": nodes, "edges": edges}
        print(f"{month} : {len(nodes)} gares, {len(edges)} liaisons")

    return months


def main() -> None:
    """Génère un tableau de bord HTML autonome côté Python."""
    raw = pd.read_csv(DATA_PATH, sep=";")
    data = prepare_graph_data(raw)
    coords = pd.read_csv(COORDS_PATH)

    monthly = build_monthly_networks(data, coords)
    if not monthly:
        raise ValueError("Aucun mois disponible.")

    # Préserve le fonctionnement hors ligne de Plotly.
    js = get_plotlyjs()
    payload = json.dumps(monthly, ensure_ascii=False, allow_nan=False)
    payload = payload.replace("</", "<\\/")

    html = HTML_TEMPLATE.replace("__PLOTLY_JS__", js).replace("__NETWORK_DATA__", payload)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"\nCarte générée : {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1e6:.1f} Mo)")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>RailInsight — Explorateur du réseau TGV</title>
  <style>
    :root{--navy:#101e36;--blue:#2563eb;--teal:#0d9488;--paper:#f2f6fc;--line:#dfE6f1;--text:#172840;--muted:#718199}
    *{box-sizing:border-box}
    body{margin:0;background:var(--paper);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--text)}
    header{background:var(--navy);color:white;padding:17px 25px;display:flex;align-items:center;justify-content:space-between;gap:15px}
    .brand{font-weight:750;font-size:23px;letter-spacing:-.6px}
    .brand span{color:#56d3bd}
    header .sub{font-size:12px;color:#bdcce0}
    main{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;padding:16px;height:calc(100vh - 82px);min-height:650px}
    .map{background:white;border:1px solid var(--line);border-radius:16px;overflow:hidden;position:relative}
    #map{width:100%;height:100%}
    .map-legend{position:absolute;bottom:18px;left:18px;z-index:10;background:rgba(255,255,255,.96);box-shadow:0 2px 16px #20305019;
      border:1px solid var(--line);border-radius:10px;padding:10px 13px;color:#41506a;font-size:12px;pointer-events:none}
    .legend-dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--teal);vertical-align:middle;margin-right:5px}
    aside{background:white;border:1px solid var(--line);border-radius:16px;padding:20px;overflow-y:auto;box-shadow:0 2px 12px #10203609}
    h2{font-size:15px;margin:0 0 14px;letter-spacing:-.2px}
    h3{font-size:14px;margin:24px 0 12px}
    label{display:block;color:#586981;font-size:12px;font-weight:650;margin:12px 0 6px}
    select{width:100%;background:#f8fafd;color:var(--text);border:1px solid #d5deeb;border-radius:9px;padding:10px 9px;font-size:13px}
    .stats{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:18px 0}
    .stat{border-radius:10px;background:#f2f7fd;padding:12px}
    .stat .number{font-size:22px;font-weight:750;letter-spacing:-.6px}
    .stat .caption{color:var(--muted);font-size:11px}
    .detail{background:#f8fafd;border:1px solid var(--line);border-radius:11px;padding:14px;margin-top:10px}
    .detail-title{font-weight:750;font-size:15px;line-height:1.35}
    .hint{font-size:12px;color:var(--muted)}
    .data-row{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-top:10px;font-size:12px}
    .data-row b{font-variant-numeric:tabular-nums;text-align:right;font-size:13px}
    .pill{display:inline-block;border-radius:20px;background:#e5f7f3;color:#086a61;padding:3px 8px;font-size:11px;font-weight:650;margin-top:8px}
    .actions{display:flex;gap:8px;margin-top:12px}
    button{cursor:pointer;border:1px solid #cfdaeb;background:white;color:#3e5b7a;padding:7px 11px;border-radius:8px;font-size:12px}
    button:hover{background:#eef5ff}
    .note{color:#718199;font-size:11px;margin:19px 0 0}
    @media(max-width:900px){main{grid-template-columns:1fr;height:auto}.map{height:600px}aside{overflow:visible}}
  </style>
  <script>__PLOTLY_JS__</script>
</head>
<body>
<header>
 <div><div class="brand">Rail<span>Insight</span> <span style="font-size:15px;color:#ccd8e9;font-weight:450">/ Réseau TGV</span></div>
 <div class="sub">Exploration géographique · circulations mensuelles · centralités</div></div>
 <div class="sub">Données AQST · carte interactive</div>
</header>
<main>
 <section class="map"><div id="map"></div>
  <div class="map-legend"><div><span class="legend-dot"></span> Taille = PageRank pondéré</div>
    <div>Épaisseur des liens = trains circulés</div><div>Choisissez une gare ou une liaison dans le panneau de droite</div></div>
 </section>
 <aside>
   <h2>Explorer le réseau</h2>
   <label for="month">Mois</label>
   <select id="month"></select>
   <label for="station">Gare (afficher ses liaisons)</label>
   <select id="station"></select>
   <label for="route">Liaison (sens de circulation)</label>
   <select id="route"></select>
   <div class="actions"><button id="reset">Réinitialiser les filtres</button></div>
   <div class="stats">
    <div class="stat"><div class="number" id="stationCount">—</div><div class="caption">Gares actives ce mois</div></div>
    <div class="stat"><div class="number" id="edgeCount">—</div><div class="caption">Liaisons orientées</div></div>
   </div>
   <h3>Fiche de sélection</h3>
   <div class="detail" id="details"><div class="hint">Sélectionnez une gare ou une liaison dans les menus ci-dessus.</div></div>
   <p class="note">Les volumes correspondent au nombre de trains circulés, pas au nombre de voyageurs.
   Centralités calculées sur le réseau du mois sélectionné.
   Certains libellés géographiques (ex. ITALIE) sont représentatifs.</p>
 </aside>
</main>
<script>
const MONTHS = __NETWORK_DATA__;
const monthSelect = document.getElementById('month');
const stationSelect = document.getElementById('station');
const routeSelect = document.getElementById('route');
const details = document.getElementById('details');
const mapEl = document.getElementById('map');
const fmt = (n, maximumFractionDigits=0) => Number(n).toLocaleString('fr-FR',{maximumFractionDigits});
const percent = (v) => (100 * v).toLocaleString('fr-FR',{maximumFractionDigits:2}) + ' %';
const months = Object.keys(MONTHS).sort();
const allStations = [...new Set(Object.values(MONTHS).flatMap(x=>x.nodes.map(n=>n.station)))].sort();
let selectedMonth = months.includes('2024-12') ? '2024-12' : months.at(-1);
let selectedStation = '';
let selectedRoute = '';
let firstRender = true;
const mapCenter = {lat:46.4,lon:3.0};
function option(value,text){const o=document.createElement('option');o.value=value;o.textContent=text;return o;}
function setOptions(el, entries, selected) {
  el.replaceChildren(...entries.map(([v,t])=>option(v,t)));
  el.value=selected;
}
setOptions(monthSelect,months.map(m=>[m,new Date(m+'-01T00:00:00').toLocaleDateString('fr-FR',{month:'long',year:'numeric'})]),selectedMonth);
setOptions(stationSelect,[['','Toutes les gares'],...allStations.map(s=>[s,s])],'');
function row(key,val){return `<div class="data-row"><span>${key}</span><b>${val}</b></div>`;}
function renderDetails(){
  const frame=MONTHS[selectedMonth];
  if(selectedRoute){
    const e=frame.edges.find(e=>e.departure+' → '+e.arrival===selectedRoute);
    if(e){
      details.innerHTML=`<div class="detail-title">${e.departure} → ${e.arrival}</div><span class="pill">Liaison orientée · ${selectedMonth}</span>`
      +row('Trains circulés',fmt(e.edge_volume))+row('Part du trafic sortant',percent(e.edge_traffic_share))
      +row('Trafic en sens inverse',fmt(e.edge_reverse_volume));
      return;
    }
  }
  if(selectedStation){
    const n=frame.nodes.find(n=>n.station===selectedStation);
    if(n){
      details.innerHTML=`<div class="detail-title">${n.station}</div><span class="pill">Gare · ${selectedMonth}</span>`
      +row('Liaisons entrantes',fmt(n.in_degree))+row('Liaisons sortantes',fmt(n.out_degree))
      +row('Trafic entrant',fmt(n.in_strength))+row('Trafic sortant',fmt(n.out_strength))
      +row('PageRank',fmt(n.pagerank,5))+row('PageRank pondéré',fmt(n.weighted_pagerank,5))
      +row('Betweenness',fmt(n.betweenness,5));
      return;
    }
  }
  details.innerHTML='<div class="hint">Sélectionnez une gare ou une liaison pour afficher ses caractéristiques mensuelles.</div>';
}
function updateRoutes(){
  const frame=MONTHS[selectedMonth];
  const filtered=frame.edges.filter(e=>!selectedStation||e.departure===selectedStation||e.arrival===selectedStation);
  const labels=filtered.map(e=>e.departure+' → '+e.arrival).sort();
  if(!labels.includes(selectedRoute))selectedRoute='';
  setOptions(routeSelect,[['','Toutes les liaisons'],...labels.map(x=>[x,x])],selectedRoute);
}
function curve(e){
  // Décalage géographique léger, opposé selon le sens, pour dissocier A→B et B→A.
  const latD=e.b_lat-e.a_lat,lonD=e.b_lon-e.a_lon;
  const norm=Math.hypot(latD,lonD)||1;
  const offset=Math.min(norm*.10,.085);
  const mlat=(e.a_lat+e.b_lat)/2+(-lonD/norm)*offset;
  const mlon=(e.a_lon+e.b_lon)/2+(latD/norm)*offset;
  return {lat:[e.a_lat,mlat,e.b_lat],lon:[e.a_lon,mlon,e.b_lon],mlat,mlon};
}
function render(){
 const frame=MONTHS[selectedMonth];
 document.getElementById('stationCount').textContent=frame.nodes.length;
 document.getElementById('edgeCount').textContent=frame.edges.length;
 const nodeMap=new Map(frame.nodes.map(n=>[n.station,n]));
 if(selectedStation&&!nodeMap.has(selectedStation)){selectedStation='';stationSelect.value='';}
 updateRoutes();
 const maxVolume=Math.max(1,...frame.edges.map(e=>e.edge_volume));
 const maxRank=Math.max(.0001,...frame.nodes.map(n=>n.weighted_pagerank));
 const traces=[];
 const clickable=[];
 frame.edges.forEach(e=>{
   const key=e.departure+' → '+e.arrival;
   const matchesStation=!selectedStation||e.departure===selectedStation||e.arrival===selectedStation;
   const highlighted= selectedRoute ? key===selectedRoute : (selectedStation ? matchesStation : true);
   const xy=curve(e);
   const width=.6+4*Math.sqrt(e.edge_volume/maxVolume);
   traces.push({type:'scattermap',mode:'lines',lat:xy.lat,lon:xy.lon,
     line:{width:highlighted?width:.5,color: selectedRoute&&highlighted?'#f97316':highlighted?'rgba(26,118,170,.48)':'rgba(148,163,184,.12)'},
     hoverinfo:'skip',showlegend:false});
   // Point de survol pour identifier la liaison.
   if(matchesStation && (!selectedRoute||highlighted)){
     clickable.push({e,xy});
   }
 });
 // Points de liaison servant aux infobulles.
 traces.push({type:'scattermap',mode:'markers',
   lat:clickable.map(x=>x.xy.mlat),lon:clickable.map(x=>x.xy.mlon),
   marker:{size:10,color:'rgba(245,119,41,.55)'},
   customdata:clickable.map(x=>['edge',x.e.departure+' → '+x.e.arrival]),
   text:clickable.map(x=>x.e.departure+' → '+x.e.arrival),
   hovertemplate:'%{text}<extra></extra>',showlegend:false});
 const sizes=frame.nodes.map(n=>9+26*Math.sqrt(n.weighted_pagerank/maxRank));
 traces.push({type:'scattermap',mode:'markers',
   lat:frame.nodes.map(n=>n.lat),lon:frame.nodes.map(n=>n.lon),
   marker:{size:sizes,color:frame.nodes.map(n=>n.station===selectedStation?'#f97316':'#0d9488'),opacity:.92},
   customdata:frame.nodes.map(n=>['node',n.station]),text:frame.nodes.map(n=>n.station),
   hovertemplate:'<b>%{text}</b><extra></extra>',showlegend:false});
 // Étiquettes limitées aux gares les plus centrales.
 const labels=[...frame.nodes].sort((a,b)=>b.weighted_pagerank-a.weighted_pagerank).slice(0,8);
 traces.push({type:'scattermap',mode:'text',lat:labels.map(n=>n.lat),lon:labels.map(n=>n.lon),
   text:labels.map(n=>n.station),textfont:{size:11,color:'#18314d'},
   textposition:'top right',hoverinfo:'skip',showlegend:false});
 const layout={margin:{l:0,r:0,t:0,b:0},paper_bgcolor:'#fff',showlegend:false,
   map:{style:'carto-positron',center:mapCenter,zoom:4.4},uirevision:'railinsight-map'};
 const config={scrollZoom:true,responsive:true,displaylogo:false,
   modeBarButtonsToRemove:['lasso2d','select2d']};
 Plotly.react(mapEl,traces,layout,config).then(()=>{
   if(firstRender){
     firstRender=false;
     mapEl.on('plotly_click',ev=>{
       const d=ev.points?.[0]?.customdata;
       if(!d||!Array.isArray(d))return;
       if(d[0]==='node'){selectedStation=d[1];selectedRoute='';stationSelect.value=selectedStation;}
       if(d[0]==='edge'){selectedRoute=d[1];}
       render();
     });
   }
 });
 renderDetails();
}
monthSelect.addEventListener('change',()=>{selectedMonth=monthSelect.value;selectedRoute='';render();});
stationSelect.addEventListener('change',()=>{selectedStation=stationSelect.value;selectedRoute='';render();});
routeSelect.addEventListener('change',()=>{selectedRoute=routeSelect.value;render();});
document.getElementById('reset').addEventListener('click',()=>{
  selectedStation='';selectedRoute='';stationSelect.value='';render();
});
render();
</script>
</body></html>"""

if __name__ == "__main__":
    main()