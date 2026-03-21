# main.py
from hvac_engine import HVACAnalyticsEngine

def main():
    print("\n" + "=" * 50)
    print(" 🏢 Welcome to the Dynamic HVAC Analytics Engine 🏢 ")
    print("=" * 50)

    # Wrap the entire logic in a continuous loop
    while True:
        b_input = input("\nEnter Building ID [Default: 7] (or type 'q' to quit): ").strip()

        # Give the user an escape hatch!
        if b_input.lower() in ['q', 'quit', 'exit']:
            print("\nShutting down engine. Goodbye! 👋")
            break

        try:
            user_building = int(b_input) if b_input else 7
        except ValueError:
            print("❌ Invalid input! Please enter a numerical Building ID.")
            continue  # Skips the rest of the loop and asks them again immediately

        print(f"\n🚀 Booting engine for Building {user_building}...")

        # Instantiate the engine
        pipeline = HVACAnalyticsEngine(building_id=user_building)

        try:
            # Run the pipeline
            results = pipeline.run_full_pipeline()

            # Print the success summary
            print("\n" + "=" * 40)
            print(" 🎉 PIPELINE EXECUTION COMPLETE 🎉 ")
            print("=" * 40)

            # Safely calculate the efficiency penalty percentage
            expected = results['expected_annual_kwh']
            wasted = results['wasted_kwh']

            if expected > 0:
                penalty_pct = (wasted / expected) * 100
            else:
                penalty_pct = 100.0  # Failsafe

            print(f"Calculated Efficiency Penalty: {penalty_pct:.1f}%")
            print(f"Total Financial Loss (2026 Eq): ${results['wasted_dollars_2026_equivalent']:,.2f}")

            # Ask if they want to run another one after a success!
            retry = input("\nWould you like to analyze another building? (y/n): ").strip().lower()
            if retry != 'y':
                print("Shutting down engine. Goodbye! 👋")
                break

        except Exception as e:
            # THIS is where we catch the ValueError raised by hvac_engine.py
            print(f"\n❌ Pipeline failed: {e}")

            # Ask the user if they want to try a different ID
            retry = input("Would you like to try a different Building ID? (y/n): ").strip().lower()
            if retry != 'y':
                print("Shutting down engine. Goodbye! 👋")
                break


if __name__ == "__main__":
    main()