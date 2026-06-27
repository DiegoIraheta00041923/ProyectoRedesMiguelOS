import json

JSON_FILE = "planos.json"

# Constantes de cálculo bajo norma TIA-568/569
Y_PASILLO = 6.0
CAIDA_VERTICAL_M = 5.0  # 2.5m bajada al rack + 2.5m bajada al nodo
MARGEN_HOLGURA = 1.10   # 10% extra de holgura por norma horizontal

def calcular_cableado_completo():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encuentra {JSON_FILE}")
        return

    total_horizontal_neto = 0
    total_horizontal_real = 0

    print("REPORTE DE CABLEADO UTP HORIZONTAL (TIA-568/569)")

    for nivel in datos["edificio"]["niveles"]:
        num_nivel = nivel["nivel"]
        habitaciones = []
        cuarto_idf_mdf = None

        # Mapear zonas norte
        x_actual = 0
        for zona in nivel["zonas_norte"]:
            cx = x_actual + (zona["largo_m"] / 2)
            cy = 7 + (zona["ancho_m"] / 2)
            nodos = zona.get("nodos", 0)
            nombre = zona["nombre"]
            
            hab = {"nombre": nombre, "cx": cx, "cy": cy, "nodos": nodos}
            habitaciones.append(hab)
            
            if nombre in ["RED", "SERVIDORES"] and cuarto_idf_mdf is None:
                cuarto_idf_mdf = hab
            x_actual += zona["largo_m"]

        # Mapear zonas sur
        x_actual = 0
        for zona in nivel["zonas_sur"]:
            cx = x_actual + (zona["largo_m"] / 2)
            cy = 0 + (zona["ancho_m"] / 2)
            nodos = zona.get("nodos", 0)
            nombre = zona["nombre"]
            
            hab = {"nombre": nombre, "cx": cx, "cy": cy, "nodos": nodos}
            habitaciones.append(hab)
            
            if nombre in ["RED", "SERVIDORES"] and cuarto_idf_mdf is None:
                cuarto_idf_mdf = hab
            x_actual += zona["largo_m"]

        # Mapear e incluir la Zona Central (Pasillo)
        zona_central = nivel.get("zona_central")
        if zona_central:
            cx = 24.0 / 2 # Centro exacto en X (12.0)
            cy = 6.0      # Eje del pasillo en Y (6.0)
            nodos = zona_central.get("nodos", 0)
            hab = {"nombre": zona_central["nombre"], "cx": cx, "cy": cy, "nodos": nodos}
            habitaciones.append(hab)

        tipo_cuarto = "MDF" if num_nivel == 3 else "IDF"

        print(f"\n--- NIVEL {num_nivel} ---")
        if not cuarto_idf_mdf:
            print("No se definió cuarto de RED/SERVIDORES en este piso.")
            continue

        print(f"Origen ({tipo_cuarto}): {cuarto_idf_mdf['nombre']} -> Coordenadas ({cuarto_idf_mdf['cx']}, {cuarto_idf_mdf['cy']})")
        
        total_nivel_neto = 0
        
        for hab in habitaciones:
            if hab["nodos"] > 0 and hab["nombre"] != cuarto_idf_mdf["nombre"]:
                
                dist_y_origen = abs(cuarto_idf_mdf["cy"] - Y_PASILLO)
                dist_x_pasillo = abs(cuarto_idf_mdf["cx"] - hab["cx"])
                dist_y_destino = abs(hab["cy"] - Y_PASILLO)
                
                dist_plana = dist_y_origen + dist_x_pasillo + dist_y_destino
                dist_por_nodo = dist_plana + CAIDA_VERTICAL_M
                cable_sala = dist_por_nodo * hab["nodos"]
                total_nivel_neto += cable_sala
                
                print(f" > {hab['nombre']:<18} | {hab['nodos']} nodos | Ruta plana: {dist_plana}m | Total c/caídas: {dist_por_nodo}m c/u | Total Sala: {cable_sala}m")
                
        total_nivel_real = total_nivel_neto * MARGEN_HOLGURA
        print(f"Total Neto Nivel {num_nivel}: {total_nivel_neto} m")
        print(f"Total Real Nivel {num_nivel} (+10% holgura): {round(total_nivel_real, 2)} m")
        
        total_horizontal_neto += total_nivel_neto 
        total_horizontal_real += total_nivel_real

    print("RESUMEN DE MATERIALES TOTALEs")

    print(f"\nTOTAL CABLEADO HORIZONTAL (NETO): {total_horizontal_neto} m")
    print(f"TOTAL CABLEADO HORIZONTAL (REAL +10%): {round(total_horizontal_real, 2)} m")
    
    backbone_cascada = 19.0
    backbone_hibrido = 32.0
    
    print("\nPROYECCIÓN DE TRONCALES (BACKBONE VERTICAL):")
    print(f" - Opción A (Cascada): {backbone_cascada} m -> Gran Total Proyecto: {round(total_horizontal_real + backbone_cascada, 2)} m")
    print(f" - Opción B (Híbrido): {backbone_hibrido} m -> Gran Total Proyecto: {round(total_horizontal_real + backbone_hibrido, 2)} m")
    
    grand_total_bobinas = (total_horizontal_real + backbone_hibrido) / 305
    print(f"\nBobinas de 305m recomendadas para el proyecto completo (Opción B): {round(grand_total_bobinas, 1)} bobinas")

if __name__ == "__main__":
    calcular_cableado_completo()
