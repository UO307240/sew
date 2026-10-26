"""
Programa: xml2kml.py
Descripción: Procesa etapaEsquema.xml mediante XPath para generar
             la planimetría de la etapa en formato KML para Google Earth.
Asignatura: Software y Estándares para la Web

@author: Darío González Martínez
"""
import sys
import xml.etree.ElementTree as ET


class KmlGenerator:
    """Clase orientada a objetos para extraer datos por XPath y construir un KML."""

    def __init__(self, xml_file="etapaEsquema.xml", kml_file="etapa.kml"):
        self.xml_file = xml_file
        self.kml_file = kml_file
        self.ns = {"uniovi": "http://www.uniovi.es"}
        self.tree = None
        self.root = None

    def cargar_arbol_dom(self):
        """Carga el documento XML y obtiene el elemento raíz."""
        self.tree = ET.parse(self.xml_file)
        self.root = self.tree.getroot()

    def _extraer_coordenadas(self, nodo):
        """Método auxiliar para extraer lat, lon y alt de un nodo mediante XPath."""
        lat = nodo.find("./uniovi:coordenadas/uniovi:latitud", self.ns).text.strip()
        lon = nodo.find("./uniovi:coordenadas/uniovi:longitud", self.ns).text.strip()
        alt = nodo.find("./uniovi:coordenadas/uniovi:altitud", self.ns).text.strip()
        return lat, lon, alt

    def obtener_datos_etapa(self):
        """Extrae todos los puntos de la etapa."""
        puntos = []

        # Salida (XPath)
        salida = self.root.find("./uniovi:itinerario/uniovi:salida", self.ns)
        if salida is not None:
            nombre = salida.find("./uniovi:poblacion", self.ns).text.strip()
            lat, lon, alt = self._extraer_coordenadas(salida)
            puntos.append({
                "nombre": f"Salida: {nombre}",
                "lat": lat, "lon": lon, "alt": alt,
                "dist": 0.0
            })

        # Puntos de paso intermedios 
        puntos_paso = self.root.findall("./uniovi:itinerario/uniovi:puntos_paso/uniovi:punto_paso", self.ns)
        for p in puntos_paso:
            nombre = p.get("nombre", "Punto de paso")
            dist = float(p.find("./uniovi:distancia_salida", self.ns).text.strip())
            lat, lon, alt = self._extraer_coordenadas(p)
            puntos.append({
                "nombre": nombre,
                "lat": lat, "lon": lon, "alt": alt,
                "dist": dist
            })

        # Hitos: Puertos y Sprints 
        hitos = self.root.findall("./uniovi:itinerario/uniovi:hitos/uniovi:hito", self.ns)
        for h in hitos:
            tipo_hito = h.get("tipo")
            nombre = h.find("./uniovi:nombre_hito", self.ns).text.strip()
            dist = float(h.find("./uniovi:distancia_salida", self.ns).text.strip())
            lat, lon, alt = self._extraer_coordenadas(h)

            puntos.append({
                "nombre": nombre,
                "lat": lat, "lon": lon, "alt": alt,
                "dist": dist
            })

        # Meta
        meta = self.root.find("./uniovi:itinerario/uniovi:meta", self.ns)
        dist_total_elem = self.root.find("./uniovi:datos_basicos/uniovi:distancia", self.ns)
        dist_meta = float(dist_total_elem.text.strip()) if dist_total_elem is not None else 999.0
        if meta is not None:
            nombre = meta.find("./uniovi:poblacion", self.ns).text.strip()
            lat, lon, alt = self._extraer_coordenadas(meta)
            puntos.append({
                "nombre": f"Meta: {nombre}",
                "lat": lat, "lon": lon, "alt": alt,
                "dist": dist_meta
            })

        # Ordenar cronológicamente por distancia de carrera para el trazado
        puntos.sort(key=lambda x: x["dist"])
        return puntos

    def generar_kml(self):
        """Genera el contenido del archivo KML con estilos de colores y el recorrido."""
        self.cargar_arbol_dom()
        puntos = self.obtener_datos_etapa()

        kml = []
        kml.append('<?xml version="1.0" encoding="UTF-8"?>')
        kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
        kml.append('  <Document>')
        kml.append('    <name>Etapa 11: Cartagena a Lorca</name>')
        kml.append('    <description>Planimetría y recorrido de la etapa</description>')

        # CREACIÓN DE LOS MARCADORES
        for p in puntos:
            kml.append('    <Placemark>')
            kml.append(f'      <name>{p["nombre"]}</name>')
            kml.append(f'      <description>Km: {p["dist"]} | Altitud: {p["alt"]} m</description>')
            kml.append('      <Point>')
            # KML exige obligatoriamente: longitud,latitud,altitud
            kml.append(f'        <coordinates>{p["lon"]},{p["lat"]},{p["alt"]}</coordinates>')
            kml.append('      </Point>')
            kml.append('    </Placemark>')

        # TRAZADO DE LA RUTA COMPLETA
        kml.append('    <Placemark>')
        kml.append('      <name>Recorrido Etapa 11</name>')
        kml.append('    <Style>')
        kml.append('      <LineStyle>')
        kml.append('        <color>ff0000ff</color>')  # Rojo intenso
        kml.append('        <width>5</width>')
        kml.append('      </LineStyle>')
        kml.append('    </Style>')
        kml.append('      <LineString>')
        kml.append('        <extrude>1</extrude>')
        kml.append('        <tessellate>1</tessellate>')
        kml.append('        <altitudeMode>clampToGround</altitudeMode>')
        kml.append('        <coordinates>')
        coords_str = " ".join([f'{p["lon"]},{p["lat"]},{p["alt"]}' for p in puntos])
        kml.append(f'          {coords_str}')
        kml.append('        </coordinates>')
        kml.append('      </LineString>')
        kml.append('    </Placemark>')

        kml.append('  </Document>')
        kml.append('</kml>')

        # Guardar en archivo
        with open(self.kml_file, "w", encoding="utf-8") as f:
            f.write("\n".join(kml))
        print(f"Archivo KML generado con éxito: {self.kml_file}")

##'#ff0000ff',"5"

if __name__ == "__main__":

    print(__doc__)

    generador = KmlGenerator()
    generador.generar_kml()
