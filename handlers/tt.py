def get_unified_lora_dictionary(self) -> dict[str, dict[str, dict[str, tuple[str | None, str | None]]]]:
    """Create a unified dictionary with all available information, tracking duplicates within unified_dict as a list."""
    unified_dict = self.initialize_dictionary_template()
    lora_dict = self.build_lora_dictionary()
    png_dict = self.build_png_dictionary()

    # Track occurrences of lora_names across categories and qualities
    lora_name_locations = {}

    # Combine all categories
    all_categories = sorted(set(lora_dict.keys()).union(png_dict.keys()), key=InfoHandler._category_sort_key)
    for category in all_categories:
        unified_dict.setdefault(category, {})
        lora_qualities = lora_dict.get(category, {})
        png_qualities = png_dict.get(category, {})

        # Combine all qualities
        all_qualities = set(lora_qualities.keys()).union(png_qualities.keys())
        for quality in sorted(all_qualities, key=InfoHandler._quality_sort_key):
            unified_dict[category].setdefault(quality, {})
            loras = lora_qualities.get(quality, {})
            pngs = png_qualities.get(quality, {})

            # Combine all lora names
            all_lora_names = set(loras.keys()).union(pngs.keys())
            for lora_name in sorted(all_lora_names):
                model_path = loras.get(lora_name)
                png_path = pngs.get(lora_name)

                # Initialize the entry if it doesn't exist
                if lora_name not in unified_dict[category][quality]:
                    unified_dict[category][quality][lora_name] = [model_path, png_path, []]
                else:
                    # Merge paths if necessary
                    entry = unified_dict[category][quality][lora_name]
                    entry[0] = entry[0] or model_path
                    entry[1] = entry[1] or png_path

                # Track occurrences
                location = (category, quality)
                if lora_name in lora_name_locations:
                    lora_name_locations[lora_name].append(location)
                else:
                    lora_name_locations[lora_name] = [location]

    # Add duplicates information into the unified_dict
    for lora_name, locations in lora_name_locations.items():
        if len(locations) > 1:
            # For each location, add the duplicates list excluding the current location
            for location in locations:
                category, quality = location
                duplicates = [loc for loc in locations if loc != location]
                unified_dict[category][quality][lora_name][2] = duplicates
        else:
            # Ensure duplicates list is empty for lora_names without duplicates
            category, quality = locations[0]
            unified_dict[category][quality][lora_name][2] = []

    # Clean up empty qualities
    for category in list(unified_dict.keys()):
        for quality in list(unified_dict[category].keys()):
            if not unified_dict[category][quality]:
                del unified_dict[category][quality]

    return unified_dict
