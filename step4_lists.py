import pandas as pd
import os
from config import FILTERED_FOLDER, LISTS_FOLDER


def main():
    """
    Step 4 – Build Date‑Ordered Lists.
    For each surviving file in step3_filtered (per threshold),
    create two lists:
      1. Ascending by date (earliest first)
      2. Descending by date (latest first)
    Save them to step4_lists.
    """
    # Ensure filtered folder exists
    if not os.path.exists(FILTERED_FOLDER):
        print(f"ERROR: {FILTERED_FOLDER} not found. Run step3_filtered.py first.")
        return

    # Ensure lists folder exists
    os.makedirs(LISTS_FOLDER, exist_ok=True)

    # Process each threshold subfolder
    for threshold_dir in os.listdir(FILTERED_FOLDER):
        subfolder = os.path.join(FILTERED_FOLDER, threshold_dir)
        if not os.path.isdir(subfolder):
            continue

        # Create corresponding subfolder in lists folder
        list_subfolder = os.path.join(LISTS_FOLDER, threshold_dir)
        os.makedirs(list_subfolder, exist_ok=True)

        # Process each CSV file in the threshold subfolder
        for filename in os.listdir(subfolder):
            if not filename.endswith(".csv"):
                continue

            filepath = os.path.join(subfolder, filename)
            df = pd.read_csv(filepath)

            # Sort ascending by date (assuming 'date' column exists)
            df_asc = df.sort_values("date")
            asc_filename = f"{filename}_asc.csv"
            asc_path = os.path.join(list_subfolder, asc_filename)
            df_asc.to_csv(asc_path, index=False)

            # Sort descending by date
            df_desc = df.sort_values("date", ascending=False)
            desc_filename = f"{filename}_desc.csv"
            desc_path = os.path.join(list_subfolder, desc_filename)
            df_desc.to_csv(desc_path, index=False)

        print(f"Threshold {threshold_dir}: processed {len(os.listdir(subfolder))} files")

    print(f"Step 4 complete. Lists saved to {LISTS_FOLDER}")


if __name__ == "__main__":
    main()