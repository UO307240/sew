#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Programa: xml2altimetria.py
Descripción: Extrae datos altimétricos mediante XPath desde etapaEsquema.xml
             y genera un archivo vectorial SVG con el perfil de la etapa.
Asignatura: Software y Estándares para la Web
Author: Darío González Martínez
"""

import xml.etree.ElementTree as ET


class SvgAltimetriaGenerator:
    """Clase orientada a objetos para extraer altimetría vía XPath y generar SVG."""

    def __init__(self, xml_file="etapaEsquema.xml", svg_file="altimetria.svg"):
        self.xml_file = xml_file
        self.svg_file = svg_file
        self.ns = {"uniovi": "http://www.uniovi.es"}
        
        # Dimensiones del lienzo SVG
        self.ancho = 1100
        self.alto = 600
        self.margen_izq = 80
        self.margen_dcha = 60
        self.margen_sup = 60
        self.margen_inf = 160  # Espacio para los textos verticales inferiores
        
        # Área útil de trazado gráfico
        self.ancho_grafica = self.ancho - self.margen_izq - self.margen_dcha
        self.alto_grafica = self.alto - self.margen_sup - self.margen_inf
        self.y_suelo = self.margen_sup + self.alto_grafica

        self.puntos = []

    def cargar_datos_xpath(self):
        """Extrae distancias y altitudes del XML usando expresiones XPath."""
        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        # 1. Salida (km 0.0)
        salida = root.find("./uniovi:itinerario/uniovi:salida", self.ns)
        nom_salida = salida.find("./uniovi:poblacion", self.ns).text.strip()
        alt_salida = float(salida.find("./uniovi:coordenadas/uniovi:altitud", self.ns).text.strip())
        self.puntos.append({"nombre": nom_salida, "dist": 0.0, "alt": alt_salida})

        # 2. Puntos de paso intermedios
        puntos_paso = root.findall("./uniovi:itinerario/uniovi:puntos_paso/uniovi:punto_paso", self.ns)
        for p in puntos_paso:
            nom = p.get("nombre", "Punto intermedio")
            dist = float(p.find("./uniovi:distancia_salida", self.ns).text.strip())
            alt = float(p.find("./uniovi:coordenadas/uniovi:altitud", self.ns).text.strip())
            self.puntos.append({"nombre": nom, "dist": dist, "alt": alt})

        # 3. Hitos (Puertos y Sprints)
        hitos = root.findall("./uniovi:itinerario/uniovi:hitos/uniovi:hito", self.ns)
        for h in hitos:
            nom = h.find("./uniovi:nombre_hito", self.ns).text.strip()
            dist = float(h.find("./uniovi:distancia_salida", self.ns).text.strip())
            alt = float(h.find("./uniovi:coordenadas/uniovi:altitud", self.ns).text.strip())
            self.puntos.append({"nombre": nom, "dist": dist, "alt": alt})

        # 4. Meta
        meta = root.find("./uniovi:itinerario/uniovi:meta", self.ns)
        nom_meta = meta.find("./uniovi:poblacion", self.ns).text.strip()
        alt_meta = float(meta.find("./uniovi:coordenadas/uniovi:altitud", self.ns).text.strip())
        dist_meta = float(root.find("./uniovi:datos_basicos/uniovi:distancia", self.ns).text.strip())
        self.puntos.append({"nombre": nom_meta, "dist": dist_meta, "alt": alt_meta})

        # Ordenar cronológicamente por distancia de etapa
        self.puntos.sort(key=lambda x: x["dist"])

    def _mapear_x(self, dist, dist_max):
        """Convierte kilómetros a coordenada X del canvas SVG."""
        return self.margen_izq + (dist / dist_max) * self.ancho_grafica

    def _mapear_y(self, alt, alt_max):
        """Convierte metros de altitud a coordenada Y del canvas SVG (eje invertido)."""
        return self.y_suelo - (alt / alt_max) * self.alto_grafica

    def generar_svg(self):
        """Construye las etiquetas SVG vectoriales y guarda el archivo."""
        self.cargar_datos_xpath()

        dist_max = max(p["dist"] for p in self.puntos)
        # Redondear la altitud máxima hacia arriba a centenas para la escala
        alt_max = (int(max(p["alt"] for p in self.puntos) // 100) + 1) * 100

        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
                   f'width="{self.ancho}" height="{self.alto}" viewBox="0 0 {self.ancho} {self.alto}">')
        
        # Fondo blanco
        svg.append(f'  <rect width="100%" height="100%" fill="#ffffff" />')

        # Título
        svg.append(f'  <text x="{self.ancho / 2}" y="35" text-anchor="middle" '
                   f'font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#333333">'
                   f'Perfil Altimétrico - Etapa 11: Cartagena a Lorca</text>')

        # Líneas de referencia horizontales (escala de altitud)
        paso_alt = 100  # marcas cada 100 m
        for alt_guia in range(0, int(alt_max) + 1, paso_alt):
            y_guia = self._mapear_y(alt_guia, alt_max)
            svg.append(f'  <line x1="{self.margen_izq}" y1="{y_guia}" '
                       f'x2="{self.margen_izq + self.ancho_grafica}" y2="{y_guia}" '
                       f'stroke="#e0e0e0" stroke-width="1" stroke-dasharray="4,4" />')
            svg.append(f'  <text x="{self.margen_izq - 10}" y="{y_guia + 4}" text-anchor="end" '
                       f'font-family="Arial, sans-serif" font-size="11" fill="#777777">{alt_guia} m</text>')

        # Coordenadas de los vértices para la polilínea del relieve
        puntos_grafica = []
        for p in self.puntos:
            x = self._mapear_x(p["dist"], dist_max)
            y = self._mapear_y(p["alt"], alt_max)
            puntos_grafica.append((x, y))

        # Polígono de relleno (efecto suelo montañoso)
        pts_poligono = [f"{self.margen_izq},{self.y_suelo}"]
        pts_poligono.extend([f"{x:.1f},{y:.1f}" for x, y in puntos_grafica])
        pts_poligono.append(f"{self.margen_izq + self.ancho_grafica},{self.y_suelo}")
        svg.append(f'  <polygon points="{" ".join(pts_poligono)}" fill="#fcd9d9" />')

        # Línea de contorno del relieve (rojo de carrera)
        pts_linea = " ".join([f"{x:.1f},{y:.1f}" for x, y in puntos_grafica])
        svg.append(f'  <polyline points="{pts_linea}" fill="none" stroke="#d32f2f" stroke-width="3" />')

        # Eje base del suelo
        svg.append(f'  <line x1="{self.margen_izq}" y1="{self.y_suelo}" '
                   f'x2="{self.margen_izq + self.ancho_grafica}" y2="{self.y_suelo}" '
                   f'stroke="#333333" stroke-width="2" />')

        # Marcas verticales, puntos y rótulos
        for i, p in enumerate(self.puntos):
            x, y = puntos_grafica[i]

            # Punto circular sobre la cima/perfil
            svg.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#d32f2f" stroke="#ffffff" stroke-width="1" />')

            # Línea guía vertical discontinua hacia el suelo
            svg.append(f'  <line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{self.y_suelo}" '
                       f'stroke="#aaaaaa" stroke-width="1" stroke-dasharray="2,2" />')

            # Texto vertical rotado 90 grados hacia abajo
            rot_x = x
            rot_y = self.y_suelo + 15
            etiqueta = f'{p["nombre"]} ({p["alt"]:.0f} m, {p["dist"]:.1f} km)'
            svg.append(f'  <text x="{rot_x:.1f}" y="{rot_y:.1f}" text-anchor="start" '
                       f'font-family="Arial, sans-serif" font-size="11" fill="#222222" '
                       f'transform="rotate(90, {rot_x:.1f}, {rot_y:.1f})">{etiqueta}</text>')

        svg.append('</svg>')

        with open(self.svg_file, "w", encoding="utf-8") as f:
            f.write("\n".join(svg))
        print(f"Archivo SVG generado con éxito: {self.svg_file}")


if __name__ == "__main__":
    generador = SvgAltimetriaGenerator()
    generador.generar_svg()
