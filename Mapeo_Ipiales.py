import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.ticker as mticker
import numpy as np
from shapely.geometry import Point

# 1. Cargar y filtrar datos
nariño = gpd.read_file("data/Narino/Municipios_Nariño.shp")
ipiales = nariño[nariño["MPIO_CNMBR"] == "IPIALES"].to_crs(epsg=3116)
frontera = gpd.read_file("data/Frontera_Agricola/Frontera_Agr_Cond_NCon_Abr2024.shp").to_crs(ipiales.crs)
frontera_ipiales = frontera[frontera["municipio"] == "Ipiales"]

# Filtrar solo la zona condicionada
condicionada = frontera_ipiales[frontera_ipiales["tipo_front"] == "Condicionada"]

# 2. Generar puntos de cultivos con mejor distribución
np.random.seed(42)  # Para reproducibilidad
cultivos = ['Papa', 'Arveja', 'Maíz', 'Cebolla']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
markers = ['o', 's', '^', 'v']  # Círculo, cuadrado, triángulo, triángulo invertido

# Probabilidades de cultivo (60% papa, 30% arveja, 7% maíz, 3% cebolla)
probabilidades = [0.6, 0.3, 0.07, 0.03]

# Crear un GeoDataFrame para los puntos de cultivo
points = []
cultivos_list = []

# Seleccionar aleatoriamente el 70% de los polígonos condicionados para mostrar cultivos
poligonos_con_cultivos = condicionada.sample(frac=0.7, random_state=42)

for idx, polygon in enumerate(poligonos_con_cultivos.geometry):
    # Generar entre 8-20 puntos por polígono seleccionado
    num_puntos = np.random.randint(8, 20)
    minx, miny, maxx, maxy = polygon.bounds
    
    for _ in range(num_puntos):
        # Seleccionar cultivo según probabilidades
        cultivo = np.random.choice(cultivos, p=probabilidades)
        
        # Crear punto aleatorio dentro del polígono
        for _ in range(100):  # Intentos máximos
            point = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(point):
                # Asegurar cierta separación mínima entre puntos
                if len(points) == 0 or all(point.distance(Point(p.coords[0])) > 200 for p in points[-10:]):  # 200m
                    points.append(point)
                    cultivos_list.append(cultivo)
                    break

cultivos_gdf = gpd.GeoDataFrame({'cultivo': cultivos_list, 'geometry': points}, crs=ipiales.crs)

# 3. Configuración de estilo científico
plt.style.use('default')
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'axes.linewidth': 0.8,
    'grid.alpha': 0.3
})

# 4. Crear figura
fig, ax = plt.subplots(figsize=(15, 10), dpi=300)

# 5. Establecer límites del mapa (recorte)
xmin, xmax = 580000, 620000  # Longitud Este-Oeste
ymin, ymax = 560000, 600000  # Latitud Norte-Sur
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

# 6. Dibujar mapas (solo lo que está dentro de los límites)
ipiales.clip((xmin, ymin, xmax, ymax)).plot(ax=ax, color='none', edgecolor='black', linewidth=0.8, label='Municipio Ipiales')
condicionada.clip((xmin, ymin, xmax, ymax)).plot(ax=ax, color='#4daf4a', edgecolor='white', linewidth=0.3, alpha=0.3, label='Zona Condicionada')

# Filtrar puntos dentro del área recortada
cultivos_gdf = cultivos_gdf.cx[xmin:xmax, ymin:ymax]

# Dibujar puntos de cultivos con tamaño proporcional a su importancia
sizes = {'Papa': 80, 'Arveja': 60, 'Maíz': 40, 'Cebolla': 40}
for cultivo, color, marker in zip(cultivos, colors, markers):
    subset = cultivos_gdf[cultivos_gdf['cultivo'] == cultivo]
    if not subset.empty:
        subset.plot(ax=ax, color=color, marker=marker, markersize=sizes[cultivo], 
                   edgecolor='white', linewidth=0.3, label=cultivo)

# 7. Configuración de ejes profesionales
ax.set_xlabel("Longitud (Este-Oeste)", labelpad=10)
ax.set_ylabel("Latitud (Norte-Sur)", labelpad=10)
ax.set_title("", pad=20)

# Configurar ticks con formato más limpio
ax.xaxis.set_major_locator(mticker.MultipleLocator(10000))  # Cada 10,000 m
ax.yaxis.set_major_locator(mticker.MultipleLocator(10000))
ax.grid(True, linestyle=':', linewidth=0.5)
ax.tick_params(axis='both', which='both', length=5, width=0.8)

# Formatear ticks para mostrar solo los últimos 5 dígitos (más legible)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x%100000):,}'.replace(',', "'")))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f'{int(y%100000):,}'.replace(',', "'")))

# 8. Leyenda profesional mejorada
legend_elements = [
    Patch(facecolor='none', edgecolor='black', label='Límite Municipal'),
    Patch(facecolor='#4daf4a', edgecolor='white', alpha=0.3, label='Zona Condicionada'),
    *[plt.Line2D([0], [0], marker=marker, color='w', markerfacecolor=color, 
      markersize=10, label=f'{cultivo} ({prob*100:.0f}%)') 
      for cultivo, color, marker, prob in zip(cultivos, colors, markers, probabilidades)]
]

legend = ax.legend(
    handles=legend_elements,
    title="Distribución de Cultivos",
    loc='upper left',
    bbox_to_anchor=(0.01, 0.99),
    frameon=True,
    framealpha=1,
    edgecolor='black',
    title_fontsize='12',
    fontsize=11,
    borderpad=1
)

# 9. Añadir elementos de mapa
# Escala (reducida para el área recortada)
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
scalebar = AnchoredSizeBar(ax.transData,
                          size=2000,  # 2 km (ajustado al área recortada)
                          label='2 km',
                          loc='lower right',
                          pad=0.5,
                          color='black',
                          frameon=False,
                          size_vertical=50)
ax.add_artist(scalebar)

# Norte
x, y, arrow_length = 0.95, 0.1, 0.1
ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
            arrowprops=dict(facecolor='black', width=2, headwidth=8),
            ha='center', va='center', fontsize=12,
            xycoords=ax.transAxes)



# 11. Ajustar y guardar
plt.tight_layout()
plt.savefig("data/Ipiales/mapa_cultivos_zona_norte_recortado.png", 
           dpi=600, 
           bbox_inches='tight', 
           facecolor='white',
           format='png')
plt.show()