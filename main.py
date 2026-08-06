import son_nadal_collector
import fetch_openmeteo
import mildiu_collector
import generate_dashboard

def main():
    print("=== ORQUESTRACIÓ INICIADA ===")
    
    print("\n--- 1. Recollint dades de l'estació (Son Nadal) ---")
    try:
        son_nadal_collector.main()
    except Exception as e:
        print(f"Error en son_nadal_collector: {e}")
        return
        
    print("\n--- 2. Obtenint dades d'Open-Meteo ---")
    try:
        fetch_openmeteo.main()
    except Exception as e:
        print(f"Error en fetch_openmeteo: {e}")
    
    print("\n--- 3. Calculant model Mildiu ---")
    try:
        mildiu_collector.main()
    except Exception as e:
        print(f"Error en mildiu_collector: {e}")
    
    print("\n--- 4. Generant Dashboard ---")
    try:
        generate_dashboard.main()
    except Exception as e:
        print(f"Error en generate_dashboard: {e}")
    
    print("\n=== ORQUESTRACIÓ COMPLETADA ===")

if __name__ == "__main__":
    main()
