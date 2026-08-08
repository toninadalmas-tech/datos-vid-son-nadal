import son_nadal_collector
import fetch_openmeteo
import oidi_collector
import mildiu_collector
import botritis_collector
import blackrot_collector
import previsio
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
    
    print("\n--- 3. Calculant model Oïdi (Gubler + UV) ---")
    try:
        oidi_collector.main()
    except Exception as e:
        print(f"Error en oidi_collector: {e}")

    print("\n--- 4. Calculant model Mildiu ---")
    try:
        mildiu_collector.main()
    except Exception as e:
        print(f"Error en mildiu_collector: {e}")
        
    print("\n--- 5. Calculant model Botritis (Broome) ---")
    try:
        botritis_collector.main()
    except Exception as e:
        print(f"Error en botritis_collector: {e}")
        
    print("\n--- 6. Calculant model Black Rot (Spotts) ---")
    try:
        blackrot_collector.main()
    except Exception as e:
        print(f"Error en blackrot_collector: {e}")
    
    print("\n--- 7. Projectant el risc als pròxims dies ---")
    try:
        previsio.main()
    except Exception as e:
        print(f"Error en previsio: {e}")

    print("\n--- 8. Generant Dashboard ---")
    try:
        generate_dashboard.main()
    except Exception as e:
        print(f"Error en generate_dashboard: {e}")
    
    print("\n=== ORQUESTRACIÓ COMPLETADA ===")

if __name__ == "__main__":
    main()
