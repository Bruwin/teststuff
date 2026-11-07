"""Industrial palette for the voxel factory asset set.

Colours are hand-picked for a bright, readable voxel look: mid-dark steel and
concrete bodies so that safety colours and indicator lights pop.  Every colour
is authored as sRGB hex; the exporter writes linear-free sRGB floats with the
glTF `baseColorFactor` left at white so engines that ignore vertex colours
still get a valid, uniformly lit material.
"""

PALETTE = {
    # --- structural steel ------------------------------------------------
    "steel_dark":   "#3A4250",
    "steel":        "#6C7885",
    "steel_light":  "#96A2AE",
    "galv":         "#B7C1CB",
    "white_panel":  "#DCE2E8",
    "iron":         "#59616D",
    "rust":         "#8C4C33",
    "rust_dark":    "#6B3927",
    "concrete":     "#9C988F",
    "concrete_dark": "#7E7A72",
    # --- safety / signal -------------------------------------------------
    "yellow":       "#E7B437",
    "yellow_dark":  "#C28F1D",
    "orange":       "#DF7A2C",
    "orange_dark":  "#B85E1B",
    "red":          "#BE3A2C",
    "red_dark":     "#93261B",
    "teal":         "#2C8B8B",
    "teal_dark":    "#1E6666",
    "blue":         "#2F6FA8",    "blue_dark":   "#235180",
    "navy":         "#223E58",
    "green":        "#4D9A5B",
    "green_dark":   "#38733F",
    # --- fluids / materials ----------------------------------------------
    "water":        "#3E7FA6",
    "water_light":  "#5FA0C4",
    "gas":          "#C9D6DE",
    "oil":          "#4A4136",
    "coolant":      "#6FBF73",
    "copper":       "#C0783C",
    "brass":        "#BE9A46",
    "rubber":       "#23262B",
    "rubber_dark":  "#15171A",
    "belt":         "#3A3F47",
    "belt_dark":    "#272B31",
    # --- reference-style machinery colours -------------------------------
    "orange_frame": "#E8722B",
    "orange_frame_dark": "#B8551B",
    "hazard_yellow": "#F5C518",
    "hazard_black": "#232323",
    "roller":       "#B9C0C7",
    "roller_dark":  "#8A929B",
    "frame_dark":   "#3B3F46",
    "grille":       "#6E7781",
    "hydraulic":    "#C9A227",
    "glass":        "#8EC5D6",
    "glass_dark":   "#5F9DB1",
    "lamp_green":   "#7FE08A",
    "lamp_amber":   "#F3C24C",
    "lamp_red":     "#E4574A",
    "lamp_blue":    "#6FB3E8",
    "screen":       "#2A6F7A",
    "screen_glow":  "#57C7C4",
    # --- organic / misc ---------------------------------------------------
    "wood":         "#9A6B43",
    "wood_dark":    "#70502F",
    "cardboard":    "#B98A56",
    "cardboard_dark": "#96693C",
    "sand":         "#C8A96E",
    "grain":        "#D9B871",
}

# Handy groupings used by several models.
STEEL_TRIO = ("steel_dark", "steel", "steel_light")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
