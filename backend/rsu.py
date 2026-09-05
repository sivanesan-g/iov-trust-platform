def verify_packet(features: dict):
    """
    RSU packet validation:
    - checks required fields
    - checks numeric values
    - basic physical sanity
    """

    required = [
        "posx", "posy", "posz",
        "spdx", "spdy", "spdz",
        "aclx", "acly", "aclz",
        "hedx", "hedy", "hedz"
    ]

    # 1. Check missing fields
    missing = [k for k in required if k not in features]
    if missing:
        return False, f"Missing fields: {missing}"

    # 2. Check numeric values
    try:
        for k in required:
            float(features[k])
    except Exception:
        return False, "Non-numeric feature value detected"

    # 3. Basic physical checks
    if abs(float(features["spdz"])) > 100:
        return False, "spdz out of physical range"

    if abs(float(features["aclz"])) > 100:
        return False, "aclz out of physical range"

    return True, "RSU verification passed"